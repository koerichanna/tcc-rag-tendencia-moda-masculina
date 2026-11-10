# Base de tendências

`market_trends.json` é a base de conhecimento indexada no ChromaDB e sincronizada com a tabela
`tendencias`. Cada registro junta duas coisas de origens diferentes:

| Parte | Origem | Campos |
|---|---|---|
| Métricas de interesse | **Dados reais** do Google Trends (Brasil) | `score_relevancia`, `nivel_risco`, `sazonalidade`, `metricas` |
| Descrição do produto | **Texto sintético** escrito pela autora | `termo`, `categoria`, `estilo`, `conteudo` |

## Dados reais: Google Trends

- **O que é:** interesse de busca semanal no Google, Brasil, últimos 5 anos, um termo por consulta
  (`termo_busca`). O Google entrega um índice de 0 a 100 relativo ao pico do termo no período, não o
  volume absoluto.
- **Coleta:** `python -m pipeline.coleta_trends` (dependências em `requirements-pipeline.txt`). O
  resultado bruto fica em `raw/google_trends_<data>.csv` e é versionado para a análise ser
  reproduzível. Coleta atual: `raw/google_trends_2026-11-10.csv` (10 termos × 262 semanas).
- **Pré-processamento:** `python -m pipeline.preprocessamento`. Descarta a semana parcial (ainda em
  andamento) e calcula, para cada termo:

| Métrica | Cálculo |
|---|---|
| `interesse_recente` | média das últimas 12 semanas |
| `variacao_12m_pct` | média das últimas 52 semanas comparada com as 52 anteriores, em % |
| `volatilidade` | desvio-padrão ÷ média das últimas 52 semanas |
| `mes_pico`, `amplitude_sazonal` | mês com maior média histórica e quanto ele fica acima da média geral |

- **Regras de classificação:**
  - `score_relevancia = 0,5 × interesse_recente + 0,5 × (50 + variação)`, com a segunda parcela
    limitada entre 0 e 100. Assim um termo estável fica perto de 50, um em alta passa disso e um em
    queda fica abaixo.
  - `nivel_risco`: **Alto** se a variação for de -15% ou pior; **Baixo** se crescer 10% ou mais com
    volatilidade abaixo de 0,35; **Moderado** nos demais casos. A volatilidade entra porque um
    termo que cresce mas oscila muito (ex.: peça de estação) não é aposta segura para estoque.
  - `sazonalidade`: **Atemporal** se o mês de pico fica menos de 25% acima da média; senão
    **Primavera/Verão** (pico de setembro a fevereiro) ou **Outono/Inverno**.

Os limiares (-15%, +10%, 0,35, 25%) são escolhas da autora para separar quedas e altas claras de
oscilações normais. Eles estão em constantes no topo de `pipeline/preprocessamento.py` e têm testes
em `tests/test_preprocessamento.py`.

## Texto sintético: descrições

As descrições (`conteudo`) foram escritas pela autora para dar ao RAG um texto que explique o produto
(modelagem, tecido, uso). Elas não trazem números nem citam relatórios. Todo dado quantitativo vem do
Google Trends. Cada registro marca isso em `origem_descricao`.

**Justificativa:** não existe base pública que descreva produtos de moda masculina e as respectivas
tendências em português. Relatórios como os da WGSN são pagos e não podem ser redistribuídos. Por
isso, a descrição qualitativa é sintética e a evidência de mercado é real e reproduzível.

## Limitações

- Interesse de busca não é venda: mostra curiosidade do público, não conversão.
- O índice é relativo a cada termo, então `interesse_recente` compara o termo com ele mesmo, não com
  os outros termos.
- O resultado depende da escolha do `termo_busca` (ex.: "tênis branco" também capta modelos femininos).
- São 10 termos: a base cobre categorias principais, não um catálogo completo.

## Tendências sugeridas pelo LLM

A rota `/ia/gerar-tendencias` pode acrescentar tendências sugeridas pelo LLM. Elas não fazem parte
desta base, ficam gravadas com a fonte "Sugestão de LLM (não verificada)" e não são alteradas pela
ingestão.
