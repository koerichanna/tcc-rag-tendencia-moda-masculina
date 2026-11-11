import { useCallback, useEffect, useState } from 'react';
import { api, quandoSessaoExpirar } from '../api';

// Usuário logado (ou null). Ao abrir a página, confirma com a API se o token salvo ainda vale;
// enquanto isso `verificando` fica true, para a tela de login não piscar antes do painel.
export default function useSessao() {
  const [usuario, setUsuario] = useState(null);
  const [verificando, setVerificando] = useState(api.temToken());

  useEffect(() => {
    quandoSessaoExpirar(() => setUsuario(null));
    if (!api.temToken()) return;
    api.eu()
      .then(setUsuario)
      .catch(() => api.sair())
      .finally(() => setVerificando(false));
  }, []);

  const entrar = useCallback(async (nome, senha) => {
    setUsuario(await api.entrar(nome, senha));
  }, []);

  const sair = useCallback(() => {
    api.sair();
    setUsuario(null);
  }, []);

  return { usuario, verificando, entrar, sair };
}
