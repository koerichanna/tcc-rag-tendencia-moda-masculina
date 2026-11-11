"""Métricas Prometheus próprias do domínio (as de HTTP vêm do instrumentator, em main.py)."""
from prometheus_client import Counter, Histogram

LLM_CHAMADAS = Counter(
    "moda_llm_chamadas_total",
    "Chamadas ao LLM por operação e resultado",
    ["operacao", "resultado"],  # resultado: sucesso | falha
)

LLM_LATENCIA = Histogram(
    "moda_llm_latencia_segundos",
    "Tempo de resposta do LLM por operação",
    ["operacao"],
    buckets=(0.5, 1, 2, 5, 10, 15, 20, 30, 45),
)

RAG_RESPOSTAS = Counter(
    "moda_rag_respostas_total",
    "Respostas do consultor RAG por origem",
    ["origem"],  # origem: llm | regras (fallback quando o LLM falha ou não está configurado)
)

RAG_AJUSTES = Counter(
    "moda_rag_ajustes_total",
    "Respostas do LLM corrigidas para respeitar o risco calculado (ver coerencia.py)",
    ["tipo"],  # tipo: risco | acao
)
