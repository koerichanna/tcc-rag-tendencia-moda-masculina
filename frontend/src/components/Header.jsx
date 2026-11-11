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

      <div className="header-acoes">
        <div className={`api-status ${apiOnline ? 'online' : 'offline'}`} role="status">
          <div className="status-dot" />
          {apiOnline ? 'Serviço Operacional' : 'Aguardando API'}
        </div>
        <button type="button" onClick={onAtualizar} className="badge btn-cabecalho">
          <RefreshCw size={14} /> Atualizar
        </button>
        {children}
      </div>
    </header>
  );
}
