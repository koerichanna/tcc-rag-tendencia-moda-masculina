"""Vincula cada produto da loja à tendência mais parecida da base, pela busca vetorial.

O `tendencia_score` do produto deixa de ser digitado: passa a ser o `score_relevancia` da
tendência vinculada, que vem do Google Trends. O vínculo é refeito quando o nome ou a categoria
do produto mudam e a cada ingestão (quando uma coleta nova muda os scores).

A busca fica restrita à categoria do produto (uma calça só se vincula a tendências de calças) e
ignora as tendências sugeridas pelo LLM, cujo score não vem de dados reais.
"""
import logging

import vector_db

logger = logging.getLogger("projeto_moda.vinculo")

FONTE_LLM = "Sugestão de LLM (não verificada)"


def tendencia_mais_proxima(nome: str, categoria: str):
    resultados = vector_db.buscar(
        nome, n_results=1, where={"$and": [{"categoria": categoria}, {"fonte": {"$ne": FONTE_LLM}}]})
    return resultados[0] if resultados else None


def vincular(produto) -> bool:
    """Atualiza tendencia_codigo e tendencia_score do produto. Devolve False se não achou tendência
    (nesse caso o score informado no cadastro é mantido)."""
    try:
        tendencia = tendencia_mais_proxima(produto.nome, produto.categoria)
    except Exception as erro:  # base vetorial indisponível não deve impedir o cadastro
        logger.warning("Não foi possível vincular '%s' a uma tendência: %s", produto.nome, erro)
        return False
    if tendencia is None:
        produto.tendencia_codigo = None
        return False
    produto.tendencia_codigo = tendencia["id"]
    produto.tendencia_score = float(tendencia["metadados"]["score_relevancia"])
    return True


def revincular_todos(db, modelo_produto) -> int:
    produtos = db.query(modelo_produto).all()
    vinculados = sum(vincular(p) for p in produtos)
    db.commit()
    logger.info("Produtos vinculados a tendências: %d de %d", vinculados, len(produtos))
    return vinculados
