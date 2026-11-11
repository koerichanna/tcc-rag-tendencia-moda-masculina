"""Compara as respostas geradas por cinco configurações do consultor nas mesmas perguntas.

Uso: python -m avaliacao.avaliar_respostas [quantidade_por_risco]
Saída: avaliacao/resultados/respostas.json (requer GOOGLE_API_KEY; faz cerca de 3 chamadas por pergunta)

Configurações:
- regras:           só as regras locais, sem LLM
- llm_sem_contexto: o LLM responde sem documento recuperado e sem o risco calculado
- rag_sem_risco:    RAG com o prompt antigo (contexto recuperado, sem o risco calculado)
- rag:              RAG com o prompt atual (informa o risco calculado e as regras de coerência)
- rag_validado:     o anterior + correção automática de coerencia.py (o que a API devolve)

Métricas (todas automáticas, sem juiz humano nem LLM avaliador):
- risco_correto:   nivel_risco declarado = risco calculado da tendência esperada
- acao_coerente:   ação compatível com esse risco (regra de coerencia.py)
- sem_invencao:    % de respostas em que todo número citado (percentuais e notas x/100) aparece nos
                   dados da tendência; um número fora deles foi inventado pelo modelo
"""
import json
import pathlib
import re
import sys
import time

import coerencia
import rag_engine
import vector_db
from ingestion import carregar_dados_mercado

PASTA = pathlib.Path(__file__).resolve().parent
PAUSA_ENTRE_CHAMADAS = 4.5  # segundos; o plano gratuito do Gemini limita as requisições por minuto

PROMPT_SEM_CONTEXTO = """Você é um consultor especialista em tendências e gestão de compras para o varejo de moda masculina.
Responda ESTRITAMENTE em formato JSON (sem blocos markdown) com as chaves "diagnostico", "acao_recomendada",
"nivel_risco" (exatamente 'Baixo', 'Moderado' ou 'Alto'), "justificativa_explicavel" e "fontes_consultadas".

Pergunta do Lojista:
{pergunta}
"""

NUMERO = re.compile(r"[-+]?\d+(?:[.,]\d+)?")


def numeros_citados(resposta):
    """Percentuais e notas 'x/100' no texto da resposta (anos e quantidades soltas ficam de fora)."""
    texto = f"{resposta.get('diagnostico', '')} {resposta.get('justificativa_explicavel', '')}"
    candidatos = re.findall(r"[-+]?\d+(?:[.,]\d+)?\s*%|\d+(?:[.,]\d+)?\s*/\s*100", texto)
    return [abs(float(NUMERO.search(c).group().replace(",", "."))) for c in candidatos]


def numeros_dos_dados(tendencia):
    """Todos os números que o documento da tendência mostra ao LLM (ver ingestion.montar_documento)."""
    m = tendencia.get("metricas", {})
    valores = [tendencia["score_relevancia"], m.get("interesse_recente"), m.get("variacao_12m_pct"),
               m.get("semanas_zeradas_pct")]
    return {round(abs(v), 1) for v in valores if v is not None}


def sem_invencao(resposta, permitidos):
    return all(round(n, 1) in permitidos or round(n) in {round(p) for p in permitidos}
               for n in numeros_citados(resposta))


def escolher_perguntas(perguntas, base, por_risco):
    """Mesma quantidade de perguntas para cada nível de risco, para a comparação não pender para um lado."""
    escolhidas = {"Baixo": [], "Moderado": [], "Alto": []}
    for caso in perguntas:
        risco = base[caso["relevantes"][0]]["nivel_risco"]
        if len(escolhidas[risco]) < por_risco:
            escolhidas[risco].append(caso)
    return [c for lista in escolhidas.values() for c in lista]


def chamar_llm(funcao):
    time.sleep(PAUSA_ENTRE_CHAMADAS)
    try:
        return funcao()
    except Exception as erro:  # uma falha isolada vira resposta vazia em vez de derrubar a avaliação
        print(f"    falha: {erro}")
        return None


def llm_sem_contexto(pergunta):
    llm = rag_engine._obter_llm()
    texto = rag_engine._invocar_llm(llm, PROMPT_SEM_CONTEXTO.format(pergunta=pergunta), "avaliacao")
    return rag_engine._extrair_json_resposta(texto)


def main(por_risco=8):
    if rag_engine._obter_llm() is None:
        sys.exit("Configure GOOGLE_API_KEY para avaliar as respostas do LLM.")
    base = {t["id"]: t for t in carregar_dados_mercado()}
    perguntas = escolher_perguntas(json.loads((PASTA / "perguntas.json").read_text(encoding="utf-8")), base, por_risco)
    print(f"{len(perguntas)} perguntas ({por_risco} por nível de risco)\n")

    linhas = []
    for i, caso in enumerate(perguntas, start=1):
        esperada = base[caso["relevantes"][0]]
        risco = esperada["nivel_risco"]
        docs = vector_db.buscar_tendencias_similares(caso["pergunta"], n_results=3)
        print(f"[{i}/{len(perguntas)}] ({risco}) {caso['pergunta']}")

        regras = rag_engine.sintetizar_resposta_contextual(caso["pergunta"], docs)
        respostas = {
            "regras": regras,
            "llm_sem_contexto": chamar_llm(lambda: llm_sem_contexto(caso["pergunta"])),
            "rag_sem_risco": chamar_llm(lambda: rag_engine.executar_rag_llm(caso["pergunta"], docs, informar_risco=False)),
            "rag": chamar_llm(lambda: rag_engine.executar_rag_llm(caso["pergunta"], docs)),
        }
        if respostas["rag"]:
            validada = dict(respostas["rag"])
            # mesma referência que a API usa: a primeira tendência recuperada
            coerencia.alinhar(validada, regras["nivel_risco"], regras["acao_recomendada"])
            respostas["rag_validado"] = validada
        else:
            respostas["rag_validado"] = None

        # Números permitidos: os da tendência esperada e os dos documentos que o RAG recuperou.
        permitidos = numeros_dos_dados(esperada)
        for d in docs:
            permitidos |= numeros_dos_dados(base.get(d["id"], {"score_relevancia": d["metadados"]["score_relevancia"]}))

        for nome, r in respostas.items():
            linhas.append({
                "pergunta": caso["pergunta"], "risco_esperado": risco, "configuracao": nome,
                "respondeu": r is not None,
                "risco_correto": bool(r) and r.get("nivel_risco") == risco,
                "acao_coerente": bool(r) and coerencia.acao_compativel(r.get("acao_recomendada", ""), risco),
                "sem_invencao": bool(r) and sem_invencao(r, permitidos),
                "numeros_citados": numeros_citados(r) if r else [],
                "numeros_permitidos": sorted(permitidos),
                "acao": (r or {}).get("acao_recomendada"),
                "texto": f"{(r or {}).get('diagnostico', '')} {(r or {}).get('justificativa_explicavel', '')}".strip(),
                "nivel_risco": (r or {}).get("nivel_risco"),
            })

    resumo = {}
    for nome in ["regras", "llm_sem_contexto", "rag_sem_risco", "rag", "rag_validado"]:
        da_config = [r for r in linhas if r["configuracao"] == nome]
        respondidas = [r for r in da_config if r["respondeu"]]
        pct = lambda campo: round(100 * sum(r[campo] for r in respondidas) / len(respondidas), 1) if respondidas else None  # noqa: E731
        resumo[nome] = {
            "respondidas": len(respondidas), "total": len(da_config),
            "risco_correto": pct("risco_correto"), "acao_coerente": pct("acao_coerente"),
            "sem_invencao": pct("sem_invencao"),
        }
        print(f"{nome:<17} risco correto {resumo[nome]['risco_correto']}%  ação coerente {resumo[nome]['acao_coerente']}%  "
              f"sem números inventados {resumo[nome]['sem_invencao']}%  ({len(respondidas)}/{len(da_config)})")

    saida = PASTA / "resultados" / "respostas.json"
    saida.parent.mkdir(exist_ok=True)
    saida.write_text(json.dumps({"perguntas": len(perguntas), "resumo": resumo, "detalhes": linhas},
                                ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\nResultados em {saida.relative_to(PASTA.parent)}")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 8)
