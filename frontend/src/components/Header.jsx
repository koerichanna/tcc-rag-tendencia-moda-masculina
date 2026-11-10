import { RefreshCw, ShoppingBag } from 'lucide-react';

export default function Header({ apiOnline, onAtualizar, children }) {
  return (
    <header className="app-header">
      <div className="header-brand">
        <div className="brand-icon"><ShoppingBag size={24} /></div>
        <div>
          <h1 className="brand-title">Moda Inteligente</h1>
          <p className="brand-subtitle">Decisões Estratégicas e Inteligência de Mercado para o Varejo Masculino</p>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <div className="api-status" role="status"
          style={{ backgroundColor: apiOnline ? '#ecfdf5' : '#fef2f2', color: apiOnline ? '#059669' : '#dc2626' }}>
          <div className="status-dot" style={{ backgroundColor: apiOnline ? '#10b981' : '#ef4444' }} />
          {apiOnline ? 'Serviço Operacional' : 'Aguardando API'}
        </div>
        <button type="button" onClick={onAtualizar} className="badge"
          style={{ background: '#f1f5f9', color: '#475569', cursor: 'pointer', padding: '0.4rem 0.6rem' }}>
          <RefreshCw size={14} /> Atualizar
        </button>
        {children}
      </div>
    </header>
  );
}
