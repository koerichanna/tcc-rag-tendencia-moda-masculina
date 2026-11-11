"""Limite de requisições por IP nas rotas que chamam o LLM ou aceitam senha."""
import os

from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

# O IP vem de request.client, que o uvicorn preenche a partir do X-Forwarded-For
# (opção --proxy-headers no Dockerfile), já que a API fica atrás do Caddy e do Nginx.
limiter = Limiter(
    key_func=get_remote_address,
    enabled=os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true",
)

LOGIN = "5/minute"
LLM = "10/minute"
GERAR_TENDENCIAS = "3/minute"


def limite_excedido(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    # Todos os limites são por minuto, então 60 s é o tempo máximo até liberar.
    return JSONResponse(
        status_code=429,
        content={"detail": "Muitas requisições em pouco tempo. Aguarde um minuto e tente de novo."},
        headers={"Retry-After": "60"},
    )
