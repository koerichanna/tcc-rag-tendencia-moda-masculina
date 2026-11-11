"""Compara a recuperação de documentos entre modelos de embedding e uma busca por palavras-chave.

Uso: python -m avaliacao.avaliar_recuperacao
Saída: avaliacao/resultados/recuperacao.json (o relatório em docs/avaliacao_rag.md usa esses números)

Para cada pergunta de avaliacao/perguntas.json, verifica em que posição aparece o primeiro
documento relevante entre os 3 recuperados. Métricas:
- hit@1 e hit@3: % de perguntas com um documento relevante na 1ª posição / entre os 3 primeiros
- MRR@3: média de 1/posição do primeiro relevante (0 se não aparece entre os 3)
- latência: mediana do tempo de uma consulta, em ms
"""
import json
import pathlib
import statistics
import time

import chromadb

import embeddings
from busca import BM25, fundir_rankings
from ingestion import carregar_dados_mercado, montar_documento, montar_texto_busca

PASTA = pathlib.Path(__file__).resolve().parent
K = 3

def busca_hibrida(consulta, colecao, bm25, ids, candidatos=10):
    densa = colecao.query(query_texts=[consulta], n_results=candidatos)["ids"][0]
    lexical = [ids[i] for i in bm25.buscar(consulta, k=candidatos)]
    return fundir_rankings(lexical, densa)[:K]


def posicao_relevante(recuperados, relevantes):
    for posicao, doc_id in enumerate(recuperados, start=1):
        if doc_id in relevantes:
            return posicao
    return None


def resumir(posicoes, tempos):
    n = len(posicoes)
    return {
        "hit@1": round(100 * sum(p == 1 for p in posicoes) / n, 1),
        "hit@3": round(100 * sum(p is not None for p in posicoes) / n, 1),
        "mrr@3": round(sum(1 / p for p in posicoes if p) / n, 3),
        "latencia_ms": round(statistics.median(tempos), 1),
    }


def avaliar(nome, buscar, perguntas):
    buscar("aquecimento")  # a primeira consulta carrega o modelo; não entra na medição
    linhas = []
    for caso in perguntas:
        inicio = time.perf_counter()
        recuperados = buscar(caso["pergunta"])
        tempo = (time.perf_counter() - inicio) * 1000
        linhas.append({**caso, "recuperados": recuperados,
                       "posicao": posicao_relevante(recuperados, set(caso["relevantes"])), "tempo_ms": tempo})

    resultado = {"geral": resumir([r["posicao"] for r in linhas], [r["tempo_ms"] for r in linhas])}
    for tipo in ("direta", "parafrase", "sem_sobreposicao"):
        do_tipo = [r for r in linhas if r["tipo"] == tipo]
        resultado[tipo] = resumir([r["posicao"] for r in do_tipo], [r["tempo_ms"] for r in do_tipo])
    resultado["erros"] = [
        {"pergunta": r["pergunta"], "esperado": r["relevantes"], "recuperados": r["recuperados"]}
        for r in linhas if r["posicao"] is None
    ]
    print(f"{nome:<18} hit@1 {resultado['geral']['hit@1']:5.1f}%  hit@3 {resultado['geral']['hit@3']:5.1f}%  "
          f"MRR {resultado['geral']['mrr@3']:.3f}  paráfrase {resultado['parafrase']['hit@3']:5.1f}%  "
          f"sem sobreposição {resultado['sem_sobreposicao']['hit@3']:5.1f}%  "
          f"{resultado['geral']['latencia_ms']:6.1f} ms")
    return resultado


def main():
    base = carregar_dados_mercado()
    perguntas = json.loads((PASTA / "perguntas.json").read_text(encoding="utf-8"))
    ids = [t["id"] for t in base]
    print(f"{len(perguntas)} perguntas, {len(base)} documentos, top-{K}\n")

    # Dois formatos do texto que vira vetor:
    # - completo: o documento inteiro entregue ao LLM (metadados, números do Google Trends e descrição)
    # - descritivo: só termo, categoria, estilo e descrição (o que descreve a peça)
    formatos = {"completo": montar_documento, "descritivo": montar_texto_busca}
    resultados = {}
    cliente = chromadb.EphemeralClient()
    for formato, montar in formatos.items():
        documentos = [montar(t) for t in base]
        print(f"Formato {formato}:")
        bm25 = BM25(documentos)
        resultados[f"bm25/{formato}"] = avaliar("  bm25 (palavras)", lambda q, b=bm25: [ids[i] for i in b.buscar(q)], perguntas)
        for modelo in embeddings.modelos_disponiveis():
            colecao = cliente.get_or_create_collection(f"aval_{formato}_{modelo.replace('-', '_')}",
                                                       embedding_function=embeddings.funcao_embedding(modelo))
            colecao.upsert(ids=ids, documents=documentos)
            resultados[f"{modelo}/{formato}"] = avaliar(
                f"  {modelo}", lambda q, c=colecao: c.query(query_texts=[q], n_results=K)["ids"][0], perguntas)
            if modelo != "multilingue-fp32":
                resultados[f"hibrida-{modelo}/{formato}"] = avaliar(
                    f"  híbrida+{modelo}", lambda q, c=colecao, b=bm25: busca_hibrida(q, c, b, ids), perguntas)
        print()

    saida = PASTA / "resultados" / "recuperacao.json"
    saida.parent.mkdir(exist_ok=True)
    saida.write_text(json.dumps({"perguntas": len(perguntas), "documentos": len(base), "k": K,
                                 "resultados": resultados}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\nResultados em {saida.relative_to(PASTA.parent)}")


if __name__ == "__main__":
    main()
