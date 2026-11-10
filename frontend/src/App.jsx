import React, { useState, useEffect } from 'react';
import {
  TrendingUp,
  Brain,
  Package,
  ShoppingBag,
  BarChart3,
  RefreshCw,
  Zap
} from 'lucide-react';
import { api } from './api';
import ConsultorRag from './pages/ConsultorRag';
import Dashboard from './pages/Dashboard';
import Produtos from './pages/Produtos';
import Tendencias from './pages/Tendencias';
import './App.css';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [apiOnline, setApiOnline] = useState(false);

  const [kpis, setKpis] = useState(null);
  const [produtos, setProdutos] = useState([]);
  const [tendencias, setTendencias] = useState([]);
  const [recomendacoes, setRecomendacoes] = useState([]);

  const carregarDados = async () => {
    try {
      await api.status();
      setApiOnline(true);
    } catch (err) {
      console.warn('API offline:', err);
      setApiOnline(false);
      return;
    }
    // Cada bloco carrega independente: uma falha não esconde o resto do painel.
    const [kpiData, prodData, tendData, recData] = await Promise.allSettled([
      api.kpis(), api.produtos(), api.tendencias(), api.recomendacoes(),
    ]);
    if (kpiData.status === 'fulfilled') setKpis(kpiData.value);
    if (prodData.status === 'fulfilled') setProdutos(prodData.value);
    if (tendData.status === 'fulfilled') setTendencias(tendData.value);
    if (recData.status === 'fulfilled') setRecomendacoes(recData.value);
  };

  useEffect(() => {
    carregarDados();
  }, []);

  return (
    <div className="app-container">
      <header className="app-header">
        <div className="header-brand">
          <div className="brand-icon">
            <ShoppingBag size={24} />
          </div>
          <div>
            <h1 className="brand-title">Moda Inteligente</h1>
            <p className="brand-subtitle">Decisões Estratégicas e Inteligência de Mercado para o Varejo Masculino</p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div className="api-status" style={{ backgroundColor: apiOnline ? '#ecfdf5' : '#fef2f2', color: apiOnline ? '#059669' : '#dc2626' }}>
            <div className="status-dot" style={{ backgroundColor: apiOnline ? '#10b981' : '#ef4444' }} />
            {apiOnline ? 'Serviço Operacional' : 'Aguardando API'}
          </div>
          <button onClick={carregarDados} className="badge" style={{ background: '#f1f5f9', color: '#475569', cursor: 'pointer', padding: '0.4rem 0.6rem' }}>
            <RefreshCw size={14} /> Atualizar
          </button>
        </div>
      </header>

      <nav className="tabs-bar">
        <button
          className={`tab-btn ${activeTab === 'dashboard' ? 'active' : ''}`}
          onClick={() => setActiveTab('dashboard')}
        >
          <BarChart3 size={18} /> Visão Geral & Briefing IA
        </button>
        <button
          className={`tab-btn ${activeTab === 'rag' ? 'active' : ''}`}
          onClick={() => setActiveTab('rag')}
        >
          <Brain size={18} /> Consultor RAG com IA
        </button>
        <button
          className={`tab-btn ${activeTab === 'tendencias' ? 'active' : ''}`}
          onClick={() => setActiveTab('tendencias')}
        >
          <TrendingUp size={18} /> Tendências & Descoberta IA
        </button>
        <button
          className={`tab-btn ${activeTab === 'produtos' ? 'active' : ''}`}
          onClick={() => setActiveTab('produtos')}
        >
          <Package size={18} /> Estoque & Avaliação IA
        </button>
      </nav>

      <main className="main-content">
        {activeTab === 'dashboard' && <Dashboard kpis={kpis} recomendacoes={recomendacoes} />}

        {activeTab === 'rag' && <ConsultorRag produtos={produtos} onAtualizar={carregarDados} />}

        {activeTab === 'tendencias' && <Tendencias tendencias={tendencias} onAtualizar={carregarDados} />}

        {activeTab === 'produtos' && <Produtos produtos={produtos} onAtualizar={carregarDados} />}
      </main>
    </div>
  );
}
