def test_endpoint_raiz(client):
    response = client.get("/")
    assert response.status_code == 200
    dados = response.json()
    assert dados["status"] == "online"
    assert "versao" in dados


def test_endpoint_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    dados = response.json()
    assert dados["status"] == "healthy"
    assert "timestamp" in dados
    assert "X-Response-Time-Ms" in response.headers


def test_crud_produtos(client):
    novo = {
        "nome": "Camisa Linho Off-White",
        "categoria": "Camisas",
        "preco_medio": 189.90,
        "custo_aquisicao": 85.00,
        "quantidade_estoque": 12,
        "estoque_minimo": 5,
        "tendencia_score": 92.0
    }
    res_criar = client.post("/produtos/", json=novo)
    assert res_criar.status_code == 201
    prod_criado = res_criar.json()
    assert prod_criado["id"] is not None
    assert prod_criado["nome"] == novo["nome"]
    prod_id = prod_criado["id"]

    res_listar = client.get("/produtos/")
    assert res_listar.status_code == 200
    lista = res_listar.json()
    assert len(lista) == 1

    res_obter = client.get(f"/produtos/{prod_id}")
    assert res_obter.status_code == 200
    assert res_obter.json()["nome"] == novo["nome"]

    res_atualizar = client.put(f"/produtos/{prod_id}", json={"quantidade_estoque": 20})
    assert res_atualizar.status_code == 200
    assert res_atualizar.json()["quantidade_estoque"] == 20

    res_deletar = client.delete(f"/produtos/{prod_id}")
    assert res_deletar.status_code == 200

    res_busca_deletado = client.get(f"/produtos/{prod_id}")
    assert res_busca_deletado.status_code == 404


def test_dashboard_kpis(client):
    client.post("/produtos/", json={
        "nome": "Calça Jeans Slim",
        "categoria": "Calças",
        "preco_medio": 220.0,
        "custo_aquisicao": 95.0,
        "quantidade_estoque": 2,
        "estoque_minimo": 5,
        "tendencia_score": 70.0
    })

    res = client.get("/dashboard/kpis")
    assert res.status_code == 200
    kpis = res.json()
    assert kpis["total_produtos"] == 1
    assert kpis["produtos_estoque_critico"] == 1
    assert "distribuicao_risco" in kpis


def test_listar_recomendacoes_mais_recentes_primeiro(client):
    for titulo in ["Primeira", "Segunda"]:
        client.post("/recomendacoes/", json={"titulo": titulo, "categoria": "Camisas",
                                             "acao_sugerida": "Manter", "justificativa": "Teste"})
    res = client.get("/recomendacoes/")
    assert res.status_code == 200
    assert [r["titulo"] for r in res.json()] == ["Segunda", "Primeira"]
