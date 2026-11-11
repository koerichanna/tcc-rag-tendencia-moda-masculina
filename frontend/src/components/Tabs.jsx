import { BarChart3, Brain, Package, TrendingUp, Users } from 'lucide-react';

const ABAS = [
  { id: 'dashboard', rotulo: 'Visão Geral & Briefing IA', icone: BarChart3 },
  { id: 'rag', rotulo: 'Consultor RAG com IA', icone: Brain },
  { id: 'tendencias', rotulo: 'Tendências & Descoberta IA', icone: TrendingUp },
  { id: 'produtos', rotulo: 'Estoque & Avaliação IA', icone: Package },
  { id: 'usuarios', rotulo: 'Usuários', icone: Users, somenteAdmin: true },
];

export default function Tabs({ ativa, onSelecionar, admin = false }) {
  return (
    <nav className="tabs-bar" role="tablist">
      {ABAS.filter((aba) => admin || !aba.somenteAdmin).map(({ id, rotulo, icone: Icone }) => (
        <button key={id} type="button" role="tab" aria-selected={ativa === id}
          className={`tab-btn ${ativa === id ? 'active' : ''}`} onClick={() => onSelecionar(id)}>
          <Icone size={18} /> {rotulo}
        </button>
      ))}
    </nav>
  );
}
