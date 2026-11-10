import React, { useState, useEffect } from 'react';
import {
  TrendingUp,
  Brain,
  Package,
  AlertTriangle,
  ShoppingBag,
  Sparkles,
  Layers,
  BarChart3,
  RefreshCw,
  Bot,
  Zap
} from 'lucide-react';
import { api } from './api';
import ConsultorRag from './pages/ConsultorRag';
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

  const [briefing, setBriefing] = useState(null);
  const [loadingBriefing, setLoadingBriefing] = useState(false);

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

  const carregarBriefingIA = async () => {
    setLoadingBriefing(true);
    try {
      setBriefing(await api.briefing());
    } catch (e) {
      console.warn('Erro ao obter briefing:', e);
    } finally {
      setLoadingBriefing(false);
    }
  };

  useEffect(() => {
    carregarDados();
    carregarBriefingIA();
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
        {activeTab === 'dashboard' && (
          <div>
            <div style={{
              background: 'linear-gradient(135deg, #1e1b4b, #312e81)',
              color: 'white',
              borderRadius: '12px',
              padding: '1.5rem 1.75rem',
              marginBottom: '2rem',
              boxShadow: '0 4px 15px rgba(49, 46, 129, 0.2)'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                  <Bot size={22} color="#818cf8" />
                  <h3 style={{ fontSize: '1.15rem', fontWeight: 700 }}>
                    {briefing ? briefing.titulo : 'Briefing Estratégico'}
                  </h3>
                  <span className="badge" style={{ background: '#4338ca', color: '#c7d2fe', fontSize: '0.75rem' }}>
                    Análise em Tempo Real
                  </span>
                </div>
                <button
                  onClick={carregarBriefingIA}
                  disabled={loadingBriefing}
                  style={{ background: 'rgba(255,255,255,0.1)', color: 'white', padding: '0.4rem 0.8rem', borderRadius: '6px', fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: '0.3rem' }}
                >
                  <RefreshCw size={12} className={loadingBriefing ? 'animate-spin' : ''} />
                  {loadingBriefing ? 'Gerando Análise com Gemini...' : 'Recalcular Briefing'}
                </button>
              </div>

              <p style={{ fontSize: '0.95rem', lineHeight: 1.6, color: '#e0e7ff', marginBottom: '1.25rem' }}>
                {briefing ? briefing.resumo_executivo : 'Carregando análise estratégica do mix de produtos e tendências da sua loja...'}
              </p>

              {briefing && (briefing.pontos_atencao?.length > 0 || briefing.oportunidades?.length > 0) && (
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', paddingTop: '1rem', borderTop: '1px solid rgba(255,255,255,0.15)' }}>
                  <div>
                    <h5 style={{ fontSize: '0.8rem', textTransform: 'uppercase', color: '#fca5a5', fontWeight: 700, marginBottom: '0.4rem', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                      <AlertTriangle size={14} /> Pontos de Atenção no Estoque
                    </h5>
                    {briefing.pontos_atencao?.map((p, idx) => (
                      <div key={idx} style={{ fontSize: '0.85rem', color: '#fecaca', marginBottom: '0.2rem' }}>• {p}</div>
                    ))}
                  </div>
                  <div>
                    <h5 style={{ fontSize: '0.8rem', textTransform: 'uppercase', color: '#86efac', fontWeight: 700, marginBottom: '0.4rem', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                      <Zap size={14} /> Oportunidades de Compra
                    </h5>
                    {briefing.oportunidades?.map((o, idx) => (
                      <div key={idx} style={{ fontSize: '0.85rem', color: '#bbf7d0', marginBottom: '0.2rem' }}>• {o}</div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="kpi-grid">
              <div className="kpi-card">
                <div>
                  <div className="kpi-label">Produtos Cadastrados</div>
                  <div className="kpi-value">{kpis ? kpis.total_produtos : produtos.length}</div>
                </div>
                <div className="kpi-icon-wrapper icon-blue">
                  <Package size={24} />
                </div>
              </div>

              <div className="kpi-card">
                <div>
                  <div className="kpi-label">Tendências Mapeadas</div>
                  <div className="kpi-value">{kpis ? kpis.total_tendencias : tendencias.length}</div>
                </div>
                <div className="kpi-icon-wrapper icon-emerald">
                  <TrendingUp size={24} />
                </div>
              </div>

              <div className="kpi-card">
                <div>
                  <div className="kpi-label">Estoque Crítico (Abaixo do Mínimo)</div>
                  <div className="kpi-value" style={{ color: (kpis && kpis.produtos_estoque_critico > 0) ? '#dc2626' : '#0f172a' }}>
                    {kpis ? kpis.produtos_estoque_critico : 0}
                  </div>
                </div>
                <div className="kpi-icon-wrapper icon-amber">
                  <AlertTriangle size={24} />
                </div>
              </div>

              <div className="kpi-card">
                <div>
                  <div className="kpi-label">Recomendações Geradas por IA</div>
                  <div className="kpi-value">{kpis ? kpis.total_recomendacoes : recomendacoes.length}</div>
                </div>
                <div className="kpi-icon-wrapper icon-purple">
                  <Sparkles size={24} />
                </div>
              </div>
            </div>

            <div className="dashboard-columns">
              <div className="panel-card">
                <h2 className="panel-title">
                  <TrendingUp size={20} color="#2563eb" /> Top Tendências em Evidência
                </h2>
                <div>
                  {kpis && kpis.top_tendencias && kpis.top_tendencias.map((item) => (
                    <div key={item.id} className="trend-item">
                      <div className="trend-header">
                        <span className="trend-name">{item.termo}</span>
                        <span className="trend-score">{item.score} / 100</span>
                      </div>
                      <div className="progress-track">
                        <div className="progress-fill" style={{ width: `${item.score}%` }} />
                      </div>
                      <div className="trend-meta">
                        <span><strong>Categoria:</strong> {item.categoria}</span>
                        <span>•</span>
                        <span><strong>Sazonalidade:</strong> {item.sazonalidade || 'Atemporal'}</span>
                        <span>•</span>
                        <span className={`badge badge-risk-${item.risco.toLowerCase()}`}>
                          Risco: {item.risco}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="panel-card">
                <h2 className="panel-title">
                  <Layers size={20} color="#d97706" /> Distribuição por Risco de Estoque
                </h2>
                <div style={{ marginTop: '1rem' }}>
                  <div className="risk-row">
                    <div className="risk-label">
                      <span className="badge badge-risk-baixo">Baixo Risco</span>
                      <span style={{ fontSize: '0.8rem', color: '#64748b' }}>Alta procura e giro seguro</span>
                    </div>
                    <strong>{kpis && kpis.distribuicao_risco ? kpis.distribuicao_risco.Baixo : 0} tendências</strong>
                  </div>

                  <div className="risk-row">
                    <div className="risk-label">
                      <span className="badge badge-risk-moderado">Moderado</span>
                      <span style={{ fontSize: '0.8rem', color: '#64748b' }}>Adoção gradual</span>
                    </div>
                    <strong>{kpis && kpis.distribuicao_risco ? kpis.distribuicao_risco.Moderado : 0} tendências</strong>
                  </div>

                  <div className="risk-row">
                    <div className="risk-label">
                      <span className="badge badge-risk-alto">Alto Risco</span>
                      <span style={{ fontSize: '0.8rem', color: '#64748b' }}>Desaceleração de vendas</span>
                    </div>
                    <strong style={{ color: '#dc2626' }}>{kpis && kpis.distribuicao_risco ? kpis.distribuicao_risco.Alto : 0} tendências</strong>
                  </div>
                </div>

                <div style={{ marginTop: '2rem', padding: '1rem', background: '#f8fafc', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                  <h4 style={{ fontSize: '0.85rem', fontWeight: 600, color: '#334155', marginBottom: '0.3rem', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                    <Sparkles size={14} color="#2563eb" /> Inteligência Artificial Contínua
                  </h4>
                  <p style={{ fontSize: '0.8rem', color: '#64748b' }}>
                    As análises utilizam o <strong>LLM (Gemini)</strong> integrado ao banco vetorial ChromaDB para cruzar o mercado com o estoque da sua loja.
                  </p>
                </div>
              </div>
            </div>

            <div className="panel-card">
              <h2 className="panel-title">
                <Sparkles size={20} color="#7c3aed" /> Histórico de Análises & Recomendações por IA
              </h2>
              {recomendacoes.length === 0 ? (
                <p style={{ color: '#64748b', fontSize: '0.9rem' }}>Nenhuma recomendação registrada ainda.</p>
              ) : (
                <div className="table-container">
                  <table className="custom-table">
                    <thead>
                      <tr>
                        <th>Título da Análise</th>
                        <th>Categoria</th>
                        <th>Ação Recomendada</th>
                        <th>Prioridade</th>
                        <th>Justificativa Explicável da IA</th>
                      </tr>
                    </thead>
                    <tbody>
                      {recomendacoes.slice(0, 5).map((r) => (
                        <tr key={r.id}>
                          <td style={{ fontWeight: 600 }}>{r.titulo}</td>
                          <td>{r.categoria}</td>
                          <td>
                            <span className="badge" style={{ background: '#dbeafe', color: '#1e40af' }}>
                              {r.acao_sugerida}
                            </span>
                          </td>
                          <td>
                            <span className={`badge ${r.nivel_prioridade === 'Alta' ? 'badge-risk-alto' : 'badge-risk-moderado'}`}>
                              {r.nivel_prioridade}
                            </span>
                          </td>
                          <td style={{ fontSize: '0.825rem', color: '#475569', maxWidth: '400px' }}>
                            {r.justificativa}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'rag' && <ConsultorRag produtos={produtos} onAtualizar={carregarDados} />}

        {activeTab === 'tendencias' && <Tendencias tendencias={tendencias} onAtualizar={carregarDados} />}

        {activeTab === 'produtos' && <Produtos produtos={produtos} onAtualizar={carregarDados} />}
      </main>
    </div>
  );
}
