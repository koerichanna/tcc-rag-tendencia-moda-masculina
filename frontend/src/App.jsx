import { useState } from 'react';
import { LogIn, LogOut } from 'lucide-react';
import Header from './components/Header';
import LoginModal from './components/LoginModal';
import Tabs from './components/Tabs';
import useDadosLoja from './hooks/useDadosLoja';
import useSessao from './hooks/useSessao';
import ConsultorRag from './pages/ConsultorRag';
import Dashboard from './pages/Dashboard';
import Produtos from './pages/Produtos';
import Tendencias from './pages/Tendencias';
import './App.css';

const ESTILO_BOTAO = { background: '#f1f5f9', color: '#475569', cursor: 'pointer', padding: '0.4rem 0.6rem' };

export default function App() {
  const [abaAtiva, setAbaAtiva] = useState('dashboard');
  const [loginAberto, setLoginAberto] = useState(false);
  const { apiOnline, kpis, produtos, tendencias, recomendacoes, recarregar } = useDadosLoja();
  const { usuario, entrar, sair } = useSessao();
  const logado = Boolean(usuario);

  return (
    <div className="app-container">
      <Header apiOnline={apiOnline} onAtualizar={recarregar}>
        {logado ? (
          <button type="button" className="badge" style={ESTILO_BOTAO} onClick={sair}>
            <LogOut size={14} /> Sair ({usuario.nome_usuario})
          </button>
        ) : (
          <button type="button" className="badge" style={ESTILO_BOTAO} onClick={() => setLoginAberto(true)}>
            <LogIn size={14} /> Entrar
          </button>
        )}
      </Header>
      <Tabs ativa={abaAtiva} onSelecionar={setAbaAtiva} />

      <main className="main-content">
        {abaAtiva === 'dashboard' && <Dashboard kpis={kpis} recomendacoes={recomendacoes} />}
        {abaAtiva === 'rag' && <ConsultorRag produtos={produtos} onAtualizar={recarregar} />}
        {abaAtiva === 'tendencias' && <Tendencias tendencias={tendencias} logado={logado} onAtualizar={recarregar} />}
        {abaAtiva === 'produtos' && <Produtos produtos={produtos} logado={logado} onAtualizar={recarregar} />}
      </main>

      {loginAberto && <LoginModal onEntrar={entrar} onFechar={() => setLoginAberto(false)} />}
    </div>
  );
}
