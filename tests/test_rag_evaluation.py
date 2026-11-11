"""Regressão da recuperação: roda o conjunto de avaliação inteiro na busca usada pela API.

Os limites ficam um pouco abaixo do resultado medido (hit@1 61,9% e hit@3 75,2% nas 105 perguntas, ver
docs/avaliacao_rag.md) para o teste falhar se uma mudança piorar a busca, mas não por uma
pergunta a mais ou a menos. A latência não é verificada aqui: ela oscila com a carga da máquina
do CI e fica medida em avaliacao/avaliar_recuperacao.py.
"""
import json
import pathlib

import vector_db
from rag_engine import consultar_rag

PERGUNTAS = json.loads((pathlib.Path(__file__).parent.parent / "avaliacao" / "perguntas.json").read_text(encoding="utf-8"))
HIT1_MINIMO = 57.0
HIT3_MINIMO = 70.0


def test_recuperacao_no_conjunto_de_avaliacao():
    acertos_1 = acertos_3 = 0
    for caso in PERGUNTAS:
        ids = [d["id"] for d in vector_db.buscar_tendencias_similares(caso["pergunta"], n_results=3)]
        relevantes = set(caso["relevantes"])
        acertos_1 += ids[:1] and ids[0] in relevantes
        acertos_3 += bool(relevantes & set(ids))

    hit1 = 100 * acertos_1 / len(PERGUNTAS)
    hit3 = 100 * acertos_3 / len(PERGUNTAS)
    assert hit1 >= HIT1_MINIMO, f"hit@1 caiu para {hit1:.1f}%"
    assert hit3 >= HIT3_MINIMO, f"hit@3 caiu para {hit3:.1f}%"


def test_documento_entregue_ao_llm_traz_os_numeros_do_google_trends():
    doc = vector_db.buscar_tendencias_similares("calça wide leg", n_results=1)[0]
    assert doc["id"] == "trend_wide_leg_02"
    assert "Google Trends Brasil" in doc["documento"]
    assert "Nível de Risco" in doc["documento"]


def test_schema_explicabilidade_rag():
    resultado = consultar_rag(pergunta="Como está a demanda por bermudas de alfaiataria?", salvar_historico=False)

    for chave in ["pergunta", "diagnostico", "acao_recomendada", "nivel_risco",
                  "justificativa_explicavel", "fontes_consultadas"]:
        assert chave in resultado, f"Chave de explicabilidade ausente: {chave}"
    assert resultado["nivel_risco"] in ["Baixo", "Moderado", "Alto"]
    assert len(resultado["justificativa_explicavel"]) > 20
