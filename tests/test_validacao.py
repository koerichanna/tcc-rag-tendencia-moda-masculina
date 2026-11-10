import pytest

PRODUTO_VALIDO = {
    "nome": "Camisa Linho",
    "categoria": "Camisas",
    "preco_medio": 189.9,
    "quantidade_estoque": 10,
    "estoque_minimo": 5,
}


def campos_com_erro(resposta):
    return {erro["loc"][-1] for erro in resposta.json()["detail"]}


@pytest.mark.parametrize("campo,valor", [
    ("categoria", "Sapatos"),
    ("preco_medio", -1),
    ("quantidade_estoque", -5),
    ("tendencia_score", 150),
    ("nome", " "),
])
def test_criar_produto_rejeita_valor_invalido(client, campo, valor):
    resposta = client.post("/produtos/", json={**PRODUTO_VALIDO, campo: valor})
    assert resposta.status_code == 422
    assert campo in campos_com_erro(resposta)


def test_criar_produto_remove_espacos_do_nome(client):
    resposta = client.post("/produtos/", json={**PRODUTO_VALIDO, "nome": "  Camisa Linho  "})
    assert resposta.status_code == 201
    assert resposta.json()["nome"] == "Camisa Linho"


def test_atualizar_produto_nao_aceita_estoque_negativo(client):
    produto_id = client.post("/produtos/", json=PRODUTO_VALIDO).json()["id"]
    resposta = client.put(f"/produtos/{produto_id}", json={"quantidade_estoque": -1})
    assert resposta.status_code == 422


def test_cadastrar_tendencia_valida_risco(client):
    resposta = client.post("/tendencias/", json={"termo": "Calça Teste", "categoria": "Calças",
                                                 "nivel_risco": "Altíssimo"})
    assert resposta.status_code == 422
    assert "nivel_risco" in campos_com_erro(resposta)


@pytest.mark.parametrize("pergunta", ["oi", "x" * 501])
def test_consulta_rag_limita_tamanho_da_pergunta(client, pergunta):
    resposta = client.post("/rag/consultar", json={"pergunta": pergunta})
    assert resposta.status_code == 422
