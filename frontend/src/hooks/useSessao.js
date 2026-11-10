import { useCallback, useEffect, useState } from 'react';
import { api, quandoSessaoExpirar } from '../api';

// Usuário logado (ou null). Ao abrir a página, confirma com a API se o token salvo ainda vale.
export default function useSessao() {
  const [usuario, setUsuario] = useState(null);

  useEffect(() => {
    quandoSessaoExpirar(() => setUsuario(null));
    if (!api.temToken()) return;
    api.eu().then(setUsuario).catch(() => api.sair());
  }, []);

  const entrar = useCallback(async (nome, senha) => {
    setUsuario(await api.entrar(nome, senha));
  }, []);

  const sair = useCallback(() => {
    api.sair();
    setUsuario(null);
  }, []);

  return { usuario, entrar, sair };
}
