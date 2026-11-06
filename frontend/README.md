# Frontend

React 19 + Vite. Painel com KPIs, consulta ao RAG e cadastro de produtos.

```bash
npm install
npm run dev     # http://localhost:5173, API em http://localhost:8000
npm run lint
npm run build
```

A URL da API vem de `VITE_API_URL`. No build de produção (Dockerfile) ela é `/api`, que o Nginx
repassa para o backend.
