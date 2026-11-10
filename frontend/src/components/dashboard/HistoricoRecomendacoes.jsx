import { Sparkles } from 'lucide-react';

export default function HistoricoRecomendacoes({ recomendacoes }) {
  return (
    <div className="panel-card">
      <h2 className="panel-title"><Sparkles size={20} color="#7c3aed" /> Histórico de Análises & Recomendações por IA</h2>
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
                  <td><span className="badge" style={{ background: '#dbeafe', color: '#1e40af' }}>{r.acao_sugerida}</span></td>
                  <td>
                    <span className={`badge ${r.nivel_prioridade === 'Alta' ? 'badge-risk-alto' : 'badge-risk-moderado'}`}>
                      {r.nivel_prioridade}
                    </span>
                  </td>
                  <td style={{ fontSize: '0.825rem', color: '#475569', maxWidth: '400px' }}>{r.justificativa}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
