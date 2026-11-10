import pytest

import limites


@pytest.fixture
def limite_ligado():
    limites.limiter.enabled = True
    limites.limiter.reset()
    yield
    limites.limiter.reset()
    limites.limiter.enabled = False


def test_login_bloqueia_apos_cinco_tentativas_por_minuto(client_anonimo, limite_ligado):
    dados = {"username": "alguem", "password": "senha-qualquer"}
    respostas = [client_anonimo.post("/auth/login", data=dados).status_code for _ in range(6)]

    assert respostas[:5] == [401] * 5
    assert respostas[5] == 429


def test_resposta_429_explica_e_informa_quando_tentar_de_novo(client_anonimo, limite_ligado):
    for _ in range(5):
        client_anonimo.post("/auth/login", data={"username": "x", "password": "y"})
    resposta = client_anonimo.post("/auth/login", data={"username": "x", "password": "y"})

    assert resposta.status_code == 429
    assert "Aguarde" in resposta.json()["detail"]
    assert "Retry-After" in resposta.headers


def test_rotas_sem_limite_nao_sao_afetadas(client_anonimo, limite_ligado):
    assert all(client_anonimo.get("/health").status_code == 200 for _ in range(20))


def test_cors_libera_origem_configurada(client_anonimo):
    resposta = client_anonimo.options("/produtos/", headers={
        "Origin": "http://localhost:5173",
        "Access-Control-Request-Method": "POST",
    })
    assert resposta.headers.get("access-control-allow-origin") == "http://localhost:5173"


def test_cors_recusa_origem_desconhecida(client_anonimo):
    resposta = client_anonimo.options("/produtos/", headers={
        "Origin": "https://site-malicioso.example",
        "Access-Control-Request-Method": "POST",
    })
    assert "access-control-allow-origin" not in resposta.headers
