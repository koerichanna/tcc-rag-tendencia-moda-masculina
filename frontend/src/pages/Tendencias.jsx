import { useState } from 'react';
import { RefreshCw, Sparkles, TrendingUp } from 'lucide-react';
import { api } from '../api';
import Modal from '../components/Modal';
import RiscoBadge from '../components/RiscoBadge';

const PROXIMO_ANO = new Date().getFullYear() + 1;

function ListaGeradas({ tendencias }) {
  return (
    <ul className="lista-geradas">
      {tendencias.map((t) => (
        <li key={t.termo}>
          <div className="cabecalho-painel" style={{ marginBottom: '0.25rem' }}>
            <strong>{t.termo}</strong>
            <RiscoBadge risco={t.nivel_risco} prefixo="Risco: " />
          </div>
          <span className="texto-pequeno">{t.categoria} · {t.sazonalidade}</span>
          <p className="paragrafo" style={{ fontSize: '0.85rem' }}>{t.descricao}</p>
        </li>
      ))}
    </ul>
  );
}

function ModalGerarTendencias({ onFechar, onGeradas }) {
  const [tema, setTema] = useState(`Tendências Emergentes de Moda Masculina ${PROXIMO_ANO}`);
  const [gerando, setGerando] = useState(false);
  const [erro, setErro] = useState('');
  const [geradas, setGeradas] = useState(null);

  const gerar = async () => {
    setGerando(true);
    setErro('');
    try {
      const data = await api.gerarTendencias(tema);
      setGeradas(data.tendencias);
      onGeradas();
    } catch (err) {
      setErro(err.message);
    } finally {
      setGerando(false);
    }
  };

  if (geradas) {
    return (
      <Modal titulo="Tendências geradas pela IA" maxWidth="640px">
        <h3 className="modal-titulo"><Sparkles size={22} color="#4f46e5" /> {geradas.length} tendências sugeridas</h3>
        <p className="aviso-ajuste" role="note">
          Sugestões do LLM, não verificadas: o score e o risco foram estimados pela IA, não calculados a
          partir do Google Trends. Use como ponto de partida para pesquisar, não como dado de mercado.
        </p>
        <ListaGeradas tendencias={geradas} />
        <div className="modal-acoes">
          <button type="button" className="btn btn-confirmar" onClick={onFechar}>Fechar</button>
        </div>
      </Modal>
    );
  }

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

      {erro && <p role="alert" className="login-erro">{erro}</p>}
      {gerando && <p className="texto-pequeno">A IA costuma levar de 30 segundos a 1 minuto para responder.</p>}

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
          onGeradas={onAtualizar}
        />
      )}
    </div>
  );
}
