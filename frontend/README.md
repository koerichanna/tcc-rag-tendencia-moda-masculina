# Frontend

React 19 + Vite. Painel com KPIs, consulta ao RAG, tendências e cadastro de produtos.

```bash
npm install
npm run dev     # http://localhost:5173, API em http://localhost:8000
npm run lint
npm run build
```

A URL da API vem de `VITE_API_URL`. No build de produção (Dockerfile) ela é `/api`, que o Nginx
repassa para o backend.

## Estrutura

```
src/
  App.jsx              escolhe a aba e repassa os dados para as páginas
  api.js               todas as chamadas HTTP; converte erros da API em mensagens
  constants.js         categorias (iguais ao enum do backend) e perguntas de exemplo
  hooks/useDadosLoja   carrega KPIs, produtos, tendências e recomendações
  pages/               uma página por aba: Dashboard, ConsultorRag, Tendencias, Produtos
  components/          peças reutilizadas: Header, Tabs, Modal, RiscoBadge, SelectCategoria
  components/dashboard partes do painel: briefing, KPIs, top tendências, risco, histórico
```

Cada página cuida do próprio estado (formulários, modais, carregamento). Depois de uma ação que
altera dados, ela chama `onAtualizar`, que recarrega os dados compartilhados.
