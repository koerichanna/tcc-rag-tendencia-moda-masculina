import pytest

import models
from criar_usuario import salvar_usuario

SENHA = "senha-de-teste-123"


def entrar(cliente, nome, senha=SENHA):
    token = cliente.post("/auth/login", data={"username": nome, "password": senha}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin(client_anonimo):
    salvar_usuario("anna", SENHA, admin=True)
    return entrar(client_anonimo, "anna")


@pytest.fixture
def comum(client_anonimo):
    salvar_usuario("joao", SENHA)
    return entrar(client_anonimo, "joao")


def id_de(db_session, nome):
    return db_session.query(models.UsuarioModel).filter_by(nome_usuario=nome).one().id


def test_admin_cadastra_e_lista_usuarios(client_anonimo, admin):
    resposta = client_anonimo.post("/usuarios/", headers=admin,
                                   json={"nome_usuario": "Maria.Silva", "senha": "outra-senha-456"})
    assert resposta.status_code == 201
    criado = resposta.json()
    # nome normalizado para minúsculas, perfil comum e ativo por padrão; a senha nunca volta na resposta
    assert (criado["nome_usuario"], criado["perfil"], criado["ativo"]) == ("maria.silva", "usuario", True)
    assert "senha" not in criado and "senha_hash" not in criado

    nomes = [u["nome_usuario"] for u in client_anonimo.get("/usuarios/", headers=admin).json()]
    assert nomes == ["anna", "maria.silva"]
    # o login aceita o nome do jeito que a pessoa digitar
    assert entrar(client_anonimo, "Maria.Silva", "outra-senha-456")


def test_usuario_cadastrado_consegue_entrar(client_anonimo, admin):
    client_anonimo.post("/usuarios/", headers=admin, json={"nome_usuario": "maria", "senha": "outra-senha-456"})
    assert client_anonimo.get("/auth/me", headers=entrar(client_anonimo, "maria", "outra-senha-456")).status_code == 200


def test_nome_repetido_e_recusado(client_anonimo, admin):
    resposta = client_anonimo.post("/usuarios/", headers=admin, json={"nome_usuario": "anna", "senha": SENHA})
    assert resposta.status_code == 409


@pytest.mark.parametrize("dados", [
    {"nome_usuario": "maria", "senha": "curta"},
    {"nome_usuario": "ma", "senha": SENHA},
    {"nome_usuario": "maria silva", "senha": SENHA},
    {"nome_usuario": "maria", "senha": SENHA, "perfil": "dono"},
    {"nome_usuario": "maria", "senha": "ç" * 40},  # 40 caracteres, mas 80 bytes
])
def test_cadastro_invalido_e_recusado(client_anonimo, admin, dados):
    assert client_anonimo.post("/usuarios/", headers=admin, json=dados).status_code == 422


@pytest.mark.parametrize("metodo,rota", [
    ("get", "/usuarios/"),
    ("post", "/usuarios/"),
    ("put", "/usuarios/1"),
    ("delete", "/usuarios/1"),
])
def test_usuario_comum_nao_gerencia_usuarios(client_anonimo, comum, metodo, rota):
    assert getattr(client_anonimo, metodo)(rota, headers=comum).status_code == 403


def test_sem_login_nao_gerencia_usuarios(client_anonimo):
    assert client_anonimo.get("/usuarios/").status_code == 401


def test_admin_desativa_e_reativa_usuario(client_anonimo, db_session, admin, comum):
    alvo = id_de(db_session, "joao")

    assert client_anonimo.put(f"/usuarios/{alvo}", headers=admin, json={"ativo": False}).json()["ativo"] is False
    assert client_anonimo.get("/auth/me", headers=comum).status_code == 401

    client_anonimo.put(f"/usuarios/{alvo}", headers=admin, json={"ativo": True})
    assert client_anonimo.get("/auth/me", headers=comum).status_code == 200


def test_admin_promove_usuario(client_anonimo, db_session, admin, comum):
    alvo = id_de(db_session, "joao")
    client_anonimo.put(f"/usuarios/{alvo}", headers=admin, json={"perfil": "admin"})
    assert client_anonimo.get("/usuarios/", headers=comum).status_code == 200


def test_admin_redefine_senha_de_outro_usuario(client_anonimo, db_session, admin, comum):
    alvo = id_de(db_session, "joao")
    client_anonimo.put(f"/usuarios/{alvo}", headers=admin, json={"senha": "senha-redefinida-1"})
    login = client_anonimo.post("/auth/login", data={"username": "joao", "password": "senha-redefinida-1"})
    assert login.status_code == 200


def test_admin_exclui_usuario(client_anonimo, db_session, admin, comum):
    alvo = id_de(db_session, "joao")
    assert client_anonimo.delete(f"/usuarios/{alvo}", headers=admin).status_code == 200
    assert client_anonimo.delete(f"/usuarios/{alvo}", headers=admin).status_code == 404


@pytest.mark.parametrize("metodo,corpo", [
    ("put", {"ativo": False}),
    ("put", {"perfil": "usuario"}),
    ("delete", None),
])
def test_admin_nao_se_bloqueia(client_anonimo, db_session, admin, metodo, corpo):
    proprio = id_de(db_session, "anna")
    opcoes = {"json": corpo} if corpo else {}
    resposta = getattr(client_anonimo, metodo)(f"/usuarios/{proprio}", headers=admin, **opcoes)
    assert resposta.status_code == 400
    assert "própria conta" in resposta.json()["detail"]


def test_usuario_troca_a_propria_senha(client_anonimo, comum):
    resposta = client_anonimo.put("/auth/me/senha", headers=comum,
                                  json={"senha_atual": SENHA, "nova_senha": "minha-nova-senha-9"})
    assert resposta.status_code == 200
    login = client_anonimo.post("/auth/login", data={"username": "joao", "password": "minha-nova-senha-9"})
    assert login.status_code == 200


def test_troca_de_senha_exige_a_senha_atual(client_anonimo, comum):
    resposta = client_anonimo.put("/auth/me/senha", headers=comum,
                                  json={"senha_atual": "errada", "nova_senha": "minha-nova-senha-9"})
    assert resposta.status_code == 400
