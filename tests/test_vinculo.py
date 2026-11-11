import pytest

import models
import vinculo
from ingestion import carregar_dados_mercado

BASE = {t["id"]: t for t in carregar_dados_mercado()}


def criar(client, nome, categoria, **extra):
    resposta = client.post("/produtos/", json={"nome": nome, "categoria": categoria, "preco_medio": 150, **extra})
    assert resposta.status_code == 201
    return resposta.json()


@pytest.mark.parametrize("nome,categoria,aceitos", [
    ("Calça Jeans Skinny Preta", "Calças", {"trend_skinny_queda_03"}),
    ("Calça Wide Leg Alfaiataria", "Calças", {"trend_wide_leg_02"}),
    ("Camisa de Linho Manga Curta", "Camisas", {"trend_linho_01"}),
    # jaqueta e colete puffer são peças acolchoadas parecidas; as duas tendências servem
    ("Jaqueta Puffer Acolchoada Preta", "Jaquetas", {"trend_puffer_46", "trend_colete_puffer_49"}),
    ("Tênis de Corrida com Amortecimento", "Calçados", {"trend_corrida_34"}),
])
def test_produto_novo_e_vinculado_a_tendencia_parecida(client, nome, categoria, aceitos):
    produto = criar(client, nome, categoria)
    assert produto["tendencia_codigo"] in aceitos
    # o score digitado é ignorado: vale o score calculado do Google Trends
    assert produto["tendencia_score"] == BASE[produto["tendencia_codigo"]]["score_relevancia"]


def test_score_informado_no_cadastro_e_substituido(client):
    produto = criar(client, "Calça Jeans Skinny Azul", "Calças", tendencia_score=99)
    assert produto["tendencia_score"] == BASE["trend_skinny_queda_03"]["score_relevancia"]


def test_vinculo_respeita_a_categoria(client):
    produto = criar(client, "Linho", "Calças")  # termo de camisa, mas cadastrado como calça
    assert BASE[produto["tendencia_codigo"]]["categoria"] == "Calças"


def test_mudar_nome_refaz_o_vinculo(client):
    produto = criar(client, "Calça Jeans Skinny", "Calças")
    resposta = client.put(f"/produtos/{produto['id']}", json={"nome": "Calça Cargo com Bolsos Laterais"})
    assert resposta.json()["tendencia_codigo"] == "trend_cargo_18"


def test_base_vetorial_fora_do_ar_nao_impede_cadastro(client, monkeypatch):
    def falha(*_):
        raise ConnectionError("chroma indisponível")
    monkeypatch.setattr(vinculo, "tendencia_mais_proxima", falha)
    produto = criar(client, "Calça Qualquer", "Calças", tendencia_score=42)
    assert produto["tendencia_codigo"] is None
    assert produto["tendencia_score"] == 42


def test_revincular_todos_atualiza_produtos_existentes(db_session):
    produto = models.ProdutoModel(nome="Bermuda Jeans Clara", categoria="Bermudas", preco_medio=99, tendencia_score=0)
    db_session.add(produto)
    db_session.commit()

    assert vinculo.revincular_todos(db_session, models.ProdutoModel) == 1
    db_session.refresh(produto)
    assert produto.tendencia_codigo == "trend_bermuda_jeans_40"
