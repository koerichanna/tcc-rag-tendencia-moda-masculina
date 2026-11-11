import ingestion
import models
from database import Base, SessionLocal, engine


def tendencia(**extra):
    base = {
        "id": "trend_teste_01", "termo": "Calça Teste", "categoria": "Calças", "estilo": "Casual",
        "sazonalidade": "Atemporal", "nivel_risco": "Moderado", "score_relevancia": 50.0,
        "fonte": "Google Trends Brasil", "conteudo": "Descrição de teste.",
    }
    return {**base, **extra}


def test_documento_inclui_metricas_do_google_trends():
    t = tendencia(metricas={"data_coleta": "2026-11-10", "interesse_recente": 42.3,
                            "variacao_12m_pct": -6.6, "mes_pico": 12})
    doc = ingestion.montar_documento(t)
    assert "variação de -6.6%" in doc
    assert "pico de buscas em dezembro" in doc


def test_documento_sem_metricas_continua_valido():
    assert "Descrição: Descrição de teste." in ingestion.montar_documento(tendencia())


def test_sincronizar_atualiza_sem_duplicar():
    Base.metadata.create_all(bind=engine)
    try:
        ingestion.sincronizar_com_postgresql([tendencia()])
        ingestion.sincronizar_com_postgresql([tendencia(termo="Calça Renomeada", nivel_risco="Alto")])

        with SessionLocal() as db:
            registros = db.query(models.TendenciaModel).filter_by(codigo="trend_teste_01").all()
            assert len(registros) == 1
            assert registros[0].termo == "Calça Renomeada"
            assert registros[0].nivel_risco == "Alto"
    finally:
        Base.metadata.drop_all(bind=engine)
