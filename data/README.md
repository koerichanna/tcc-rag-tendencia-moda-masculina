# Base de tendências

`market_trends.json` é a base de conhecimento indexada no ChromaDB e sincronizada com a tabela
`tendencias`. Cada registro junta duas coisas de origens diferentes:

| Parte | Origem | Campos |
|---|---|---|
| Métricas de interesse | **Dados reais** do Google Trends (Brasil) | `score_relevancia`, `nivel_risco`, `sazonalidade`, `metricas` |
| Descrição do produto | **Texto sintético** (ver abaixo) | `termo`, `categoria`, `estilo`, `conteudo` |

## Dados reais: Google Trends

- **O que é:** interesse de busca semanal no Google, Brasil, últimos 5 anos, um termo por consulta
  (`termo_busca`). O Google entrega um índice de 0 a 100 relativo ao pico do termo no período, não o
  volume absoluto.
- **Coleta:** `python -m pipeline.coleta_trends` (dependências em `requirements-pipeline.txt`). O
  resultado bruto fica em `raw/google_trends_<data>.csv` e é versionado para a análise ser
  reproduzível. Coleta atual: `raw/google_trends_2026-11-11.csv` (53 termos × 262 semanas). A coleta
  anterior, `raw/google_trends_2026-11-10.csv` (10 termos), fica guardada porque os números do pôster
  vêm dela. Para coletar só alguns termos e juntá-los ao arquivo do dia:
  `python -m pipeline.coleta_trends "termo 1" "termo 2"`.
- **Atualização semanal:** o workflow `.github/workflows/atualizar-trends.yml` roda toda segunda-feira
  (06h de Brasília): coleta todos os termos, recalcula as métricas e grava a coleta nova e o
  `market_trends.json` na `develop`. Em seguida dispara o CI, que testa e publica em homologação; a
  produção recebe os dados no próximo PR `develop` → `main`. Também pode ser disparado à mão na aba
  **Actions → Atualizar Google Trends → Run workflow**. Se o Google bloquear a coleta (erro 429), o
  workflow falha sem gravar nada e a base continua com a coleta anterior. Os números do pôster e de
  `docs/avaliacao_rag.md` continuam ligados às coletas de 10 e 11/11/2026, que ficam guardadas.
- **Pré-processamento:** `python -m pipeline.preprocessamento`. Descarta a semana parcial (ainda em
  andamento) e calcula, para cada termo:

| Métrica | Cálculo |
|---|---|
| `interesse_recente` | média das últimas 12 semanas |
| `variacao_12m_pct` | média das últimas 52 semanas comparada com as 52 anteriores, em % |
| `volatilidade` | desvio-padrão ÷ média das últimas 52 semanas |
| `mes_pico`, `amplitude_sazonal` | mês com maior média histórica e quanto ele fica acima da média geral |
| `semanas_zeradas_pct`, `dados_esparsos` | % das últimas 104 semanas sem buscas; esparso se for 50% ou mais |

- **Regras de classificação:**
  - `score_relevancia = 0,5 × interesse_recente + 0,5 × (50 + variação)`, com a segunda parcela
    limitada entre 0 e 100. Assim um termo estável fica perto de 50, um em alta passa disso e um em
    queda fica abaixo.
  - `nivel_risco`: **Alto** se a variação for de -15% ou pior; **Baixo** se crescer 10% ou mais com
    volatilidade abaixo de 0,35; **Moderado** nos demais casos. A volatilidade entra porque um
    termo que cresce mas oscila muito (ex.: peça de estação) não é aposta segura para estoque.
  - `sazonalidade`: **Atemporal** se o mês de pico fica menos de 25% acima da média; senão
    **Primavera/Verão** (pico de setembro a fevereiro) ou **Outono/Inverno**.
  - **Dados esparsos:** se metade ou mais das semanas dos últimos 2 anos tem interesse zero, a
    variação anual vira ruído (uma média anterior 0 dá "+100%"). Nesses termos a variação fica 0,
    a sazonalidade fica Atemporal e o risco fica **Alto**, porque não há evidência de demanda que
    justifique estoque. Na coleta atual isso acontece com "camisa cubana", "camiseta estampada
    masculina" e "short de linho masculino".

Os limiares (-15%, +10%, 0,35, 25%, 50%) são escolhas da autora para separar quedas e altas claras de
oscilações normais. Eles estão em constantes no topo de `pipeline/preprocessamento.py` e têm testes
em `tests/test_preprocessamento.py`.

## Texto sintético: descrições

As descrições (`conteudo`) dão ao RAG um texto que explique o produto (modelagem, tecido, uso). Elas
não trazem números nem citam relatórios: todo dado quantitativo vem do Google Trends. O campo
`origem_descricao` diz de onde veio cada texto:

- "Texto sintético redigido pela autora": os 10 registros originais;
- "Texto sintético (redação assistida por IA)": os 43 registros acrescentados na ampliação da base.

**Justificativa:** não existe base pública que descreva produtos de moda masculina e as respectivas
tendências em português. Relatórios como os da WGSN são pagos e não podem ser redistribuídos. Por
isso, a descrição qualitativa é sintética e a evidência de mercado é real e reproduzível.

## Limitações

- Interesse de busca não é venda: mostra curiosidade do público, não conversão.
- O índice é relativo a cada termo, então `interesse_recente` compara o termo com ele mesmo, não com
  os outros termos.
- O resultado depende da escolha do `termo_busca` (ex.: "tênis branco" também capta modelos femininos;
  "camisa retrô" capta outras camisas além das de futebol). Na ampliação, três termos com séries quase
  zeradas foram trocados por formas mais buscadas: "camisa de time retrô" → "camisa retrô",
  "camisa overshirt" → "overshirt" e "camisa oxford masculina" → "camisa oxford".
- São 53 termos: a base cobre as categorias principais do varejo masculino, não um catálogo completo.

## Tendências sugeridas pelo LLM

A rota `/ia/gerar-tendencias` pode acrescentar tendências sugeridas pelo LLM. Elas não fazem parte
desta base, ficam gravadas com a fonte "Sugestão de LLM (não verificada)" e não são alteradas pela
ingestão.
