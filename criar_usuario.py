"""Cria ou redefine a senha de um usuário.

Uso:
    python criar_usuario.py <nome_usuario>          # pede a senha no terminal
    SENHA_USUARIO=... python criar_usuario.py <nome> # senha por variável (uso em servidor)
"""
import getpass
import os
import sys

import auth
import migrar
import models
from database import SessionLocal

TAMANHO_MINIMO = 10


def salvar_usuario(nome_usuario: str, senha: str) -> bool:
    """Devolve True se criou, False se só trocou a senha de um usuário existente."""
    if len(senha) < TAMANHO_MINIMO:
        raise ValueError(f"A senha precisa ter pelo menos {TAMANHO_MINIMO} caracteres")
    with SessionLocal() as db:
        usuario = db.query(models.UsuarioModel).filter_by(nome_usuario=nome_usuario).first()
        criado = usuario is None
        if criado:
            usuario = models.UsuarioModel(nome_usuario=nome_usuario)
            db.add(usuario)
        usuario.senha_hash = auth.gerar_hash(senha)
        db.commit()
    return criado


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    migrar.aplicar()
    nome = sys.argv[1].strip()
    senha = os.getenv("SENHA_USUARIO") or getpass.getpass(f"Senha para {nome}: ")
    try:
        criado = salvar_usuario(nome, senha)
    except ValueError as erro:
        sys.exit(str(erro))
    print(f"Usuário '{nome}' {'criado' if criado else 'atualizado'}.")
