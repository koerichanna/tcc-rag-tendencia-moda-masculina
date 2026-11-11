import { Layers, Sparkles } from 'lucide-react';

const FAIXAS = [
  { risco: 'Baixo', rotulo: 'Baixo Risco', classe: 'badge-risk-baixo', descricao: 'Buscas em alta e estáveis' },
  { risco: 'Moderado', rotulo: 'Moderado', classe: 'badge-risk-moderado', descricao: 'Estável ou oscilando' },
  { risco: 'Alto', rotulo: 'Alto Risco', classe: 'badge-risk-alto', descricao: 'Buscas em queda ou sem volume' },
];

export default function DistribuicaoRisco({ distribuicao = {} }) {
  return (
    <div className="panel-card">
      <h2 className="panel-title"><Layers size={20} color="#d97706" /> Distribuição por Risco de Estoque</h2>
      <div style={{ marginTop: '1rem' }}>
        {FAIXAS.map((f) => (
          <div key={f.risco} className="risk-row">
            <div className="risk-label">
              <span className={`badge ${f.classe}`}>{f.rotulo}</span>
              <span className="texto-pequeno">{f.descricao}</span>
            </div>
            <strong style={f.risco === 'Alto' ? { color: '#dc2626' } : undefined}>
              {distribuicao[f.risco] ?? 0} tendências
            </strong>
          </div>
        ))}
      </div>

      <div className="caixa-cinza" style={{ marginTop: '2rem' }}>
        <h4 className="subtitulo titulo-com-icone">
          <Sparkles size={14} color="#2563eb" /> Como o risco é calculado
        </h4>
        <p className="texto-pequeno">
          A partir da variação do interesse de busca no Google Trends nos últimos 12 meses e da volatilidade da série.
          Termos quase sem buscas ficam com risco alto, por falta de evidência de demanda.
        </p>
      </div>
    </div>
  );
}
