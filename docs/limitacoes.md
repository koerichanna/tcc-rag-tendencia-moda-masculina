# Limitações do projeto

Este documento reúne o que o sistema **não** faz bem, por que isso acontece, o que já foi feito para
reduzir o problema e como responder quando a banca perguntar. Os números vêm de
[avaliacao_rag.md](avaliacao_rag.md) (base de 53 tendências, coleta de 11/11/2026).

Resumo em uma frase: **o consultor acerta bem quando o lojista usa o nome da peça ou descreve a peça
com outras palavras, mas erra quando a pergunta não tem nenhuma palavra em comum com a base; os
dados mostram interesse de busca, não vendas; e a avaliação foi feita pela autora, sem lojistas
reais.**

| # | Limitação | Gravidade | Mitigação existente |
|---|---|---|---|
| 1 | Busca não é venda | Alta | cada resposta mostra a justificativa e os números usados |
| 2 | Perguntas sem palavras em comum: 15% de acerto | Alta | busca híbrida com modelo multilíngue |
| 3 | Avaliação feita sem lojistas reais | Alta | perguntas `sem_sobreposicao`, teste estatístico |
| 4 | Descrições das peças são sintéticas | Média | números vêm só do Google Trends; origem marcada |
| 5 | Índice do Google é relativo a cada termo | Média | métricas comparam o termo com ele mesmo |
| 6 | Limiares de risco escolhidos pela autora | Média | constantes documentadas e testadas |
| 7 | Base pequena (53 termos) e só Brasil | Média | categorias principais cobertas |
| 8 | Tendências geradas pela IA não são verificadas | Média | marcadas como "não verificada" na tela e no banco |
| 9 | Dependência do Gemini | Média | regras locais e checagem de coerência |
| 10 | Erros de recuperação viram erros de risco | Média | vínculo produto↔tendência, avaliação por tipo |
| 11 | Infraestrutura em uma VM só | Baixa (para um TCC) | deploy automatizado, rollback, monitoramento |
| 12 | Avaliação da geração com 24 perguntas | Baixa | só a diferença grande é tratada como conclusão |

---

## 1. Interesse de busca não é venda

**O que é:** o Google Trends mostra quantas pessoas pesquisaram um termo, não quantas compraram.
Uma peça pode ser muito pesquisada por curiosidade (um meme, uma celebridade) e vender pouco.

**Por que acontece:** não existe base pública de vendas de moda masculina no Brasil; dados de
varejo são privados.

**Impacto:** o "risco" calculado é risco de interesse, não de venda. Ele indica direção, não
quantidade a comprar.

**Mitigação:** a resposta traz a justificativa e os números usados, para o lojista decidir; o
sistema é apoio à decisão, não decisão automática. O cruzamento com o estoque do próprio lojista
(produtos cadastrados) aproxima a recomendação da realidade da loja.

**Como responder:** "Busca é um indicador antecedente de demanda, usado no varejo justamente
porque aparece antes da venda. O sistema não promete prever venda; ele mostra a direção do
interesse e explica a recomendação. Integrar o histórico de vendas da loja seria a evolução
natural."

## 2. Perguntas sem nenhuma palavra em comum com a base

**O que é:** se o lojista pergunta "Casacão estufado tipo edredom, compro?" e a base chama a peça
de "jaqueta puffer", o sistema acerta a tendência entre as 3 primeiras em só **15,4%** dos casos
(4 de 26 perguntas desse tipo). O BM25 sozinho acerta 0%, por construção.

**Por que acontece:** a busca por palavras (BM25) não tem o que casar, e o modelo de embedding
usado é pequeno (MiniLM, 118 MB) e não aprendeu o vocabulário informal de moda.

**Mitigação:** a busca híbrida com o modelo multilíngue é a única configuração testada que acerta
paráfrases (96,2%) e alguma coisa sem sobreposição ao mesmo tempo. Nas perguntas diretas o acerto
é 94,3%.

**Como responder:** "Medi isso de propósito: criei 26 perguntas filtradas por código para não ter
nenhuma palavra em comum, porque percebi que as paráfrases repetiam 57% das palavras e inflavam o
resultado. É a principal limitação da recuperação. Os próximos passos são um modelo maior, como o
multilingual-e5, ou expandir a pergunta com sinônimos de moda antes da busca."

## 3. A avaliação foi feita sem lojistas reais

**O que é:** as 105 perguntas de teste foram escritas dentro do projeto, com assistência de IA,
na mesma etapa em que 43 das 53 descrições foram redigidas. Ninguém do varejo avaliou as
respostas.

**Impacto:** o vocabulário das perguntas se parece com o das descrições, o que favorece a busca
por palavras. Os números podem ser otimistas em relação ao uso real.

**Mitigação:** o tipo `sem_sobreposicao` reduz esse viés; o teste de McNemar mostra o que é
diferença real e o que é ruído; os erros encontrados (colete puffer, camisa cubana) foram
registrados, inclusive o fato de que corrigi-los depois de vê-los deixa o número levemente
otimista.

**Como responder:** "É a limitação mais importante da avaliação e está escrita no relatório. O
próximo passo é coletar perguntas de lojistas reais e pedir que deem nota às respostas."

## 4. As descrições das peças são sintéticas

**O que é:** o texto que explica cada peça (modelagem, tecido, uso) foi escrito pela autora (10
registros) ou com assistência de IA (43 registros). Só os números são reais.

**Por que acontece:** não existe base pública em português que descreva produtos de moda
masculina e suas tendências; relatórios como os da WGSN são pagos e não podem ser redistribuídos.

**Mitigação:** as descrições não trazem números nem citam fontes; toda evidência quantitativa vem
do Google Trends e é reproduzível. O campo `origem_descricao` diz de onde veio cada texto.

**Como responder:** "Separei o que é qualitativo do que é evidência. A descrição só ajuda a busca
a entender a peça; risco, score e variação vêm de dados reais versionados no repositório."

## 5. O índice do Google é relativo a cada termo

**O que é:** o Google entrega um índice de 0 a 100 em que 100 é o pico **daquele termo** no
período. "Interesse 80" em "camiseta" e "interesse 80" em "mocassim" não significam o mesmo número
de buscas.

**Impacto:** não dá para dizer que uma peça é mais buscada que outra; só se cada uma está subindo
ou caindo em relação a ela mesma.

**Mitigação:** as métricas usadas (variação em 12 meses, volatilidade, sazonalidade) comparam o
termo com ele mesmo, que é o que o índice permite.

## 6. Os limiares de risco foram escolhidos pela autora

**O que é:** "Alto" se o interesse caiu 15% ou mais; "Baixo" se cresceu 10% ou mais com
volatilidade abaixo de 0,35; "esparso" se metade das semanas dos últimos 2 anos está zerada.
Esses cortes não vêm de literatura nem de dados de venda.

**Mitigação:** estão em constantes no topo de `pipeline/preprocessamento.py`, documentados em
`data/README.md` e cobertos por testes. Mudar um limiar é trocar um número e rodar o pipeline.

**Como responder:** "São parâmetros de negócio, e por isso ficaram explícitos e fáceis de ajustar.
Com dados de venda de uma loja, daria para calibrá-los."

## 7. Base pequena e só do Brasil

**O que é:** 53 termos cobrindo as categorias principais do varejo masculino (calças, camisas,
calçados, jaquetas etc.), não um catálogo completo. A coleta é só do Brasil. O resultado também
depende da palavra escolhida: "tênis branco" capta modelos femininos, "camisa retrô" capta mais do
que camisas de futebol.

**Mitigação:** três termos quase sem buscas foram trocados por formas mais pesquisadas; séries
esparsas recebem risco Alto em vez de uma variação enganosa (uma média anterior zero daria
"+100%"). A rotina semanal mantém os números atualizados.

## 8. Tendências geradas pela IA não são verificadas

**O que é:** a aba "Tendências e Descoberta com IA" pede ao Gemini novas tendências para um tema
(ex.: moda masculina 2027). Elas não vêm do Google Trends: são palpites do modelo.

**Mitigação:** ficam gravadas com a fonte "Sugestão de LLM (não verificada)", aparecem com aviso
na tela, não são alteradas pela ingestão e **não** são usadas para vincular produtos a
tendências.

**Como responder:** "É uma função de descoberta, para dar ideias. O sistema deixa claro que não é
evidência, e o consultor de compra prioriza os dados reais."

## 9. Dependência do Gemini

**O que é:** a resposta em linguagem natural depende de um serviço externo. Na avaliação, o
Gemini deixou de responder 1 a 7 de 24 perguntas, conforme a configuração (tempo esgotado ou
serviço indisponível). Há também a cota gratuita e a chave de API para proteger.

**Mitigação:** se o Gemini falhar, as regras locais respondem (91,7% de risco correto, sem LLM);
`coerencia.py` corrige ações incompatíveis com o risco; tempo limite de 30 s na consulta e 90 s na
geração de tendências, com erro explícito (HTTP 503) em vez de resposta vazia. A chave fica só no
`.env` da VM, fora do Git.

**O ponto forte que vem daqui:** sem os dados recuperados, o Gemini acertou só **29%** dos riscos
(abaixo do acaso entre três opções, 33%); com RAG, acima de **90%**. Essa é a justificativa
principal do RAG.

## 10. Erros de recuperação viram erros de risco

**O que é:** o risco da resposta vem da primeira tendência recuperada. Se a busca trouxer a calça
errada, o risco vem errado, mesmo com o Gemini funcionando bem. Os dois riscos errados da
avaliação da geração vieram daí ("calça larga de perna ampla" e "calça baggy" recuperaram outra
calça).

**Mitigação:** quando a pergunta é sobre um produto cadastrado, o sistema usa a tendência
vinculada a ele (busca restrita à mesma categoria); a avaliação separa os erros por tipo de
pergunta para mostrar onde a busca falha.

## 11. Infraestrutura em uma VM só

**O que é:** produção e homologação rodam na mesma VM ARM pequena da Azure (2 vCPU, 4 GB), com o
PostgreSQL e o ChromaDB em contêineres. Se a VM cair, os dois ambientes caem juntos. Bancos
gerenciados e alta disponibilidade ficaram de fora por custo (assinatura Azure for Students).

**Mitigação:** deploy automatizado pelo GitHub Actions, rollback por workflow, deploys
serializados, healthchecks, Prometheus e Grafana. A decisão está em
[adr-001-hospedagem-nuvem.md](adr-001-hospedagem-nuvem.md). O backup dos volumes é manual.

**Como responder:** "Para um TCC, uma VM com Docker Compose foi o melhor equilíbrio entre custo e
realismo. Para produção de verdade eu separaria os ambientes e usaria um banco gerenciado com
backup automático."

## 12. A avaliação da geração tem poucas perguntas

**O que é:** 24 perguntas (8 por nível de risco), rodadas duas vezes. É pouco para separar
configurações parecidas: o prompt com o risco informado foi melhor na primeira rodada e pior na
segunda.

**Mitigação:** o relatório só tira conclusão da diferença grande (29% sem contexto contra mais de
90% com RAG) e trata a diferença entre prompts como ruído. As métricas são automáticas (risco
correto, ação coerente, números inventados) e não medem a qualidade do texto.

---

## Perguntas prováveis da banca

**"Qual a maior limitação do seu trabalho?"**
Não ter validado com lojistas reais. Toda a avaliação foi feita por mim, com perguntas escritas no
projeto. Eu medi e documentei o viés que isso causa, mas o próximo passo é um teste com usuários.

**"Onde o sistema erra?"**
Em perguntas que não têm nenhuma palavra em comum com a base: acerta 15%. Nas perguntas com o nome
da peça acerta 94%, e com outras palavras, 96%.

**"Seus dados são reais?"**
Os números sim: Google Trends Brasil, 5 anos, coleta versionada e atualizada toda semana. As
descrições das peças são sintéticas, e isso está marcado em cada registro.

**"Por que não usar só o ChatGPT/Gemini?"**
Porque sem os dados ele chuta: acertou 29% dos riscos sem contexto e mais de 90% com RAG.

**"Busca no Google prevê venda?"**
Não. É um indicador de interesse que aparece antes da venda. O sistema mostra a direção e explica;
a decisão continua com o lojista.

**"O que você faria com mais tempo?"**
Validar com lojistas, testar um embedding maior para as perguntas difíceis, integrar o histórico de
vendas da loja para calibrar os limiares e separar produção e homologação em máquinas diferentes.
