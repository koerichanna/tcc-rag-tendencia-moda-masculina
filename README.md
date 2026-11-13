# Moda Inteligente: RAG para o varejo de moda masculina

Projeto de Portfólio (Engenharia de Software, Católica SC), linha de Inteligência Artificial.
Autora: Anna Koerich.

## Objetivo

Ajudar pequenos lojistas de moda masculina a decidir o que comprar. O lojista faz uma pergunta
("vale a pena comprar calça skinny?"), o sistema busca as tendências mais parecidas numa base
vetorial, cruza com o estoque da loja e devolve uma recomendação com a justificativa e as fontes
usadas.

## Acesso para avaliação

| Ambiente | Endereço |
|---|---|
| Produção | https://tcc-moda-koerich.canadacentral.cloudapp.azure.com |
| Homologação | https://staging.52-139-37-198.sslip.io |

- **Usuário:** `avaliador.catolica`
- **Senha:** `adminadmin`

É uma conta de perfil `usuario`: acessa o painel, o consultor RAG, os produtos e as ações de IA,
mas não a gestão de usuários. Ela existe só para a avaliação e será desativada depois dela.

## Arquitetura

```mermaid
flowchart TD
    UI[Frontend React + Vite] <-->|HTTP / JSON| API[FastAPI]
    API <--> RAG[rag_engine.py]
    API <-->|SQLAlchemy| PG[(PostgreSQL)]
    RAG <-->|busca híbrida| CHROMA[(ChromaDB)]
    RAG -->|opcional| LLM[Gemini / OpenAI]
```

- **Frontend:** React 19, Vite, lucide-react.
- **Backend:** FastAPI, Python 3.11.
- **Banco relacional:** PostgreSQL 16 (`produtos`, `tendencias`, `recomendacoes`, `usuarios`).
- **Banco vetorial:** ChromaDB persistente, uma coleção por modelo de embedding.
- **Embedding:** `paraphrase-multilingual-MiniLM-L12-v2` em ONNX quantizado (`embeddings.py`), sem
  PyTorch. A busca é híbrida: vetorial + BM25 combinados por Reciprocal Rank Fusion (`busca.py`).
- **LLM:** Gemini (ou OpenAI) via LangChain. Sem chave configurada, ou se a API falhar, a
  resposta é montada por regras locais em `sintetizar_resposta_contextual`.

Documentação completa (C4, DER, decisões) em [docs/WIKI_ARQUITETURA.md](docs/WIKI_ARQUITETURA.md).
Avaliação da recuperação e das respostas em [docs/avaliacao_rag.md](docs/avaliacao_rag.md).
Limitações conhecidas e como foram tratadas em [docs/limitacoes.md](docs/limitacoes.md).

## Estrutura

```
.github/workflows/     ci.yml (lint, testes, Sonar, imagens, deploy), rollback.yml e
                       atualizar-trends.yml (coleta semanal do Google Trends)
data/                  base de tendências e coletas do Google Trends (ver data/README.md)
pipeline/              coleta e pré-processamento dos dados do Google Trends
deploy/                script executado na VM e modelos de .env
docs/                  arquitetura, ADRs, LGPD
frontend/              aplicação React (servida por Nginx em produção)
infra/caddy/           proxy reverso com HTTPS
infra/monitoramento/   Prometheus, Grafana e alertas (ver docs/observabilidade.md)
tests/                 testes da API, do RAG e da busca vetorial
e2e/                   testes de interface com Playwright (rodam no CI)
avaliacao/             conjunto de perguntas e scripts de avaliação do RAG
main.py                rotas da API
rag_engine.py          recuperação + síntese da recomendação
coerencia.py           garante que a resposta do LLM respeite o risco calculado
vector_db.py / busca.py  busca híbrida no ChromaDB (vetorial + BM25)
embeddings.py          modelos de embedding (multilíngue em ONNX)
vinculo.py             vincula cada produto à tendência mais parecida
ingestion.py           indexa data/market_trends.json no ChromaDB e no PostgreSQL
models.py / schemas.py modelos SQLAlchemy e schemas Pydantic
docker-compose.yml     ambiente local
docker-compose.prod.yml  produção e homologação (imagens do GHCR)
```

## Rodando localmente

Pré-requisitos: Python 3.11+, Node 20+, PostgreSQL (local ou via Docker).

```bash
cp .env.example .env            # ajustar DATABASE_URL e a chave do Gemini

python -m venv venv
venv\Scripts\pip install -r requirements.txt
venv\Scripts\python ingestion.py           # aplica as migrations e indexa a base de tendências
venv\Scripts\uvicorn main:app --reload --port 8000

cd frontend
npm install
npm run dev                                 # http://localhost:5173
```

Ou tudo com Docker: `docker compose up --build` (frontend em http://localhost:8080, API em
http://localhost:8000/docs). Na primeira vez, rodar `docker compose exec backend python ingestion.py`.

## Login e usuários

Toda a aplicação exige login: sem ele só aparece a tela de entrada. A API responde 401 em todas as
rotas de dados; ficam abertas apenas `/`, `/health` (healthcheck) e `/auth/login`. O token JWT vale
por 8 horas e fica na `sessionStorage` (some ao fechar a aba).

Há dois perfis:

| Perfil | Pode |
|---|---|
| `usuario` | usar o painel, o consultor RAG, cadastrar produtos e as ações de IA; trocar a própria senha |
| `admin` | tudo acima e gerenciar usuários na aba **Usuários** |

Na aba **Usuários** o administrador cadastra logins, troca o perfil, desativa ou reativa contas,
redefine senhas e exclui usuários. Desativar corta o acesso na hora, até de quem já está logado,
porque a API confere o usuário no banco a cada requisição. O administrador não pode rebaixar,
desativar nem excluir a própria conta, então sempre sobra pelo menos um admin ativo. Nomes de
usuário são gravados em minúsculas; senhas têm de 10 a 72 caracteres e são salvas com bcrypt.

O primeiro administrador é criado pelo terminal (o mesmo comando recupera o acesso se a senha for
esquecida: redefine a senha, promove a admin e reativa a conta):

```bash
venv\Scripts\python criar_usuario.py anna --admin              # pede a senha
# na VM (sem -e SENHA_USUARIO o comando pede a senha; use -it nesse caso):
docker exec -e SENHA_USUARIO='...' moda-production-backend-1 python criar_usuario.py anna --admin
```

Em produção a API não sobe sem `JWT_SECRET` definido.

## Migrations (Alembic)

O schema do banco é versionado em `migrations/versions/`. A API aplica as migrations pendentes ao
subir (`migrar.py`, chamado pelo Dockerfile); localmente, rode `venv\Scripts\python migrar.py`.

Para mudar um model:

```bash
# 1. alterar models.py
# 2. gerar a migration comparando models e banco
venv\Scripts\alembic revision --autogenerate -m "descricao da mudanca"
# 3. revisar o arquivo gerado em migrations/versions/ e aplicar
venv\Scripts\alembic upgrade head
```

Desfazer a última: `venv\Scripts\alembic downgrade -1`. O teste `tests/test_migrations.py` falha se
um model for alterado sem a migration correspondente.

## Testes

```bash
venv\Scripts\python -m pytest tests/ -v --cov=.
venv\Scripts\python -m ruff check .
```

Os testes usam um banco separado (`moda_test`, criado automaticamente no mesmo servidor do
`DATABASE_URL`) para não apagar os dados de desenvolvimento. `tests/test_rag_evaluation.py` roda as
105 perguntas de `avaliacao/perguntas.json` na busca da API e falha se a recuperação piorar.

Testes de interface (precisam da API e do frontend no ar; no CI rodam no job `e2e`):

```bash
pip install -r e2e/requirements.txt && python -m playwright install chromium
E2E_URL=http://localhost:5173 E2E_ADMIN=<admin> E2E_SENHA=<senha> pytest e2e/
```

## Como a recomendação é montada

1. A busca híbrida devolve as 3 tendências mais parecidas com a pergunta (opcionalmente
   filtradas por categoria). O vetor de cada tendência vem só da descrição da peça; o texto
   entregue ao LLM traz também risco, score e números do Google Trends.
2. Se um produto foi selecionado, o estoque dele é lido do PostgreSQL e a tendência vinculada ao
   produto passa a ser a primeira da lista.
3. Documentos + estoque + o risco calculado da primeira tendência vão para o LLM, com instrução de
   responder em JSON (`diagnostico`, `acao_recomendada`, `nivel_risco`, `justificativa_explicavel`,
   `fontes_consultadas`) com uma ação compatível com o risco.
4. `coerencia.py` confere a resposta: se o LLM trocou o risco ou recomendou algo contraditório
   (comprar com risco Alto, liquidar com risco Baixo), o sistema corrige e avisa na justificativa.
5. Se o LLM não responder, as regras locais decidem a ação a partir do score e do risco da
   tendência e da situação do estoque.
6. A recomendação é gravada na tabela `recomendacoes`.

O `tendencia_score` de cada produto não é digitado: `vinculo.py` liga o produto à tendência mais
parecida da mesma categoria e copia o score dela. O vínculo é refeito a cada ingestão.

## Deploy

Azure VM com Docker Compose, imagens publicadas no GitHub Container Registry e deploy pelo
GitHub Actions via `az vm run-command` (sem SSH). `main` vai para produção e `develop` para
homologação. Detalhes em [docs/adr-001-hospedagem-nuvem.md](docs/adr-001-hospedagem-nuvem.md).
