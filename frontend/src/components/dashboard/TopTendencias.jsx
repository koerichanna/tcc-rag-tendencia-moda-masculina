import { TrendingUp } from 'lucide-react';
import RiscoBadge from '../RiscoBadge';

export default function TopTendencias({ tendencias = [] }) {
  return (
    <div className="panel-card">
      <h2 className="panel-title"><TrendingUp size={20} color="#2563eb" /> Top Tendências em Evidência</h2>
      <div>
        {tendencias.map((item) => (
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
              <RiscoBadge risco={item.risco} prefixo="Risco: " />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
