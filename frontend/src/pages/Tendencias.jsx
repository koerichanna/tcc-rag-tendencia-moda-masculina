import { useState } from 'react';
import { RefreshCw, Sparkles, TrendingUp } from 'lucide-react';
import { api } from '../api';
import Modal from '../components/Modal';
import RiscoBadge from '../components/RiscoBadge';

function ModalGerarTendencias({ onFechar, onGeradas }) {
  const [tema, setTema] = useState('Tendências Emergentes de Moda Masculina 2026');
  const [gerando, setGerando] = useState(false);

  const gerar = async () => {
    setGerando(true);
    try {
      const data = await api.gerarTendencias(tema);
      alert(data.mensagem || 'Novas tendências geradas com sucesso!');
      onGeradas();
    } catch (err) {
      alert('Erro ao gerar tendências:\n' + err.message);
    } finally {
      setGerando(false);
    }
  };

  return (
    <Modal titulo="Gerar tendências com IA">
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
        <Sparkles size={22} color="#4f46e5" />
        <h3 style={{ fontSize: '1.2rem', fontWeight: 700 }}>Gerar Tendências com Gemini AI</h3>
      </div>
      <p style={{ fontSize: '0.85rem', color: '#64748b', marginBottom: '1.25rem' }}>
        O LLM sugere novas tendências com pontuação de risco e relevância. Elas ficam marcadas como "não verificadas" e são salvas no PostgreSQL e indexadas no ChromaDB.
      </p>

      <div className="rag-form-group">
        <label htmlFor="tema-ia">Tema ou Foco de Pesquisa:</label>
        <input id="tema-ia" className="rag-input" value={tema} maxLength={200}
          onChange={(e) => setTema(e.target.value)}
          placeholder="Ex: Alfaiataria Desestruturada, Verão 2026, Calçados Urbanos" />
      </div>

      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1.5rem' }}>
        <button type="button" disabled={gerando} onClick={onFechar}
          style={{ padding: '0.6rem 1.25rem', borderRadius: '6px', background: '#f1f5f9', color: '#475569', fontWeight: 600 }}>
          Cancelar
        </button>
        <button type="button" disabled={gerando || tema.trim().length < 3} onClick={gerar}
          style={{ padding: '0.6rem 1.25rem', borderRadius: '6px', background: '#4f46e5', color: 'white', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
          {gerando
            ? <><RefreshCw className="animate-spin" size={16} /> Pesquisando com Gemini...</>
            : <><Sparkles size={16} /> Gerar e Indexar</>}
        </button>
      </div>
    </Modal>
  );
}

function BarraScore({ valor }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
      <span style={{ fontWeight: 700, color: '#2563eb' }}>{valor}</span>
      <div style={{ width: '60px', height: '6px', background: '#e2e8f0', borderRadius: '4px' }}>
        <div style={{ width: `${valor}%`, height: '100%', background: '#3b82f6', borderRadius: '4px' }} />
      </div>
    </div>
  );
}

export default function Tendencias({ tendencias, logado, onAtualizar }) {
  const [modalAberto, setModalAberto] = useState(false);

  return (
    <div className="panel-card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h2 className="panel-title" style={{ marginBottom: '0.25rem' }}>
            <TrendingUp size={22} color="#2563eb" /> Base de Tendências de Moda Masculina
          </h2>
          <p style={{ fontSize: '0.85rem', color: '#64748b' }}>
            Score, risco e sazonalidade calculados a partir do interesse de busca no Google Trends.
          </p>
        </div>
        <button type="button" className="badge" onClick={() => setModalAberto(true)} disabled={!logado}
          title={logado ? undefined : 'Faça login para usar esta ação'}
          style={{ background: 'linear-gradient(135deg, #4f46e5, #7c3aed)', color: 'white', padding: '0.65rem 1.2rem', fontSize: '0.875rem', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
          <Sparkles size={16} /> Descobrir Novas Tendências com IA
        </button>
      </div>

      <div className="table-container">
        <table className="custom-table">
          <thead>
            <tr>
              <th>Termo / Tendência</th>
              <th>Categoria</th>
              <th>Score Relevância</th>
              <th>Nível de Risco</th>
              <th>Sazonalidade</th>
              <th>Fonte</th>
              <th>Contexto de Mercado</th>
            </tr>
          </thead>
          <tbody>
            {tendencias.map((t) => (
              <tr key={t.id}>
                <td style={{ fontWeight: 600, color: '#0f172a' }}>{t.termo}</td>
                <td><span className="badge" style={{ background: '#f1f5f9', color: '#334155' }}>{t.categoria}</span></td>
                <td><BarraScore valor={t.score_relevancia} /></td>
                <td><RiscoBadge risco={t.nivel_risco} /></td>
                <td>{t.sazonalidade || 'Atemporal'}</td>
                <td style={{ fontSize: '0.8rem', color: '#64748b' }}>{t.fonte}</td>
                <td style={{ fontSize: '0.825rem', color: '#475569', maxWidth: '350px' }}>{t.descricao}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {modalAberto && (
        <ModalGerarTendencias
          onFechar={() => setModalAberto(false)}
          onGeradas={() => { setModalAberto(false); onAtualizar(); }}
        />
      )}
    </div>
  );
}
