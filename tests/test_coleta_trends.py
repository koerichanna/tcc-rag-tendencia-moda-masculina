import sys
import types

import pytest

from pipeline import coleta_trends


class SemDados:
    empty = True


def instalar_pytrends_falso(monkeypatch, falhas):
    """Simula o pytrends: as primeiras `falhas` consultas dão erro (como o 429 do Google)."""
    chamadas = []

    class TrendReq:
        def __init__(self, **kwargs):
            pass

        def build_payload(self, termos, **kwargs):
            chamadas.append(termos[0])
            if len(chamadas) <= falhas:
                raise ConnectionError("429")

        def interest_over_time(self):
            return SemDados()

    modulo = types.ModuleType("pytrends.request")
    modulo.TrendReq = TrendReq
    monkeypatch.setitem(sys.modules, "pytrends", types.ModuleType("pytrends"))
    monkeypatch.setitem(sys.modules, "pytrends.request", modulo)
    monkeypatch.setattr(coleta_trends.time, "sleep", lambda segundos: None)
    return chamadas


def test_coletar_tenta_de_novo_quando_o_google_recusa(monkeypatch):
    chamadas = instalar_pytrends_falso(monkeypatch, falhas=2)
    assert coleta_trends.coletar(["camisa de linho"]) == []
    assert chamadas == ["camisa de linho"] * 3


def test_coletar_desiste_depois_de_tres_falhas(monkeypatch):
    instalar_pytrends_falso(monkeypatch, falhas=3)
    with pytest.raises(RuntimeError, match="camisa de linho"):
        coleta_trends.coletar(["camisa de linho"])
