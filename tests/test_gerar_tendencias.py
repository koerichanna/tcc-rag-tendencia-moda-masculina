import json

import models
import rag_engine

ROTA = "/ia/gerar-tendencias"


class LLMFalso:
    def __init__(self, texto=None, erro=None):
        self.texto, self.erro = texto, erro

    def invoke(self, prompt):
        if self.erro:
            raise self.erro
        return type("Resposta", (), {"content": self.texto})()


def usar_llm(monkeypatch, llm):
    monkeypatch.setattr(rag_engine, "_obter_llm", lambda **_: llm)


def test_sem_chave_de_ia_responde_503(client, monkeypatch):
    usar_llm(monkeypatch, None)
    resposta = client.post(ROTA, json={"tema": "Moda masculina 2027"})
    assert resposta.status_code == 503
    assert "chave" in resposta.json()["detail"]


def test_ia_que_estoura_o_tempo_responde_503_explicando(client, monkeypatch):
    usar_llm(monkeypatch, LLMFalso(erro=TimeoutError("504 DEADLINE_EXCEEDED")))
    resposta = client.post(ROTA, json={"tema": "Moda masculina 2027"})
    assert resposta.status_code == 503
    assert "não respondeu a tempo" in resposta.json()["detail"]


def test_resposta_fora_do_formato_responde_503(client, monkeypatch):
    usar_llm(monkeypatch, LLMFalso(texto="Desculpe, não consigo ajudar."))
    assert client.post(ROTA, json={"tema": "Moda masculina 2027"}).status_code == 503


def test_tendencias_geradas_ficam_marcadas_como_nao_verificadas(client, db_session, monkeypatch):
    sugestao = [{"termo": "Alfaiataria Utilitária Tech", "categoria": "Calças", "score_relevancia": 92,
                 "sazonalidade": "Atemporal", "nivel_risco": "Baixo", "descricao": "Calça de alfaiataria em tecido técnico."}]
    usar_llm(monkeypatch, LLMFalso(texto=json.dumps(sugestao, ensure_ascii=False)))

    resposta = client.post(ROTA, json={"tema": "Moda masculina 2027"})

    assert resposta.status_code == 200
    assert resposta.json()["mensagem"] == "1 tendências processadas"
    registro = db_session.query(models.TendenciaModel).filter_by(termo="Alfaiataria Utilitária Tech").one()
    assert registro.fonte == "Sugestão de LLM (não verificada)"


def test_geracao_usa_tempo_limite_maior(monkeypatch):
    recebido = {}
    monkeypatch.setattr(rag_engine, "_obter_llm", lambda **kw: recebido.update(kw))
    try:
        rag_engine.gerar_novas_tendencias_com_ia("tema")
    except rag_engine.LLMIndisponivel:
        pass
    assert recebido["timeout"] == rag_engine.TEMPO_LIMITE_GERACAO > rag_engine.TEMPO_LIMITE_LLM
