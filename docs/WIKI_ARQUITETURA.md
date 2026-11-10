# Arquitetura do Projeto Moda

**Projeto:** Sistema RAG para Apoio à Tomada de Decisão no Varejo de Moda Masculina  
**Autora:** Anna Koerich  
**Instituição:** Centro Universitário Católica de Santa Catarina (Católica SC)  
**Linha de Projeto:** Inteligência Artificial (IA)  
**Semestre:** 2026/2 — 8º Período  

---

## 1. Visão Geral do Sistema

Pequenas lojas de moda masculina costumam comprar "no feeling" e acabam com estoque parado. O Projeto Moda usa **RAG (Retrieval-Augmented Generation)**: busca as tendências de mercado mais parecidas com a pergunta do lojista, cruza com o estoque da loja e devolve uma recomendação com justificativa e fontes.

---

## 2. Modelo C4 de Arquitetura

### 2.1 Nível 1: Diagrama de Contexto
Apresenta os usuários do sistema, os limites da solução e suas integrações com o mundo externo.

```mermaid
flowchart TD
    User["Lojista / Gestor de Compras<br/>(Pequeno Varejista de Moda Masculina)"]
    System["Sistema RAG Moda Masculina<br/>[Software System]<br/>Plataforma inteligente de análise de tendências e recomendação de compras"]
    Gemini["Google Gemini AI API<br/>[External System]<br/>Modelos LLM para síntese explicável e briefing executivo"]
    MarketData["Bases de Mercado & Redes<br/>[External Data Source]<br/>WGSN, Pitti Uomo, TikTok Trends, Google Trends"]

    User -->|"Consulta tendências, analisa estoque e solicita recomendações"| System
    System -->|"Envia contexto de mercado e prompt estruturado"| Gemini
    Gemini -->|"Retorna diagnóstico mercadológico em formato JSON"| System
    MarketData -.->|"Relatórios e evidências para indexação vetorial"| System
```

---

### 2.2 Nível 2: Diagrama de Containers
Decompõe o sistema em suas unidades de execução e armazenamento independentes.

```mermaid
flowchart TD
    subgraph ClientApp ["Navegador do Lojista"]
        SPA["Frontend SPA<br/>[React 19 + Vite + Nginx]<br/>Interface de usuário com dashboard de KPIs, assistente RAG e controle de estoque"]
    end

    subgraph CloudServer ["Servidor de Aplicação (Docker / Nuvem)"]
        API["Backend REST API<br/>[FastAPI / Python 3.11]<br/>Rotas CRUD, medição de latência e chamada ao motor RAG"]
        RAGCore["Motor RAG & Explicabilidade<br/>[LangChain Core]<br/>Recuperador de similaridade, cruzamento de regras de estoque e sintetizador de resposta"]
    end

    subgraph DataStorage ["Camada de Dados Persistentes"]
        Postgres[("PostgreSQL 16<br/>[Banco Relacional]<br/>Armazena produtos, categorias, níveis de estoque e histórico de recomendações")]
        Chroma[("ChromaDB Persistente<br/>[Banco Vetorial]<br/>Coleção 'tendencias_moda' com embeddings semânticos e metadados de mercado")]
    end

    SPA -->|"Requisições HTTP / JSON (Porta 8000)"| API
    API -->|"Invoca pipeline de recuperação e síntese"| RAGCore
    API -->|"Consultas e persistência via SQLAlchemy ORM"| Postgres
    RAGCore -->|"Busca por similaridade semântica (Top-K)"| Chroma
    RAGCore -->|"Recupera dados de estoque do produto alvo"| Postgres
```

---

### 2.3 Nível 3: Diagrama de Componentes (Backend FastAPI)
Detalha a organização interna dos módulos da API.

```mermaid
flowchart LR
    Router["main.py<br/>(Rotas REST, CORS & Middleware de Latência)"]
    DBLayer["database.py & models.py<br/>(Mapeamento Objeto-Relacional SQLAlchemy)"]
    Schemas["schemas.py<br/>(Validação Pydantic v2 dos contratos JSON)"]
    RAGEngine["rag_engine.py<br/>(Orquestrador RAG, Fallback Heurístico e Integração LLM)"]
    VectorDB["vector_db.py<br/>(Cliente ChromaDB e busca por similaridade)"]

    Router --> Schemas
    Router --> DBLayer
    Router --> RAGEngine
    RAGEngine --> VectorDB
    RAGEngine --> DBLayer
```

---

## 3. Modelo de Dados Relacional (DER)

```mermaid
erDiagram
    PRODUTOS ||--o{ RECOMENDACOES : "gera"
    
    PRODUTOS {
        int id PK
        string nome
        string categoria
        float preco_medio
        float custo_aquisicao
        int quantidade_estoque
        int estoque_minimo
        float tendencia_score
        datetime data_atualizacao
    }

    TENDENCIAS {
        int id PK
        string termo
        string categoria
        float score_relevancia
        string sazonalidade
        string nivel_risco
        text descricao
        string fonte
        datetime data_registro
    }

    RECOMENDACOES {
        int id PK
        int produto_id FK
        string titulo
        string categoria
        string acao_sugerida
        text justificativa
        string nivel_prioridade
        datetime data_criacao
    }
```

---

## 4. Pipeline de Inteligência Artificial & RAG

```mermaid
sequenceDiagram
    autonumber
    actor Lojista
    participant UI as Frontend React
    participant API as FastAPI REST
    participant Chroma as ChromaDB Vetorial
    participant PG as PostgreSQL
    participant LLM as Google Gemini / Heurística

    Lojista->>UI: Digita dúvida (ex.: "Vale a pena comprar camisas de linho?")
    UI->>API: POST /rag/consultar { pergunta, produto_id }
    API->>Chroma: buscar_tendencias_similares(query, n_results=3)
    Chroma-->>API: Retorna top-3 documentos com metadados (score, fonte, sazonalidade)
    opt Produto informado
        API->>PG: Consulta estoque atual vs. estoque mínimo do produto
        PG-->>API: Retorna dados estruturados de estoque
    end
    API->>LLM: Injeta documentos recuperados + estoque + prompt explicável
    LLM-->>API: Retorna diagnóstico, ação recomendada, nível de risco e justificativa
    API->>PG: Salva registro na tabela 'recomendacoes'
    API-->>UI: Retorna JSON estruturado e cabeçalho X-Response-Time-Ms
    UI-->>Lojista: Exibe cards visuais com cores de risco e justificativa fundamentada
```

---

## 5. Núcleo Comum de Engenharia

Requisitos do [Portfólio Directions](https://github.com/CatolicaSC-Portfolio/The-Portfolio-Playbook/blob/main/directions/portfolio-directions-GERAL.md):

| Requisito | Como está no projeto |
| :--- | :--- |
| Wiki | Este conteúdo, publicado na Wiki do GitHub do repositório. |
| CI/CD | `.github/workflows/ci.yml`: Ruff, Pytest (com PostgreSQL), lint/build do frontend, SonarCloud, imagens no GHCR e deploy na Azure. |
| Análise estática e segurança | Ruff e Oxlint no pipeline; SonarCloud (`sonar-project.properties`). |
| Observabilidade | Prometheus coleta `/metrics` das duas APIs (requisições, latência, erros, chamadas e latência do LLM, origem das respostas do RAG); Grafana com painel e alertas. Ver [observabilidade](observabilidade.md). |
| Ambientes | Desenvolvimento local (`docker-compose.yml`), homologação (`develop`) e produção (`main`) na VM, ver [ADR 001](adr-001-hospedagem-nuvem.md). |

---

## 6. Execução

Ver [README](../README.md#rodando-localmente) para rodar localmente e o
[ADR 001](adr-001-hospedagem-nuvem.md) para o deploy.
