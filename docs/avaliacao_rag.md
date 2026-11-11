# Avaliação do RAG

Este documento mede as duas metades do consultor: a **recuperação** (o ChromaDB acha a tendência
certa para a pergunta?) e a **geração** (a resposta do LLM respeita os dados?). Tudo pode ser
reproduzido com os scripts de `avaliacao/`:

```bash
python -m avaliacao.avaliar_recuperacao      # ~1 min, sem LLM
python -m avaliacao.avaliar_respostas 8      # ~15 min, precisa de GOOGLE_API_KEY
```

Os números brutos ficam em `avaliacao/resultados/`. Base avaliada: 53 tendências (coleta do
Google Trends de 2026-11-11).

## 1. Recuperação

### Conjunto de perguntas

`avaliacao/perguntas.json` tem **105 perguntas** no tom de um lojista, cada uma com a tendência (ou
as tendências) que deveria ser recuperada. São três tipos:

| Tipo | Qtd. | O que testa |
|---|---|---|
| `direta` | 53 | a pergunta usa o nome da peça ("Calça cargo masculina está crescendo?") |
| `parafrase` | 26 | descreve a peça com outras palavras ("Calça com bolsos grandes nas laterais estilo militar vende?") |
| `sem_sobreposicao` | 26 | nenhuma palavra em comum com o documento certo ("Casacão estufado tipo edredom, compro?") |

O terceiro tipo foi criado depois de uma constatação: as perguntas e 43 das 53 descrições sintéticas
foram redigidas na mesma etapa, com assistência de IA, e mesmo as "paráfrases" repetiam em média 57%
das palavras do documento certo. Isso favorece a busca por palavras-chave. As perguntas `sem_sobreposicao` foram
filtradas por código (mesmo tokenizador do BM25) para garantir zero palavras em comum.

### Métricas

- **hit@1 / hit@3:** % de perguntas em que uma tendência certa aparece em 1º lugar / entre as 3
  primeiras (o consultor usa as 3 primeiras como contexto e a 1ª como referência de risco).
- **MRR@3:** média de 1/posição da primeira tendência certa (1,0 = sempre em 1º lugar).

### Configurações comparadas

- **BM25:** busca por palavras-chave (Okapi BM25 com redução simples de plural e gênero).
- **minilm-en:** `all-MiniLM-L6-v2`, o padrão do ChromaDB, treinado só em inglês.
- **multilíngue:** `paraphrase-multilingual-MiniLM-L12-v2` em ONNX quantizado (fp32 também testado).
- **híbrida:** BM25 + vetorial, combinados por Reciprocal Rank Fusion.

E dois formatos para o texto que vira vetor:

- **completo:** o documento inteiro entregue ao LLM (rótulos, risco, score, números do Google Trends
  e descrição);
- **descritivo:** só termo, categoria, estilo e descrição da peça.

### Resultados (105 perguntas, top-3)

Formato descritivo:

| Configuração | hit@1 | hit@3 | MRR | Diretas hit@3 | Paráfrases hit@3 | Sem sobreposição hit@3 |
|---|---|---|---|---|---|---|
| BM25 | 65,7% | 71,4% | 0,681 | 100% | 84,6% | 0,0% |
| minilm-en | 57,1% | 67,6% | 0,622 | 96,2% | 65,4% | 11,5% |
| multilíngue | 49,5% | 68,6% | 0,573 | 84,9% | 80,8% | 23,1% |
| multilíngue fp32 | 50,5% | 67,6% | 0,578 | 83,0% | 80,8% | 23,1% |
| híbrida + minilm-en | 63,8% | 71,4% | 0,670 | 100% | 80,8% | 3,8% |
| **híbrida + multilíngue (escolhida)** | 61,9% | **75,2%** | 0,678 | 94,3% | **96,2%** | 15,4% |

Formato completo, para comparação: multilíngue 24,8% / 43,8% (hit@1 / hit@3); híbrida + multilíngue
45,7% / 68,6%; minilm-en 56,2% / 66,7%.

### Significância

Teste de McNemar exato sobre o hit@3, comparando a configuração escolhida com as demais nas mesmas
perguntas:

| Híbrida + multilíngue contra | Só a híbrida acerta | Só a outra acerta | p |
|---|---|---|---|
| multilíngue, formato completo | 36 | 2 | < 0,001 |
| multilíngue, formato descritivo | 9 | 2 | 0,065 |
| minilm-en | 14 | 6 | 0,115 |
| BM25 | 7 | 3 | 0,344 |
| híbrida + minilm-en | 8 | 4 | 0,388 |

### O que os números mostram

1. **O formato do documento foi a decisão que mais pesou** e é o único ganho estatisticamente
   significativo. Com o texto completo, os rótulos e números repetidos em todos os documentos
   ("Nível de Risco: … Relevância: …/100 … Google Trends Brasil …") dominam a média dos vetores e
   os documentos ficam parecidos entre si. Por isso a aplicação guarda duas formas de cada
   tendência: a descritiva gera o vetor e a completa vai para o LLM (`vector_db.py`).
2. **A hipótese inicial estava errada.** Esperávamos que o modelo multilíngue ganhasse com folga
   do modelo em inglês. Sozinho, ele só foi melhor nas paráfrases e nas perguntas sem
   sobreposição; no geral empatou e errou mais a 1ª posição.
3. **A busca híbrida teve o melhor hit@3 e o melhor resultado nas paráfrases**, mas com 105
   perguntas a vantagem sobre o BM25 e sobre a híbrida com MiniLM não é significativa (p > 0,3).
   A escolha pela híbrida com o multilíngue se apoia em três pontos: melhor hit@3, nenhuma
   configuração foi melhor de forma significativa e ela é a única que acerta paráfrases e
   perguntas sem palavras em comum ao mesmo tempo.
4. **Perguntas sem nenhuma palavra em comum continuam difíceis:** a melhor configuração acerta
   cerca de 1 em cada 5 (o BM25 zera, por construção). É a principal limitação da recuperação.
5. **Quantizar o modelo não custou qualidade** (fp32 e quantizado empatam) e reduz o arquivo de
   470 MB para 118 MB, o que importa na VM ARM.
6. **Latência:** todas as configurações respondem em dezenas de milissegundos numa máquina comum.
   As medições oscilaram muito entre execuções (o mesmo modelo foi de ~30 ms a ~500 ms conforme a
   carga), então a latência não foi usada como critério.

### Erros encontrados pela avaliação

A avaliação e os testes de vínculo encontraram dois defeitos nas descrições sintéticas, corrigidos
**depois** de observados: a descrição do colete puffer citava "jaqueta puffer" e a da camisa cubana
citava "linho", o que fazia a busca escolher a tendência errada. A regra que fica: uma descrição
não deve citar características de outra tendência da base. Os números acima já são da base
corrigida; como a correção foi feita olhando os erros, eles podem estar levemente otimistas.

## 2. Geração

### Configurações

Mesmas perguntas, cinco formas de responder:

| Configuração | O que é |
|---|---|
| regras | só as regras locais (`sintetizar_resposta_contextual`), sem LLM |
| llm_sem_contexto | o Gemini responde sem documento recuperado e sem risco calculado |
| rag_sem_risco | RAG com o prompt anterior: contexto recuperado, sem o risco calculado |
| rag | RAG com o prompt atual: informa o risco calculado e as ações compatíveis |
| rag_validado | o anterior + a correção automática de `coerencia.py` (é o que a API devolve) |

### Métricas (automáticas, sem juiz humano nem LLM avaliador)

- **risco correto:** o `nivel_risco` da resposta é o risco calculado da tendência esperada;
- **ação coerente:** risco Alto não recomenda comprar e risco Baixo não recomenda liquidar;
- **sem números inventados:** todo percentual ou nota x/100 citado aparece nos dados das tendências
  esperada e recuperadas.

### Resultados

24 perguntas, 8 por nível de risco da tendência esperada. A avaliação foi rodada duas vezes (a
primeira com um erro na métrica de números, corrigido; as colunas de risco não foram afetadas):

| Configuração | Risco correto (rodada 1) | Risco correto (rodada 2) | Ação coerente (rodada 2) | Sem números inventados (rodada 2) | Respondidas (rodada 2) |
|---|---|---|---|---|---|
| regras | 95,8% | 91,7% | 95,8% | 100% | 24/24 |
| llm_sem_contexto | **28,6%** | **29,4%** | 94,1% | 100% | 17/24 |
| rag_sem_risco | 88,9% | 95,0% | 100% | 100% | 20/24 |
| rag | 95,2% | 91,3% | 100% | 95,7% | 23/24 |
| rag_validado | 95,2% | 91,3% | 100% | 95,7% | 23/24 |

O que os números mostram:

1. **Sem os dados recuperados, o LLM chuta o risco.** Nas duas rodadas o Gemini sem contexto
   acertou cerca de 29% dos riscos, abaixo do acaso entre três opções (33%). Com RAG, acima de
   90%. É a conclusão mais forte da avaliação e a justificativa para usar RAG.
2. **Informar o risco no prompt não teve efeito mensurável.** Na primeira rodada o prompt atual foi
   melhor (95,2% contra 88,9%); na segunda, o anterior (95,0% contra 91,3%). Com 24 perguntas e
   respostas faltando por falha do Gemini, a diferença é ruído.
3. **A correção automática não precisou agir nessas amostras:** com contexto, o Gemini nunca
   recomendou uma ação incompatível com o risco (ação coerente 100%). `coerencia.py` funciona como
   rede de segurança, e os testes de `tests/test_coerencia.py` comprovam que ela corrige quando
   o modelo erra.
4. **Os erros que sobram vêm da recuperação.** Os dois riscos errados do `rag_validado` na rodada 2
   ("Calça larga de perna ampla…" e "Calça baggy…") aconteceram porque a primeira tendência
   recuperada era outra calça. O mesmo explica os erros das `regras`.
5. **Números:** o modelo quase não inventou dados. A única resposta marcada citou "40" ao falar da
   camiseta oversized, cujo valor mais próximo nos dados é 41,6; provavelmente um arredondamento,
   mas a métrica conta como invenção. A partir desta versão o script também guarda o texto das
   respostas para esse tipo de conferência.

### Limitações desta avaliação

- O conjunto foi redigido dentro do projeto, com assistência de IA, e não por lojistas. As perguntas `sem_sobreposicao`
  reduzem, mas não eliminam, o viés de vocabulário.
- 24 perguntas na avaliação da geração é pouco para separar configurações próximas; a diferença
  grande (LLM sem contexto contra RAG) é a conclusão robusta.
- As métricas de geração verificam coerência e números, não a qualidade do texto. Uma avaliação
  com lojistas reais seria o próximo passo.
- O Gemini falhou em algumas chamadas (tempo esgotado ou serviço indisponível); essas respostas
  ficam de fora das porcentagens e a quantidade aparece na coluna "respondidas".

## Próximos passos

- Testar um modelo de embedding maior (ex.: multilingual-e5) para as perguntas sem sobreposição.
- Expandir a pergunta com sinônimos do vocabulário de moda antes da busca.
- Coletar perguntas de lojistas reais para um conjunto de avaliação independente.
