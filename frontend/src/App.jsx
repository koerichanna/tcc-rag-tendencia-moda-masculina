import { useState } from 'react';
import Header from './components/Header';
import Tabs from './components/Tabs';
import useDadosLoja from './hooks/useDadosLoja';
import ConsultorRag from './pages/ConsultorRag';
import Dashboard from './pages/Dashboard';
import Produtos from './pages/Produtos';
import Tendencias from './pages/Tendencias';
import './App.css';

export default function App() {
  const [abaAtiva, setAbaAtiva] = useState('dashboard');
  const { apiOnline, kpis, produtos, tendencias, recomendacoes, recarregar } = useDadosLoja();

  return (
    <div className="app-container">
      <Header apiOnline={apiOnline} onAtualizar={recarregar} />
      <Tabs ativa={abaAtiva} onSelecionar={setAbaAtiva} />

      <main className="main-content">
        {abaAtiva === 'dashboard' && <Dashboard kpis={kpis} recomendacoes={recomendacoes} />}
        {abaAtiva === 'rag' && <ConsultorRag produtos={produtos} onAtualizar={recarregar} />}
        {abaAtiva === 'tendencias' && <Tendencias tendencias={tendencias} onAtualizar={recarregar} />}
        {abaAtiva === 'produtos' && <Produtos produtos={produtos} onAtualizar={recarregar} />}
      </main>
    </div>
  );
}
