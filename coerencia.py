"""Garante que a resposta do LLM respeite o risco calculado a partir do Google Trends.

O risco (Baixo, Moderado, Alto) vem do pré-processamento dos dados reais (pipeline/preprocessamento.py).
O LLM só redige a recomendação. Se ele contradiz o risco (ex.: risco Alto e ação "Aumentar
Pedido"), a resposta perde a explicabilidade. Por isso, depois de cada resposta:

1. o nivel_risco volta a ser o calculado, se o LLM trocou;
2. se a ação for incompatível com esse risco, entra a ação das regras locais e a justificativa
   avisa que houve ajuste.

Compatibilidade:
- risco Alto: não pode recomendar compra (aumentar, reforçar, apostar...);
- risco Baixo: não pode recomendar liquidar ou evitar a tendência;
- risco Moderado: qualquer ação é aceita (a decisão depende do estoque da loja).
"""
import unicodedata

# Comparação sem acento e em minúsculas: "Reforçar" e "reforcar" contam igual.
SINAIS_DE_COMPRA = ("aumentar", "reforcar", "apostar", "ampliar", "comprar mais", "compra alta", "repor com urgencia")
SINAIS_DE_CAUTELA = ("evitar", "reduzir", "liquidar", "liquidacao", "nao recomprar", "nao comprar", "suspender",
                     "promocao", "promocional", "desovar")

RISCOS = ("Baixo", "Moderado", "Alto")


def _simplificar(texto: str) -> str:
    return unicodedata.normalize("NFKD", (texto or "").lower()).encode("ascii", "ignore").decode()


def classificar_acao(acao: str) -> str:
    """'compra', 'cautela' ou 'neutra'. Cautela vence: "Evitar aumentar o pedido" é cautela."""
    texto = _simplificar(acao)
    if any(s in texto for s in SINAIS_DE_CAUTELA):
        return "cautela"
    if any(s in texto for s in SINAIS_DE_COMPRA):
        return "compra"
    return "neutra"


def acao_compativel(acao: str, risco: str) -> bool:
    tipo = classificar_acao(acao)
    if risco == "Alto":
        return tipo != "compra"
    if risco == "Baixo":
        return tipo != "cautela"
    return True


def alinhar(resposta: dict, risco_calculado: str, acao_das_regras: str) -> list:
    """Corrige a resposta no lugar e devolve a lista de ajustes feitos ('risco', 'acao')."""
    if risco_calculado not in RISCOS:
        return []
    ajustes = []
    if resposta.get("nivel_risco") != risco_calculado:
        resposta["nivel_risco"] = risco_calculado
        ajustes.append("risco")
    acao_llm = resposta.get("acao_recomendada", "")
    if not acao_compativel(acao_llm, risco_calculado):
        resposta["acao_recomendada"] = acao_das_regras
        resposta["justificativa_explicavel"] = (
            f"[Ação ajustada pelo sistema: o modelo sugeriu \"{acao_llm}\", incompatível com o risco "
            f"{risco_calculado} calculado a partir do Google Trends.] "
            + resposta.get("justificativa_explicavel", "")
        )
        ajustes.append("acao")
    return ajustes


def regras_para_prompt() -> str:
    return (
        "- Risco Alto: NÃO recomende comprar, aumentar ou reforçar estoque; prefira evitar, reduzir ou testar com cautela.\n"
        "- Risco Baixo: NÃO recomende liquidar nem evitar a tendência; prefira reforçar, repor ou manter.\n"
        "- Risco Moderado: decida pelo estoque da loja (testar lote, manter ou repor com moderação)."
    )
