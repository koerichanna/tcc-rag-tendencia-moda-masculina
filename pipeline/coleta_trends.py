"""Coleta o interesse de busca semanal (Brasil, últimos 5 anos) no Google Trends.

Uso: python -m pipeline.coleta_trends
Saída: data/raw/google_trends_<AAAA-MM-DD>.csv com colunas data, termo_busca, interesse, parcial
(parcial = semana ainda em andamento no momento da coleta).

Cada termo é consultado sozinho: o Google normaliza o interesse de 0 a 100 dentro de cada
consulta, então cada série fica relativa ao próprio pico no período.
"""
import csv
import datetime
import json
import logging
import pathlib
import random
import time

BASE = pathlib.Path(__file__).resolve().parent.parent
ARQUIVO_BASE = BASE / "data" / "market_trends.json"
PASTA_RAW = BASE / "data" / "raw"

logger = logging.getLogger("projeto_moda.coleta")


def termos_da_base():
    with open(ARQUIVO_BASE, encoding="utf-8") as f:
        return [t["termo_busca"] for t in json.load(f)]


def coletar(termos, geo="BR", periodo="today 5-y"):
    try:
        # Usa os certificados do sistema operacional (necessário atrás de proxy corporativo).
        import truststore
        truststore.inject_into_ssl()
    except ImportError:
        pass
    from pytrends.request import TrendReq

    cliente = TrendReq(hl="pt-BR", tz=180, timeout=(10, 30))
    linhas = []
    for termo in termos:
        for tentativa in range(3):
            try:
                cliente.build_payload([termo], geo=geo, timeframe=periodo)
                df = cliente.interest_over_time()
                break
            except Exception as erro:  # o Google responde 429 quando há muitas consultas seguidas
                espera = 30 * (tentativa + 1)
                logger.warning("Falha em '%s' (%s), nova tentativa em %ss", termo, erro, espera)
                time.sleep(espera)
        else:
            raise RuntimeError(f"Não foi possível coletar '{termo}'")

        if df.empty:
            logger.warning("Sem dados para '%s'", termo)
            continue
        for data, linha in df.iterrows():
            linhas.append({
                "data": data.date().isoformat(),
                "termo_busca": termo,
                "interesse": int(linha[termo]),
                "parcial": bool(linha["isPartial"]),
            })
        logger.info("'%s': %d semanas", termo, len(df))
        time.sleep(random.uniform(5, 10))
    return linhas


def salvar(linhas, pasta=PASTA_RAW):
    pasta.mkdir(parents=True, exist_ok=True)
    destino = pasta / f"google_trends_{datetime.date.today().isoformat()}.csv"
    with open(destino, "w", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=["data", "termo_busca", "interesse", "parcial"])
        escritor.writeheader()
        escritor.writerows(linhas)
    return destino


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    arquivo = salvar(coletar(termos_da_base()))
    logger.info("Coleta salva em %s", arquivo)
