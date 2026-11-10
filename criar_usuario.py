"""Cria ou redefine a senha de um usuário pelo terminal.

Serve para criar o primeiro administrador; os demais usuários podem ser cadastrados por ele
na aba "Usuários" da aplicação. Também recupera o acesso se o admin esquecer a senha.

Uso:
    python criar_usuario.py <nome_usuario> [--admin]          # pede a senha no terminal
    SENHA_USUARIO=... python criar_usuario.py <nome> --admin  # senha por variável (uso em servidor)
"""
import getpass
import os
import sys

import auth
import migrar
import models
from database import SessionLocal

TAMANHO_MINIMO = auth.TAMANHO_MINIMO_SENHA


def salvar_usuario(nome_usuario: str, senha: str, admin: bool = False) -> bool:
    """Devolve True se criou, False se só trocou a senha de um usuário existente.

    Com admin=True o usuário também vira administrador e é reativado.
    """
    if len(senha) < TAMANHO_MINIMO:
        raise ValueError(f"A senha precisa ter pelo menos {TAMANHO_MINIMO} caracteres")
    with SessionLocal() as db:
        usuario = db.query(models.UsuarioModel).filter_by(nome_usuario=nome_usuario).first()
        criado = usuario is None
        if criado:
            usuario = models.UsuarioModel(nome_usuario=nome_usuario, perfil="usuario", ativo=True)
            db.add(usuario)
        if admin:
            usuario.perfil = auth.PERFIL_ADMIN
            usuario.ativo = True
        usuario.senha_hash = auth.gerar_hash(senha)
        db.commit()
    return criado


if __name__ == "__main__":
    argumentos = [a for a in sys.argv[1:] if a != "--admin"]
    if len(argumentos) != 1:
        sys.exit(__doc__)
    admin = "--admin" in sys.argv
    migrar.aplicar()
    nome = argumentos[0].strip()
    senha = os.getenv("SENHA_USUARIO") or getpass.getpass(f"Senha para {nome}: ")
    try:
        criado = salvar_usuario(nome, senha, admin=admin)
    except ValueError as erro:
        sys.exit(str(erro))
    perfil = " (administrador)" if admin else ""
    print(f"Usuário '{nome}' {'criado' if criado else 'atualizado'}{perfil}.")
