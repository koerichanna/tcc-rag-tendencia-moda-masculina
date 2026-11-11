import datetime

import pytest

from pipeline.preprocessamento import (
    atualizar_base,
    calcular_score,
    carregar_series,
    classificar_risco,
    classificar_sazonalidade,
    fracao_semanas_zeradas,
    interesse_recente,
    metricas_do_termo,
    perfil_sazonal,
    variacao_anual,
    volatilidade,
)


def semanas(valores, inicio=datetime.date(2022, 1, 2)):
    return [(inicio + datetime.timedelta(weeks=i), v) for i, v in enumerate(valores)]


def test_interesse_recente_usa_as_ultimas_12_semanas():
    assert interesse_recente([0] * 50 + [30] * 12) == 30


def test_variacao_anual_compara_os_dois_ultimos_anos():
    assert variacao_anual([40] * 52 + [60] * 52) == pytest.approx(50.0)
    assert variacao_anual([50] * 52 + [40] * 52) == pytest.approx(-20.0)


def test_variacao_anual_exige_dois_anos_de_dados():
    with pytest.raises(ValueError):
        variacao_anual([10] * 60)


def test_volatilidade_zero_para_serie_constante():
    assert volatilidade([25] * 52) == 0


def test_perfil_sazonal_encontra_o_mes_de_pico():
    # Interesse 100 em dezembro e 10 nos outros meses.
    pontos = [(d, 100 if d.month == 12 else 10) for d, _ in semanas([0] * 156)]
    mes, amplitude = perfil_sazonal(pontos)
    assert mes == 12
    assert amplitude > 2


@pytest.mark.parametrize("mes,amplitude,esperado", [
    (12, 2.0, "Primavera/Verão"),
    (6, 2.0, "Outono/Inverno"),
    (12, 1.1, "Atemporal"),
])
def test_classificar_sazonalidade(mes, amplitude, esperado):
    assert classificar_sazonalidade(mes, amplitude) == esperado


def test_score_combina_interesse_e_direcao():
    assert calcular_score(50, 0) == 50.0      # estável
    assert calcular_score(80, 50) == 90.0     # forte e subindo
    assert calcular_score(20, -80) == 10.0    # direção limitada a 0


@pytest.mark.parametrize("variacao,vol,esperado", [
    (-20, 0.1, "Alto"),
    (15, 0.2, "Baixo"),
    (15, 0.6, "Moderado"),   # cresce, mas oscila demais
    (0, 0.1, "Moderado"),
])
def test_classificar_risco(variacao, vol, esperado):
    assert classificar_risco(variacao, vol) == esperado


def test_carregar_series_ignora_semanas_parciais(tmp_path):
    csv = tmp_path / "coleta.csv"
    csv.write_text(
        "data,termo_busca,interesse,parcial\n"
        "2026-11-01,calça,40,False\n"
        "2026-11-08,calça,5,True\n",
        encoding="utf-8",
    )
    assert carregar_series(csv) == {"calça": [(datetime.date(2026, 11, 1), 40)]}


def test_atualizar_base_preenche_metricas_e_mantem_sem_serie():
    base = [{"termo_busca": "calça"}, {"termo_busca": "sem dados"}]
    series = {"calça": semanas([40] * 52 + [60] * 52)}
    atualizar_base(base, series, "2026-11-10")

    assert base[0]["nivel_risco"] == "Baixo"
    assert base[0]["metricas"]["variacao_12m_pct"] == 50.0
    assert base[0]["metricas"]["data_coleta"] == "2026-11-10"
    assert "metricas" not in base[1]


def test_fracao_semanas_zeradas_olha_os_ultimos_dois_anos():
    assert fracao_semanas_zeradas([5] * 100 + [0] * 52 + [3] * 52) == 0.5


def test_serie_esparsa_nao_gera_variacao_artificial():
    # 2 anos quase sem buscas e alguns picos isolados no último ano: antes isso virava "+100%"
    valores = [0] * 52 + [0] * 45 + [40, 0, 60, 0, 30, 0, 50] + [0] * 52
    m = metricas_do_termo(semanas(valores[-156:]))
    assert m["dados_esparsos"] is True
    assert m["variacao_12m_pct"] == 0.0
    assert m["nivel_risco"] == "Alto"
    assert m["sazonalidade"] == "Atemporal"


def test_serie_com_volume_continua_classificada_normalmente():
    m = metricas_do_termo(semanas([40] * 104 + [50] * 52))
    assert m["dados_esparsos"] is False
    assert m["variacao_12m_pct"] == 25.0
    assert m["nivel_risco"] == "Baixo"
