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
      <h3 className="modal-titulo"><Sparkles size={22} color="#4f46e5" /> Gerar Tendências com Gemini AI</h3>
      <p className="texto-ajuda com-margem">
        O LLM sugere novas tendências com pontuação de risco e relevância. Elas ficam marcadas como "não verificadas" e são salvas no PostgreSQL e indexadas no ChromaDB.
      </p>

      <div className="rag-form-group">
        <label htmlFor="tema-ia">Tema ou Foco de Pesquisa:</label>
        <input id="tema-ia" className="rag-input" value={tema} maxLength={200}
          onChange={(e) => setTema(e.target.value)}
          placeholder="Ex: Alfaiataria Desestruturada, Verão 2026, Calçados Urbanos" />
      </div>

      <div className="modal-acoes">
        <button type="button" className="btn btn-secundario" disabled={gerando} onClick={onFechar}>Cancelar</button>
        <button type="button" className="btn btn-ia" disabled={gerando || tema.trim().length < 3} onClick={gerar}>
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
    <div className="barra-score">
      <strong>{valor}</strong>
      <div className="barra-score-trilho">
        <div className="barra-score-preenchimento" style={{ width: `${valor}%` }} />
      </div>
    </div>
  );
}

export default function Tendencias({ tendencias, onAtualizar }) {
  const [modalAberto, setModalAberto] = useState(false);

  return (
    <div className="panel-card">
      <div className="cabecalho-painel">
        <div>
          <h2 className="panel-title"><TrendingUp size={22} color="#2563eb" /> Base de Tendências de Moda Masculina</h2>
          <p className="texto-ajuda">
            Score, risco e sazonalidade calculados a partir do interesse de busca no Google Trends.
          </p>
        </div>
        <button type="button" className="btn btn-ia" onClick={() => setModalAberto(true)}>
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
                <td className="celula-destaque">{t.termo}</td>
                <td><span className="badge badge-neutro">{t.categoria}</span></td>
                <td><BarraScore valor={t.score_relevancia} /></td>
                <td><RiscoBadge risco={t.nivel_risco} /></td>
                <td>{t.sazonalidade || 'Atemporal'}</td>
                <td className="texto-pequeno">{t.fonte}</td>
                <td className="texto-pequeno" style={{ maxWidth: '350px' }}>{t.descricao}</td>
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
