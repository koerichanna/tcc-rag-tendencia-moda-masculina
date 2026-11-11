"""Testes de interface (Playwright) contra a aplicação rodando de verdade.

Precisam da API e do frontend no ar e de um admin criado (ver o job "e2e" em .github/workflows/ci.yml):
    E2E_URL=http://localhost:4173 E2E_ADMIN=anna E2E_SENHA=... pytest e2e/
Sem E2E_URL, os testes são pulados, então `pytest` na raiz do projeto continua funcionando.
E2E_NAVEGADOR escolhe o navegador: "chromium" (padrão, usado no CI) ou "msedge" (Edge instalado).
"""
import os

import pytest
from apoio import URL


def pytest_collection_modifyitems(items):
    if not URL:
        pular = pytest.mark.skip(reason="E2E_URL não definido: aplicação não está no ar")
        for item in items:
            item.add_marker(pular)


@pytest.fixture(scope="session")
def navegador():
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        nome = os.getenv("E2E_NAVEGADOR", "chromium")
        browser = p.chromium.launch(channel="msedge") if nome == "msedge" else p.chromium.launch()
        yield browser
        browser.close()


@pytest.fixture
def pagina(navegador):
    contexto = navegador.new_context(viewport={"width": 1366, "height": 860})
    page = contexto.new_page()
    page.on("dialog", lambda dialogo: dialogo.accept())
    page.goto(URL)
    yield page
    contexto.close()
