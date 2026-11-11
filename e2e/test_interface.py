import uuid

from apoio import ADMIN, SENHA_ADMIN, entrar, sair
from playwright.sync_api import expect


def nome_unico(prefixo):
    # Os testes rodam contra um banco que persiste entre execuções locais: nomes únicos evitam conflito.
    return f"{prefixo}.{uuid.uuid4().hex[:6]}"


def test_sem_login_so_aparece_a_tela_de_entrada(pagina):
    expect(pagina.get_by_role("heading", name="Moda Inteligente")).to_be_visible()
    expect(pagina.get_by_role("tab")).to_have_count(0)


def test_senha_errada_mostra_erro(pagina):
    entrar(pagina, ADMIN, "senha-errada-123")
    expect(pagina.get_by_role("alert")).to_contain_text("inválidos")


def test_admin_cadastra_usuario_que_entra_sem_aba_de_gestao(pagina):
    entrar(pagina, ADMIN, SENHA_ADMIN)
    pagina.get_by_role("tab", name="Usuários").click()
    expect(pagina.get_by_role("row", name=f"{ADMIN} (você)").get_by_role("button", name="Desativar")).to_be_disabled()

    nome = nome_unico("vendedor")
    pagina.get_by_label("Usuário", exact=True).fill(nome)
    pagina.get_by_label("Senha inicial").fill("senha-vendedor-1")
    pagina.get_by_role("button", name="Cadastrar").click()
    expect(pagina.get_by_role("row", name=nome)).to_contain_text("Ativo")

    sair(pagina)
    entrar(pagina, nome, "senha-vendedor-1")
    expect(pagina.get_by_role("tab", name="Visão Geral")).to_be_visible()
    expect(pagina.get_by_role("tab", name="Usuários")).to_have_count(0)


def test_usuario_desativado_nao_entra(pagina):
    entrar(pagina, ADMIN, SENHA_ADMIN)
    pagina.get_by_role("tab", name="Usuários").click()
    nome = nome_unico("temporario")
    pagina.get_by_label("Usuário", exact=True).fill(nome)
    pagina.get_by_label("Senha inicial").fill("senha-temporaria-1")
    pagina.get_by_role("button", name="Cadastrar").click()
    pagina.get_by_role("row", name=nome).get_by_role("button", name="Desativar").click()
    expect(pagina.get_by_role("row", name=nome)).to_contain_text("Inativo")

    sair(pagina)
    entrar(pagina, nome, "senha-temporaria-1")
    expect(pagina.get_by_role("alert")).to_contain_text("inválidos")


def test_produto_novo_mostra_tendencia_vinculada(pagina):
    entrar(pagina, ADMIN, SENHA_ADMIN)
    pagina.get_by_role("tab", name="Estoque").click()
    pagina.get_by_role("button", name="Novo Produto").click()
    nome = f"Calça Wide Leg Teste {uuid.uuid4().hex[:4]}"
    pagina.get_by_label("Nome do Produto:").fill(nome)
    pagina.get_by_label("Categoria:").select_option("Calças")
    pagina.get_by_label("Preço de Venda (R$):").fill("199.90")
    pagina.get_by_label("Estoque Atual:").fill("4")
    pagina.get_by_role("button", name="Salvar Produto").click()

    # o primeiro vínculo carrega o modelo de embedding na API, então pode demorar alguns segundos
    linha = pagina.get_by_role("row", name=nome)
    expect(linha).to_contain_text("Wide Leg", timeout=30_000)  # tendência vinculada pela busca, não digitada
    expect(linha).to_contain_text("Crítico")


def test_consultor_rag_responde_com_risco_e_justificativa(pagina):
    entrar(pagina, ADMIN, SENHA_ADMIN)
    pagina.get_by_role("tab", name="Consultor RAG").click()
    pagina.get_by_label("Sua Dúvida de Compra ou Tendência:").fill("Ainda compensa comprar calça jeans skinny?")
    pagina.get_by_role("button", name="Analisar Decisão com IA").click()
    expect(pagina.get_by_text("Ação Recomendada pela IA ao Lojista")).to_be_visible(timeout=60_000)
    expect(pagina.get_by_text("Risco:").first).to_be_visible()


def test_sessao_continua_apos_recarregar(pagina):
    entrar(pagina, ADMIN, SENHA_ADMIN)
    expect(pagina.get_by_role("tab", name="Visão Geral")).to_be_visible()
    pagina.reload()
    expect(pagina.get_by_role("tab", name="Visão Geral")).to_be_visible()
