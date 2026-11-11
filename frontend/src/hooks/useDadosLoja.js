import { useCallback, useEffect, useState } from 'react';
import { api } from '../api';

// Busca tudo sem tocar no estado; quem chama decide o que fazer com o resultado.
async function buscarDados() {
  try {
    await api.status();
  } catch (err) {
    console.warn('API offline:', err);
    return { apiOnline: false };
  }
  // Cada bloco carrega de forma independente: uma falha não esconde o resto do painel.
  const [kpis, produtos, tendencias, recomendacoes] = await Promise.allSettled([
    api.kpis(), api.produtos(), api.tendencias(), api.recomendacoes(),
  ]);
  const valor = (r) => (r.status === 'fulfilled' ? r.value : undefined);
  return {
    apiOnline: true,
    kpis: valor(kpis),
    produtos: valor(produtos),
    tendencias: valor(tendencias),
    recomendacoes: valor(recomendacoes),
  };
}

// Dados que várias páginas usam (KPIs, produtos, tendências, recomendações).
export default function useDadosLoja() {
  const [dados, setDados] = useState({
    apiOnline: false, kpis: null, produtos: [], tendencias: [], recomendacoes: [],
  });

  const aplicar = useCallback((novos) => {
    // Mantém o valor anterior de um bloco que falhou nesta rodada.
    setDados((atual) => ({
      apiOnline: novos.apiOnline,
      kpis: novos.kpis ?? atual.kpis,
      produtos: novos.produtos ?? atual.produtos,
      tendencias: novos.tendencias ?? atual.tendencias,
      recomendacoes: novos.recomendacoes ?? atual.recomendacoes,
    }));
  }, []);

  const recarregar = useCallback(() => buscarDados().then(aplicar), [aplicar]);

  useEffect(() => {
    let ativo = true;
    buscarDados().then((novos) => ativo && aplicar(novos));
    return () => { ativo = false; };
  }, [aplicar]);

  return { ...dados, recarregar };
}
