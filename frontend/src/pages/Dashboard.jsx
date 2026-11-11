import { useEffect, useState } from 'react';
import { api } from '../api';
import BriefingCard from '../components/dashboard/BriefingCard';
import DistribuicaoRisco from '../components/dashboard/DistribuicaoRisco';
import HistoricoRecomendacoes from '../components/dashboard/HistoricoRecomendacoes';
import KpiGrid from '../components/dashboard/KpiGrid';
import TopTendencias from '../components/dashboard/TopTendencias';

export default function Dashboard({ kpis, recomendacoes }) {
  const [briefing, setBriefing] = useState(null);
  const [carregando, setCarregando] = useState(true);

  const buscarBriefing = () =>
    api.briefing()
      .then(setBriefing)
      .catch((e) => console.warn('Erro ao obter briefing:', e))
      .finally(() => setCarregando(false));

  useEffect(() => {
    buscarBriefing();
  }, []);

  const recalcular = () => {
    setCarregando(true);
    buscarBriefing();
  };

  return (
    <div>
      <BriefingCard briefing={briefing} carregando={carregando} onRecalcular={recalcular} />
      <KpiGrid kpis={kpis} />
      <div className="dashboard-columns">
        <TopTendencias tendencias={kpis?.top_tendencias} />
        <DistribuicaoRisco distribuicao={kpis?.distribuicao_risco} />
      </div>
      <HistoricoRecomendacoes recomendacoes={recomendacoes} />
    </div>
  );
}
