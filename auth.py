"""Autenticação por usuário e senha com token JWT.

Fluxo: POST /auth/login devolve um token; as rotas protegidas recebem o token no cabeçalho
`Authorization: Bearer <token>` e usam a dependência `usuario_atual`.
"""
import datetime
import logging
import os
import secrets

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

import models
from database import get_db

logger = logging.getLogger("projeto_moda.auth")

ALGORITMO = "HS256"
VALIDADE = datetime.timedelta(hours=8)
PERFIL_ADMIN = "admin"
TAMANHO_MINIMO_SENHA = 10


def _carregar_segredo():
    segredo = os.getenv("JWT_SECRET", "").strip()
    if segredo:
        return segredo
    if os.getenv("ENVIRONMENT") in ("production", "staging"):
        raise RuntimeError("JWT_SECRET é obrigatório em produção e homologação")
    # Em desenvolvimento, um segredo aleatório basta: os tokens só valem até reiniciar a API.
    logger.warning("JWT_SECRET não definido; usando segredo temporário de desenvolvimento")
    return secrets.token_urlsafe(32)


SEGREDO = _carregar_segredo()

oauth2 = OAuth2PasswordBearer(tokenUrl="/auth/login")


def gerar_hash(senha: str) -> str:
    return bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def senha_confere(senha: str, senha_hash: str) -> bool:
    return bcrypt.checkpw(senha.encode("utf-8"), senha_hash.encode("utf-8"))


def criar_token(nome_usuario: str) -> str:
    agora = datetime.datetime.now(datetime.timezone.utc)
    dados = {"sub": nome_usuario, "iat": agora, "exp": agora + VALIDADE}
    return jwt.encode(dados, SEGREDO, algorithm=ALGORITMO)


def autenticar(db: Session, nome_usuario: str, senha: str):
    # Nomes são gravados em minúsculas (ver schemas.NomeUsuario).
    usuario = db.query(models.UsuarioModel).filter_by(nome_usuario=nome_usuario.strip().lower()).first()
    if usuario is None or not usuario.ativo or not senha_confere(senha, usuario.senha_hash):
        return None
    return usuario


def usuario_atual(token: str = Depends(oauth2), db: Session = Depends(get_db)) -> models.UsuarioModel:
    erro = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Faça login para executar esta ação",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        dados = jwt.decode(token, SEGREDO, algorithms=[ALGORITMO])
    except jwt.ExpiredSignatureError:
        erro.detail = "Sessão expirada, faça login novamente"
        raise erro
    except jwt.InvalidTokenError:
        raise erro

    # Consulta o banco a cada requisição: desativar um usuário derruba o token dele na hora.
    usuario = db.query(models.UsuarioModel).filter_by(nome_usuario=dados.get("sub")).first()
    if usuario is None or not usuario.ativo:
        raise erro
    return usuario


def exigir_admin(usuario: models.UsuarioModel = Depends(usuario_atual)) -> models.UsuarioModel:
    if usuario.perfil != PERFIL_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas administradores podem executar esta ação",
        )
    return usuario
