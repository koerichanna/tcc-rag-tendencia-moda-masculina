# ADR 001: Hospedagem em nuvem e deploy

## Status
Aceito

## Contexto

O sistema precisa ficar no ar, com acesso público, até o fim do semestre (dezembro/2026). Ele roda
PostgreSQL, ChromaDB persistente (os embeddings são calculados localmente), a API FastAPI e o
frontend estático, e precisa de HTTPS.

Restrições do Portfólio Directions que pesaram na decisão:

- plataformas focadas em front-end (Vercel, Netlify, Render) e BaaS são vetadas;
- o deploy tem que passar por CI/CD, e deploy por SSH/FTP está na lista de "Não usar";
- SQLite/H2 não servem como banco;
- precisa haver ambientes separados de desenvolvimento e produção/homologação.

O orçamento é o crédito do Azure for Students (US$ 100).

## Alternativas

**Azure Container Apps + Azure Database for PostgreSQL.** Menos coisa para administrar, mas o
PostgreSQL gerenciado sozinho já consome boa parte do crédito, o ChromaDB precisaria de um volume
Azure Files montado e eu teria menos controle sobre o ambiente.

**Azure VM + Docker Compose (escolhida).** Uma VM Ubuntu roda os dois ambientes como projetos
Compose separados (`moda-production` e `moda-staging`), cada um com seu banco e seus volumes. Um
Caddy na frente faz HTTPS com Let's Encrypt para os dois domínios.

## Decisão

- VM Ubuntu 24.04 `Standard_B2s` (2 vCPU, 4 GB) na Azure.
- O GitHub Actions roda lint e testes, gera as imagens do backend e do frontend e publica no
  GitHub Container Registry com o SHA do commit como tag.
- O deploy usa `az vm run-command invoke`, autenticado por OIDC (sem senha guardada no GitHub). O
  comando passa pela API da Azure, então a porta 22 não precisa ficar aberta e não há chave SSH
  no pipeline.
- Push em `develop` implanta em homologação; push em `main` implanta em produção.
- Rollback: o workflow `rollback.yml` reimplanta qualquer SHA anterior, porque as imagens antigas
  continuam no GHCR.

## Consequências

- Custo previsível (~US$ 30/mês para a VM).
- Eu sou responsável por atualizar o sistema operacional e fazer backup dos volumes
  (`docker run --rm -v moda-production_postgres_data:/d ... tar`).
- Os dois ambientes dividem a mesma máquina: um pico em homologação afeta produção. Para o
  volume de uso esperado isso é aceitável.
- `run-command` é mais lento que SSH (~30 a 60 s por deploy).
