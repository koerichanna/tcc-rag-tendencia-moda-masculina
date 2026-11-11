"""Transforma a coleta bruta do Google Trends em métricas e atualiza data/market_trends.json.

Uso: python -m pipeline.preprocessamento [caminho_do_csv]
Sem argumento, usa a coleta mais recente em data/raw/.

As regras e limiares estão documentados em data/README.md.
"""
import csv
import datetime
import json
import logging
import pathlib
import statistics
import sys
from collections import defaultdict

BASE = pathlib.Path(__file__).resolve().parent.parent
ARQUIVO_BASE = BASE / "data" / "market_trends.json"
PASTA_RAW = BASE / "data" / "raw"

SEMANAS_RECENTES = 12
SEMANAS_ANO = 52
AMPLITUDE_SAZONAL_MINIMA = 1.25  # pico mensal 25% acima da média geral
MESES_PRIMAVERA_VERAO = {9, 10, 11, 12, 1, 2}  # hemisfério sul
LIMITE_SEMANAS_ZERADAS = 0.5  # metade das semanas dos últimos 2 anos sem buscas = dados esparsos

logger = logging.getLogger("projeto_moda.preprocessamento")


def carregar_series(caminho_csv):
    """Lê o CSV bruto e devolve {termo_busca: [(data, interesse), ...]} sem semanas parciais."""
    series = defaultdict(list)
    with open(caminho_csv, encoding="utf-8") as f:
        for linha in csv.DictReader(f):
            if linha["parcial"] == "True":
                continue
            data = datetime.date.fromisoformat(linha["data"])
            series[linha["termo_busca"]].append((data, int(linha["interesse"])))
    for pontos in series.values():
        pontos.sort()
    return dict(series)


def interesse_recente(valores, semanas=SEMANAS_RECENTES):
    return statistics.fmean(valores[-semanas:])


def variacao_anual(valores):
    """Variação percentual da média das últimas 52 semanas sobre as 52 anteriores."""
    if len(valores) < 2 * SEMANAS_ANO:
        raise ValueError("série precisa de pelo menos 104 semanas")
    atual = statistics.fmean(valores[-SEMANAS_ANO:])
    anterior = statistics.fmean(valores[-2 * SEMANAS_ANO:-SEMANAS_ANO])
    if anterior == 0:
        return 0.0 if atual == 0 else 100.0
    return (atual - anterior) / anterior * 100


def volatilidade(valores):
    """Coeficiente de variação das últimas 52 semanas (0 = estável)."""
    ultimo_ano = valores[-SEMANAS_ANO:]
    media = statistics.fmean(ultimo_ano)
    return statistics.pstdev(ultimo_ano) / media if media else 0.0


def perfil_sazonal(pontos):
    """Devolve (mês de pico, amplitude) usando a média do interesse por mês do ano."""
    por_mes = defaultdict(list)
    for data, valor in pontos:
        por_mes[data.month].append(valor)
    medias = {mes: statistics.fmean(v) for mes, v in por_mes.items()}
    media_geral = statistics.fmean(medias.values())
    mes_pico = max(medias, key=medias.get)
    amplitude = medias[mes_pico] / media_geral if media_geral else 1.0
    return mes_pico, amplitude


def classificar_sazonalidade(mes_pico, amplitude):
    if amplitude < AMPLITUDE_SAZONAL_MINIMA:
        return "Atemporal"
    return "Primavera/Verão" if mes_pico in MESES_PRIMAVERA_VERAO else "Outono/Inverno"


def calcular_score(recente, variacao):
    """Metade pelo interesse atual, metade pela direção da tendência (50 = estável)."""
    direcao = min(max(50 + variacao, 0), 100)
    return round(0.5 * recente + 0.5 * direcao, 1)


def classificar_risco(variacao, vol):
    if variacao <= -15:
        return "Alto"
    if variacao >= 10 and vol < 0.35:
        return "Baixo"
    return "Moderado"


def fracao_semanas_zeradas(valores):
    """Fração das últimas 104 semanas sem nenhuma busca registrada pelo Google."""
    ultimos = valores[-2 * SEMANAS_ANO:]
    return sum(v == 0 for v in ultimos) / len(ultimos)


def metricas_do_termo(pontos):
    valores = [v for _, v in pontos]
    recente = interesse_recente(valores)
    vol = volatilidade(valores)
    mes_pico, amplitude = perfil_sazonal(pontos)
    zeradas = fracao_semanas_zeradas(valores)
    esparso = zeradas >= LIMITE_SEMANAS_ZERADAS

    if esparso:
        # Com a maioria das semanas em zero, a variação anual vira ruído (ex.: média anterior 0 dá
        # "+100%"). Sem volume de busca não há evidência de demanda, então o risco para estoque é Alto.
        variacao = 0.0
        risco = "Alto"
    else:
        variacao = variacao_anual(valores)
        risco = classificar_risco(variacao, vol)

    return {
        "interesse_recente": round(recente, 1),
        "variacao_12m_pct": round(variacao, 1),
        "volatilidade": round(vol, 2),
        "mes_pico": mes_pico,
        "amplitude_sazonal": round(amplitude, 2),
        "semanas_zeradas_pct": round(100 * zeradas, 1),
        "dados_esparsos": esparso,
        "score_relevancia": calcular_score(recente, variacao),
        "nivel_risco": risco,
        "sazonalidade": "Atemporal" if esparso else classificar_sazonalidade(mes_pico, amplitude),
    }


def atualizar_base(base, series, data_coleta):
    for item in base:
        pontos = series.get(item["termo_busca"])
        if not pontos:
            logger.warning("Sem série para '%s', registro mantido sem métricas", item["termo_busca"])
            continue
        m = metricas_do_termo(pontos)
        item["score_relevancia"] = m.pop("score_relevancia")
        item["nivel_risco"] = m.pop("nivel_risco")
        item["sazonalidade"] = m.pop("sazonalidade")
        item["metricas"] = {**m, "data_coleta": data_coleta}
    return base


def coleta_mais_recente(pasta=PASTA_RAW):
    arquivos = sorted(pasta.glob("google_trends_*.csv"))
    if not arquivos:
        raise FileNotFoundError("Nenhuma coleta em data/raw/. Rode python -m pipeline.coleta_trends")
    return arquivos[-1]


def main(caminho_csv=None):
    caminho = pathlib.Path(caminho_csv) if caminho_csv else coleta_mais_recente()
    data_coleta = caminho.stem.removeprefix("google_trends_")
    with open(ARQUIVO_BASE, encoding="utf-8") as f:
        base = json.load(f)
    atualizar_base(base, carregar_series(caminho), data_coleta)
    ARQUIVO_BASE.write_text(json.dumps(base, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    logger.info("Base atualizada com a coleta %s", caminho.name)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    main(sys.argv[1] if len(sys.argv) > 1 else None)
