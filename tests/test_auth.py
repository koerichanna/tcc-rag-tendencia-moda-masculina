import datetime

import jwt
import pytest

import auth
from criar_usuario import salvar_usuario

SENHA = "senha-de-teste-123"


@pytest.fixture
def usuario(db_session):
    salvar_usuario("anna", SENHA)
    return "anna"


def login(cliente, nome, senha):
    return cliente.post("/auth/login", data={"username": nome, "password": senha})


def test_login_devolve_token(client_anonimo, usuario):
    resposta = login(client_anonimo, usuario, SENHA)
    assert resposta.status_code == 200
    assert resposta.json()["token_type"] == "bearer"


@pytest.mark.parametrize("nome,senha", [("anna", "senha-errada-999"), ("ninguem", SENHA)])
def test_login_invalido_usa_a_mesma_mensagem(client_anonimo, usuario, nome, senha):
    resposta = login(client_anonimo, nome, senha)
    assert resposta.status_code == 401
    assert resposta.json()["detail"] == "Usuário ou senha inválidos"


def test_senha_fica_salva_como_hash(db_session, usuario):
    import models
    registro = db_session.query(models.UsuarioModel).filter_by(nome_usuario=usuario).one()
    assert registro.senha_hash != SENHA
    assert registro.senha_hash.startswith("$2b$")


@pytest.mark.parametrize("metodo,rota", [
    ("post", "/produtos/"),
    ("put", "/produtos/1"),
    ("delete", "/produtos/1"),
    ("post", "/tendencias/"),
    ("post", "/recomendacoes/"),
    ("post", "/ia/gerar-tendencias"),
    ("post", "/ia/analisar-produto/1"),
])
def test_rotas_que_alteram_dados_exigem_login(client_anonimo, metodo, rota):
    resposta = getattr(client_anonimo, metodo)(rota)
    assert resposta.status_code == 401


def test_consultas_continuam_publicas(client_anonimo):
    for rota in ["/", "/health", "/produtos/", "/tendencias/", "/recomendacoes/", "/dashboard/kpis"]:
        assert client_anonimo.get(rota).status_code == 200


def test_token_permite_acessar_rota_protegida(client_anonimo, usuario):
    token = login(client_anonimo, usuario, SENHA).json()["access_token"]
    cabecalho = {"Authorization": f"Bearer {token}"}

    assert client_anonimo.get("/auth/me", headers=cabecalho).json() == {"nome_usuario": "anna"}
    produto = {"nome": "Camisa", "categoria": "Camisas", "preco_medio": 100}
    assert client_anonimo.post("/produtos/", json=produto, headers=cabecalho).status_code == 201


def test_token_expirado_e_recusado(client_anonimo, usuario):
    vencido = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=1)
    token = jwt.encode({"sub": usuario, "exp": vencido}, auth.SEGREDO, algorithm=auth.ALGORITMO)
    resposta = client_anonimo.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resposta.status_code == 401
    assert "expirada" in resposta.json()["detail"]


def test_token_com_assinatura_falsa_e_recusado(client_anonimo, usuario):
    token = jwt.encode({"sub": usuario}, "outro-segredo", algorithm=auth.ALGORITMO)
    resposta = client_anonimo.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resposta.status_code == 401


def test_senha_curta_e_recusada(db_session):
    with pytest.raises(ValueError):
        salvar_usuario("anna", "curta")


def desativar(db_session, nome):
    import models
    db_session.query(models.UsuarioModel).filter_by(nome_usuario=nome).update({"ativo": False})
    db_session.commit()


def test_usuario_inativo_nao_consegue_entrar(client_anonimo, db_session, usuario):
    desativar(db_session, usuario)
    resposta = login(client_anonimo, usuario, SENHA)
    assert resposta.status_code == 401
    assert resposta.json()["detail"] == "Usuário ou senha inválidos"


def test_desativar_usuario_derruba_token_ja_emitido(client_anonimo, db_session, usuario):
    token = login(client_anonimo, usuario, SENHA).json()["access_token"]
    desativar(db_session, usuario)
    resposta = client_anonimo.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resposta.status_code == 401


def test_usuario_novo_nasce_com_perfil_comum(db_session):
    import models
    salvar_usuario("joao", SENHA)
    assert db_session.query(models.UsuarioModel).filter_by(nome_usuario="joao").one().perfil == "usuario"


def test_opcao_admin_promove_e_reativa(db_session, usuario):
    import models
    desativar(db_session, usuario)
    salvar_usuario(usuario, SENHA, admin=True)
    db_session.expire_all()
    registro = db_session.query(models.UsuarioModel).filter_by(nome_usuario=usuario).one()
    assert (registro.perfil, registro.ativo) == ("admin", True)


def test_salvar_usuario_existente_troca_a_senha(client_anonimo, usuario):
    assert salvar_usuario(usuario, "nova-senha-segura-1") is False
    assert login(client_anonimo, usuario, SENHA).status_code == 401
    assert login(client_anonimo, usuario, "nova-senha-segura-1").status_code == 200
