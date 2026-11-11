import { useState } from 'react';
import { KeyRound, LogOut } from 'lucide-react';
import Header from './components/Header';
import Tabs from './components/Tabs';
import TrocarSenhaModal from './components/TrocarSenhaModal';
import useDadosLoja from './hooks/useDadosLoja';
import useSessao from './hooks/useSessao';
import ConsultorRag from './pages/ConsultorRag';
import Dashboard from './pages/Dashboard';
import Login from './pages/Login';
import Produtos from './pages/Produtos';
import Tendencias from './pages/Tendencias';
import Usuarios from './pages/Usuarios';
import './App.css';

// Só é montada depois do login, então os dados da loja são buscados já com o token.
function AreaLogada({ usuario, onSair }) {
  const [abaAtiva, setAbaAtiva] = useState('dashboard');
  const [trocandoSenha, setTrocandoSenha] = useState(false);
  const { apiOnline, kpis, produtos, tendencias, recomendacoes, recarregar } = useDadosLoja();
  const admin = usuario.perfil === 'admin';

  return (
    <div className="app-container">
      <Header apiOnline={apiOnline} onAtualizar={recarregar}>
        <button type="button" className="badge btn-cabecalho" onClick={() => setTrocandoSenha(true)}>
          <KeyRound size={14} /> Trocar senha
        </button>
        <button type="button" className="badge btn-cabecalho" onClick={onSair}>
          <LogOut size={14} /> Sair ({usuario.nome_usuario})
        </button>
      </Header>
      <Tabs ativa={abaAtiva} onSelecionar={setAbaAtiva} admin={admin} />

      <main className="main-content">
        {abaAtiva === 'dashboard' && <Dashboard kpis={kpis} recomendacoes={recomendacoes} />}
        {abaAtiva === 'rag' && <ConsultorRag produtos={produtos} onAtualizar={recarregar} />}
        {abaAtiva === 'tendencias' && <Tendencias tendencias={tendencias} onAtualizar={recarregar} />}
        {abaAtiva === 'produtos' && <Produtos produtos={produtos} onAtualizar={recarregar} />}
        {abaAtiva === 'usuarios' && admin && <Usuarios usuarioLogado={usuario} />}
      </main>

      {trocandoSenha && <TrocarSenhaModal onFechar={() => setTrocandoSenha(false)} />}
    </div>
  );
}

export default function App() {
  const { usuario, verificando, entrar, sair } = useSessao();

  if (verificando) return <div className="tela-carregando" role="status">Carregando...</div>;
  if (!usuario) return <Login onEntrar={entrar} />;
  return <AreaLogada usuario={usuario} onSair={sair} />;
}
