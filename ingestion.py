import json
import logging

import migrar
import models
import vector_db
import vinculo
from database import SessionLocal

DATA_FILE = "./data/market_trends.json"

MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto",
         "setembro", "outubro", "novembro", "dezembro"]

logger = logging.getLogger("projeto_moda.ingestion")

def carregar_dados_mercado():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def descrever_metricas(t):
    m = t.get("metricas")
    if not m:
        return ""
    if m.get("dados_esparsos"):
        return (
            f"Google Trends Brasil (coleta de {m['data_coleta']}): volume de busca insuficiente, "
            f"{m['semanas_zeradas_pct']:.0f}% das semanas dos últimos 2 anos sem buscas; não há evidência de demanda. "
        )
    return (
        f"Google Trends Brasil (coleta de {m['data_coleta']}): interesse recente {m['interesse_recente']}/100, "
        f"variação de {m['variacao_12m_pct']:+.1f}% nas buscas em 12 meses, pico de buscas em {MESES[m['mes_pico'] - 1]}. "
    )

def montar_documento(t):
    return (
        f"Tendência: {t['termo']}. Categoria: {t['categoria']}. "
        f"Estilo: {t['estilo']}. Sazonalidade: {t['sazonalidade']}. "
        f"Nível de Risco: {t['nivel_risco']}. Relevância: {t['score_relevancia']}/100. "
        f"{descrever_metricas(t)}"
        f"Descrição: {t['conteudo']}"
    )

def montar_texto_busca(t):
    """Texto que vira vetor: só o que descreve a peça, sem os números e rótulos repetidos em
    todos os documentos (eles faziam os documentos parecerem iguais para o modelo multilíngue;
    ver docs/avaliacao_rag.md)."""
    return f"{t['termo']}. Categoria: {t['categoria']}. Estilo: {t['estilo']}. {t['conteudo']}"

def indexar_no_chromadb(trends):
    # upsert pelo id da base: atualiza os documentos da base e preserva os que
    # foram adicionados depois pela API (/ia/gerar-tendencias).
    collection = vector_db.get_trends_collection()
    collection.upsert(
        ids=[t["id"] for t in trends],
        documents=[montar_texto_busca(t) for t in trends],
        metadatas=[{
            "texto_completo": montar_documento(t),
            "termo": t["termo"],
            "categoria": t["categoria"],
            "estilo": t["estilo"],
            "sazonalidade": t["sazonalidade"],
            "nivel_risco": t["nivel_risco"],
            "score_relevancia": float(t["score_relevancia"]),
            "fonte": t["fonte"],
        } for t in trends],
    )
    logger.info("Indexados %d documentos no ChromaDB", len(trends))
    return collection

def sincronizar_com_postgresql(trends):
    db = SessionLocal()
    try:
        inseridos = atualizados = 0
        for t in trends:
            registro = db.query(models.TendenciaModel).filter(models.TendenciaModel.codigo == t["id"]).first()
            if registro is None:
                registro = models.TendenciaModel(codigo=t["id"])
                db.add(registro)
                inseridos += 1
            else:
                atualizados += 1
            registro.termo = t["termo"]
            registro.categoria = t["categoria"]
            registro.score_relevancia = float(t["score_relevancia"])
            registro.sazonalidade = t["sazonalidade"]
            registro.nivel_risco = t["nivel_risco"]
            registro.descricao = t["conteudo"]
            registro.fonte = t["fonte"]
        db.commit()
        logger.info("PostgreSQL: %d inseridos, %d atualizados", inseridos, atualizados)
    finally:
        db.close()

def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    migrar.aplicar()
    trends = carregar_dados_mercado()
    indexar_no_chromadb(trends)
    sincronizar_com_postgresql(trends)
    # Scores novos mudam o score dos produtos: refaz o vínculo de todos.
    with SessionLocal() as db:
        vinculo.revincular_todos(db, models.ProdutoModel)

if __name__ == "__main__":
    main()
