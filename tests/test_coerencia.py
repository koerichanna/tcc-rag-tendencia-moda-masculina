import itertools

import pytest

import coerencia
import rag_engine


@pytest.mark.parametrize("acao,tipo", [
    ("Aumentar Pedido com Urgência", "compra"),
    ("Reforçar Estoque", "compra"),
    ("Apostar na Coleção (Compra Alta)", "compra"),
    ("Evitar Compra / Realizar Liquidação", "cautela"),
    ("Reduzir Estoque / Realizar Ação Promocional", "cautela"),
    ("Não Recomprar", "cautela"),
    ("Evitar aumentar o pedido", "cautela"),
    ("Testar Lote Moderado", "neutra"),
    ("Manter Monitoramento", "neutra"),
])
def test_classificar_acao(acao, tipo):
    assert coerencia.classificar_acao(acao) == tipo


def resposta(acao, risco):
    return {"acao_recomendada": acao, "nivel_risco": risco, "justificativa_explicavel": "Texto do modelo."}


def test_risco_alto_nao_aceita_recomendacao_de_compra():
    r = resposta("Aumentar Pedido com Urgência", "Alto")
    assert coerencia.alinhar(r, "Alto", "Não Recomprar") == ["acao"]
    assert r["acao_recomendada"] == "Não Recomprar"
    assert "Aumentar Pedido com Urgência" in r["justificativa_explicavel"]
    assert r["justificativa_explicavel"].endswith("Texto do modelo.")


def test_risco_baixo_nao_aceita_liquidacao():
    r = resposta("Evitar Compra / Realizar Liquidação", "Baixo")
    assert coerencia.alinhar(r, "Baixo", "Reforçar Estoque") == ["acao"]
    assert r["acao_recomendada"] == "Reforçar Estoque"


def test_risco_trocado_pelo_modelo_volta_ao_calculado():
    r = resposta("Testar Lote Moderado", "Baixo")
    assert coerencia.alinhar(r, "Moderado", "Testar Lote Moderado") == ["risco"]
    assert r["nivel_risco"] == "Moderado"


def test_resposta_coerente_fica_como_esta():
    r = resposta("Reforçar Estoque", "Baixo")
    assert coerencia.alinhar(r, "Baixo", "Aumentar Pedido com Urgência") == []
    assert r == resposta("Reforçar Estoque", "Baixo")


def test_risco_moderado_aceita_qualquer_acao():
    for acao in ["Aumentar Pedido", "Reduzir Estoque", "Testar Lote"]:
        assert coerencia.acao_compativel(acao, "Moderado")


@pytest.mark.parametrize("risco,score,estoque", itertools.product(
    ["Baixo", "Moderado", "Alto"], [20, 44, 50, 75, 90], [0, 5, 30]))
def test_regras_locais_nunca_contradizem_o_proprio_risco(risco, score, estoque):
    """A ação das regras substitui a do LLM quando ele erra, então ela mesma precisa ser coerente."""
    docs = [{"id": "t", "documento": "doc", "metadados": {
        "termo": "T", "categoria": "Calças", "score_relevancia": score, "nivel_risco": risco, "fonte": "Google Trends Brasil"}}]
    for produto in [None, {"nome": "P", "quantidade_estoque": estoque, "estoque_minimo": 5}]:
        r = rag_engine.sintetizar_resposta_contextual("pergunta", docs, produto)
        assert coerencia.acao_compativel(r["acao_recomendada"], risco), (risco, score, produto, r["acao_recomendada"])


class LLMQueManda:
    def __init__(self, acao, risco):
        self.texto = f'{{"diagnostico": "d", "acao_recomendada": "{acao}", "nivel_risco": "{risco}", ' \
                     f'"justificativa_explicavel": "j", "fontes_consultadas": []}}'
        self.prompts = []

    def invoke(self, prompt):
        self.prompts.append(prompt)
        return type("Resposta", (), {"content": self.texto})()


def test_consulta_corrige_llm_que_contradiz_risco(monkeypatch):
    llm = LLMQueManda("Aumentar Pedido com Urgência", "Baixo")
    monkeypatch.setattr(rag_engine, "_obter_llm", lambda: llm)
    resultado = rag_engine.consultar_rag("Ainda compensa comprar calça jeans skinny?", categoria="Calças",
                                         salvar_historico=False)
    risco_calculado = rag_engine.vector_db.buscar_tendencias_similares(
        "Ainda compensa comprar calça jeans skinny?", n_results=1, categoria="Calças")[0]["metadados"]["nivel_risco"]

    assert resultado["nivel_risco"] == risco_calculado
    assert coerencia.acao_compativel(resultado["acao_recomendada"], risco_calculado)
    assert "Risco calculado a partir dos dados do Google Trends" in llm.prompts[0]
