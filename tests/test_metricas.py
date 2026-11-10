import pytest
from prometheus_client import REGISTRY

import rag_engine


def valor(nome, **rotulos):
    return REGISTRY.get_sample_value(nome, rotulos) or 0.0


def test_metrics_expoe_requisicoes_por_rota(client):
    client.get("/produtos/")
    texto = client.get("/metrics").text
    assert 'http_requests_total{handler="/produtos/",method="GET",status="2xx"}' in texto


def test_consulta_sem_llm_conta_resposta_das_regras(client, monkeypatch):
    monkeypatch.setattr(rag_engine, "_obter_llm", lambda: None)
    antes = valor("moda_rag_respostas_total", origem="regras")

    resposta = client.post("/rag/consultar", json={"pergunta": "Vale comprar camisa de linho?"})

    assert resposta.status_code == 200
    assert valor("moda_rag_respostas_total", origem="regras") == antes + 1


class LLMFalso:
    def __init__(self, erro=None):
        self.erro = erro

    def invoke(self, prompt):
        if self.erro:
            raise self.erro
        return type("Resposta", (), {"content": '{"ok": true}'})()


def test_invocar_llm_registra_sucesso_e_latencia():
    sucesso = valor("moda_llm_chamadas_total", operacao="teste", resultado="sucesso")
    medicoes = valor("moda_llm_latencia_segundos_count", operacao="teste")

    assert rag_engine._invocar_llm(LLMFalso(), "prompt", "teste") == '{"ok": true}'

    assert valor("moda_llm_chamadas_total", operacao="teste", resultado="sucesso") == sucesso + 1
    assert valor("moda_llm_latencia_segundos_count", operacao="teste") == medicoes + 1


def test_invocar_llm_registra_falha_e_repassa_o_erro():
    falhas = valor("moda_llm_chamadas_total", operacao="teste", resultado="falha")

    with pytest.raises(TimeoutError):
        rag_engine._invocar_llm(LLMFalso(TimeoutError("demorou")), "prompt", "teste")

    assert valor("moda_llm_chamadas_total", operacao="teste", resultado="falha") == falhas + 1
