"""Configuração e ações repetidas dos testes de interface."""
import os

URL = os.getenv("E2E_URL")
ADMIN = os.getenv("E2E_ADMIN", "anna")
SENHA_ADMIN = os.getenv("E2E_SENHA", "")


def entrar(pagina, nome, senha):
    pagina.get_by_label("Usuário", exact=True).fill(nome)
    pagina.get_by_label("Senha", exact=True).fill(senha)
    pagina.get_by_role("button", name="Entrar").click()


def sair(pagina):
    pagina.get_by_role("button", name="Sair").click()
