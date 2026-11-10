import { AlertTriangle, Package, Sparkles, TrendingUp } from 'lucide-react';

function KpiCard({ rotulo, valor, icone, classeIcone, destaque }) {
  return (
    <div className="kpi-card">
      <div>
        <div className="kpi-label">{rotulo}</div>
        <div className="kpi-value" style={destaque ? { color: '#dc2626' } : undefined}>{valor}</div>
      </div>
      <div className={`kpi-icon-wrapper ${classeIcone}`}>{icone}</div>
    </div>
  );
}

export default function KpiGrid({ kpis }) {
  const critico = kpis?.produtos_estoque_critico ?? 0;
  return (
    <div className="kpi-grid">
      <KpiCard rotulo="Produtos Cadastrados" valor={kpis?.total_produtos ?? 0}
        icone={<Package size={24} />} classeIcone="icon-blue" />
      <KpiCard rotulo="Tendências Mapeadas" valor={kpis?.total_tendencias ?? 0}
        icone={<TrendingUp size={24} />} classeIcone="icon-emerald" />
      <KpiCard rotulo="Estoque Crítico (Abaixo do Mínimo)" valor={critico} destaque={critico > 0}
        icone={<AlertTriangle size={24} />} classeIcone="icon-amber" />
      <KpiCard rotulo="Recomendações Geradas por IA" valor={kpis?.total_recomendacoes ?? 0}
        icone={<Sparkles size={24} />} classeIcone="icon-purple" />
    </div>
  );
}
