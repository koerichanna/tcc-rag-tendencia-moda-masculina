const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Converte a resposta de erro do FastAPI em uma mensagem legível.
// 422 traz uma lista de erros de validação; os demais trazem `detail` como texto.
function mensagemDeErro(status, corpo) {
  const detalhe = corpo?.detail;
  if (Array.isArray(detalhe)) {
    return detalhe.map((e) => `${e.loc?.slice(-1)[0] ?? 'campo'}: ${e.msg}`).join('\n');
  }
  if (typeof detalhe === 'string') return detalhe;
  return `Erro ${status} ao falar com a API`;
}

async function requisicao(caminho, { method = 'GET', body } = {}) {
  const resposta = await fetch(`${API_BASE}${caminho}`, {
    method,
    headers: body ? { 'Content-Type': 'application/json' } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  const corpo = await resposta.json().catch(() => null);
  if (!resposta.ok) {
    throw new Error(mensagemDeErro(resposta.status, corpo));
  }
  return corpo;
}

export const api = {
  status: () => requisicao('/'),
  kpis: () => requisicao('/dashboard/kpis'),
  produtos: () => requisicao('/produtos/'),
  tendencias: () => requisicao('/tendencias/'),
  recomendacoes: () => requisicao('/recomendacoes/'),
  briefing: () => requisicao('/ia/briefing-executivo'),
  consultarRag: (dados) => requisicao('/rag/consultar', { method: 'POST', body: dados }),
  gerarTendencias: (tema) => requisicao('/ia/gerar-tendencias', { method: 'POST', body: { tema } }),
  analisarProduto: (id) => requisicao(`/ia/analisar-produto/${id}`, { method: 'POST' }),
  criarProduto: (dados) => requisicao('/produtos/', { method: 'POST', body: dados }),
};
