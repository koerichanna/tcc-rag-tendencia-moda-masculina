import { BarChart3, Brain, Package, TrendingUp } from 'lucide-react';

const ABAS = [
  { id: 'dashboard', rotulo: 'Visão Geral & Briefing IA', icone: BarChart3 },
  { id: 'rag', rotulo: 'Consultor RAG com IA', icone: Brain },
  { id: 'tendencias', rotulo: 'Tendências & Descoberta IA', icone: TrendingUp },
  { id: 'produtos', rotulo: 'Estoque & Avaliação IA', icone: Package },
];

export default function Tabs({ ativa, onSelecionar }) {
  return (
    <nav className="tabs-bar" role="tablist">
      {ABAS.map(({ id, rotulo, icone: Icone }) => (
        <button key={id} type="button" role="tab" aria-selected={ativa === id}
          className={`tab-btn ${ativa === id ? 'active' : ''}`} onClick={() => onSelecionar(id)}>
          <Icone size={18} /> {rotulo}
        </button>
      ))}
    </nav>
  );
}
