const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const CHAVE_TOKEN = 'moda_token';

// O token fica na sessionStorage: vale enquanto a aba estiver aberta.
const token = {
  ler: () => sessionStorage.getItem(CHAVE_TOKEN),
  salvar: (valor) => sessionStorage.setItem(CHAVE_TOKEN, valor),
  apagar: () => sessionStorage.removeItem(CHAVE_TOKEN),
};

let aoPerderSessao = () => {};
export function quandoSessaoExpirar(callback) {
  aoPerderSessao = callback;
}

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

async function requisicao(caminho, { method = 'GET', body, form } = {}) {
  const headers = {};
  if (body) headers['Content-Type'] = 'application/json';
  const atual = token.ler();
  if (atual) headers.Authorization = `Bearer ${atual}`;

  const resposta = await fetch(`${API_BASE}${caminho}`, {
    method,
    headers,
    body: form ? new URLSearchParams(form) : body ? JSON.stringify(body) : undefined,
  });
  const corpo = await resposta.json().catch(() => null);
  if (!resposta.ok) {
    if (resposta.status === 401 && atual) {
      token.apagar();
      aoPerderSessao();
    }
    throw new Error(mensagemDeErro(resposta.status, corpo));
  }
  return corpo;
}

export const api = {
  temToken: () => Boolean(token.ler()),
  async entrar(nomeUsuario, senha) {
    const { access_token } = await requisicao('/auth/login', {
      method: 'POST',
      form: { username: nomeUsuario, password: senha },
    });
    token.salvar(access_token);
    return requisicao('/auth/me');
  },
  sair: () => token.apagar(),
  eu: () => requisicao('/auth/me'),
  trocarSenha: (senhaAtual, novaSenha) =>
    requisicao('/auth/me/senha', { method: 'PUT', body: { senha_atual: senhaAtual, nova_senha: novaSenha } }),

  usuarios: () => requisicao('/usuarios/'),
  criarUsuario: (dados) => requisicao('/usuarios/', { method: 'POST', body: dados }),
  atualizarUsuario: (id, dados) => requisicao(`/usuarios/${id}`, { method: 'PUT', body: dados }),
  excluirUsuario: (id) => requisicao(`/usuarios/${id}`, { method: 'DELETE' }),

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
