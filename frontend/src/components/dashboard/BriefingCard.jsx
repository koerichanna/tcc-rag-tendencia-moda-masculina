import { AlertTriangle, Bot, RefreshCw, Zap } from 'lucide-react';

function ListaBriefing({ titulo, itens, icone, corTitulo, corItem }) {
  return (
    <div>
      <h5 style={{ fontSize: '0.8rem', textTransform: 'uppercase', color: corTitulo, fontWeight: 700, marginBottom: '0.4rem', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
        {icone} {titulo}
      </h5>
      {itens?.map((item) => (
        <div key={item} style={{ fontSize: '0.85rem', color: corItem, marginBottom: '0.2rem' }}>• {item}</div>
      ))}
    </div>
  );
}

export default function BriefingCard({ briefing, carregando, onRecalcular }) {
  const temListas = briefing && (briefing.pontos_atencao?.length > 0 || briefing.oportunidades?.length > 0);
  return (
    <div style={{ background: 'linear-gradient(135deg, #1e1b4b, #312e81)', color: 'white', borderRadius: '12px', padding: '1.5rem 1.75rem', marginBottom: '2rem', boxShadow: '0 4px 15px rgba(49, 46, 129, 0.2)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
          <Bot size={22} color="#818cf8" />
          <h3 style={{ fontSize: '1.15rem', fontWeight: 700 }}>{briefing ? briefing.titulo : 'Briefing Estratégico'}</h3>
          <span className="badge" style={{ background: '#4338ca', color: '#c7d2fe', fontSize: '0.75rem' }}>Análise em Tempo Real</span>
        </div>
        <button type="button" onClick={onRecalcular} disabled={carregando}
          style={{ background: 'rgba(255,255,255,0.1)', color: 'white', padding: '0.4rem 0.8rem', borderRadius: '6px', fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
          <RefreshCw size={12} className={carregando ? 'animate-spin' : ''} />
          {carregando ? 'Gerando Análise com Gemini...' : 'Recalcular Briefing'}
        </button>
      </div>

      <p style={{ fontSize: '0.95rem', lineHeight: 1.6, color: '#e0e7ff', marginBottom: '1.25rem' }}>
        {briefing ? briefing.resumo_executivo : 'Carregando análise estratégica do mix de produtos e tendências da sua loja...'}
      </p>

      {temListas && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', paddingTop: '1rem', borderTop: '1px solid rgba(255,255,255,0.15)' }}>
          <ListaBriefing titulo="Pontos de Atenção no Estoque" itens={briefing.pontos_atencao}
            icone={<AlertTriangle size={14} />} corTitulo="#fca5a5" corItem="#fecaca" />
          <ListaBriefing titulo="Oportunidades de Compra" itens={briefing.oportunidades}
            icone={<Zap size={14} />} corTitulo="#86efac" corItem="#bbf7d0" />
        </div>
      )}
    </div>
  );
}
