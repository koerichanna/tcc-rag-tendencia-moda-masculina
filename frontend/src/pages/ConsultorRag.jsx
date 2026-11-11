import { useState } from 'react';
import { ArrowRight, Brain, HelpCircle, RefreshCw, Sparkles } from 'lucide-react';
import { api } from '../api';
import { PERGUNTAS_EXEMPLO } from '../constants';
import AvisoAjuste from '../components/AvisoAjuste';
import RiscoBadge from '../components/RiscoBadge';
import SelectCategoria from '../components/SelectCategoria';

const CLASSE_ACAO = { Alto: 'action-danger', Baixo: 'action-success' };

function ResultadoRag({ resultado }) {
  return (
    <div className="rag-result-box">
      <div className="cabecalho-painel" style={{ alignItems: 'flex-start', marginBottom: '1rem' }}>
        <div>
          <span className="badge badge-roxo" style={{ marginBottom: '0.4rem' }}>Recomendação Explicável por IA</span>
          <h3 className="celula-destaque" style={{ fontSize: '1.15rem', fontWeight: 700 }}>{resultado.pergunta}</h3>
        </div>
        <RiscoBadge risco={resultado.nivel_risco} prefixo="Risco: " style={{ fontSize: '0.85rem', padding: '0.35rem 0.75rem' }} />
      </div>

      <div className={`action-highlight-box ${CLASSE_ACAO[resultado.nivel_risco] ?? ''}`}>
        <div className="action-title">Ação Recomendada pela IA ao Lojista</div>
        <div className="action-value">{resultado.acao_recomendada}</div>
      </div>

      <AvisoAjuste ajustes={resultado.ajustes_coerencia} />

      <div style={{ marginBottom: '1.25rem' }}>
        <h4 className="subtitulo">Diagnóstico de Mercado:</h4>
        <p className="paragrafo">{resultado.diagnostico}</p>
      </div>

      <div className="explanation-section">
        <div className="explanation-title">
          <HelpCircle size={18} color="#2563eb" /> Justificativa Explicável (Por que tomar esta decisão?)
        </div>
        <p className="paragrafo" style={{ fontSize: '0.875rem', color: '#334155' }}>{resultado.justificativa_explicavel}</p>

        {resultado.fontes_consultadas?.length > 0 && (
          <div style={{ marginTop: '0.75rem' }}>
            <span className="rotulo-secao">Fontes e Evidências Mapeadas:</span>
            <div className="sources-tags">
              {resultado.fontes_consultadas.map((f) => <span key={f} className="source-tag">{f}</span>)}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function SemResultado() {
  return (
    <div className="panel-card" style={{ textAlign: 'center', padding: '3.5rem 1.5rem' }}>
      <Brain size={48} color="#cbd5e1" style={{ margin: '0 auto 1rem auto' }} />
      <h3 className="subtitulo" style={{ fontSize: '1.1rem' }}>Nenhuma Análise Ativa</h3>
      <p className="texto-ajuda" style={{ maxWidth: '380px', margin: '0 auto' }}>
        Escolha uma pergunta sugerida ao lado ou digite sua dúvida sobre compras para receber a recomendação contextualizada com explicabilidade.
      </p>
    </div>
  );
}

export default function ConsultorRag({ produtos, onAtualizar }) {
  const [pergunta, setPergunta] = useState('');
  const [categoria, setCategoria] = useState('');
  const [produtoId, setProdutoId] = useState('');
  const [carregando, setCarregando] = useState(false);
  const [resultado, setResultado] = useState(null);

  const consultar = async (texto = pergunta, cat = categoria) => {
    if (texto.trim().length < 5) return;
    setCarregando(true);
    try {
      setResultado(await api.consultarRag({
        pergunta: texto,
        categoria: cat || null,
        produto_id: produtoId ? parseInt(produtoId) : null,
      }));
      onAtualizar();
    } catch (err) {
      alert('Erro ao consultar o RAG:\n' + err.message);
    } finally {
      setCarregando(false);
    }
  };

  const usarExemplo = (ex) => {
    setPergunta(ex.texto);
    setCategoria(ex.cat);
    consultar(ex.texto, ex.cat);
  };

  return (
    <div className="rag-layout">
      <div className="panel-card">
        <h2 className="panel-title"><Brain size={22} color="#2563eb" /> Consultor Virtual de Compras & Tendências</h2>
        <p className="texto-ajuda com-margem">
          O RAG recupera as tendências mais próximas da pergunta no ChromaDB e cruza com o estoque da loja para responder perguntas estratégicas de compra.
        </p>

        <div style={{ marginBottom: '1.25rem' }}>
          <span className="rotulo-secao">Perguntas Sugeridas:</span>
          <div className="lista-exemplos">
            {PERGUNTAS_EXEMPLO.map((ex) => (
              <button key={ex.texto} type="button" className="btn-exemplo" onClick={() => usarExemplo(ex)}>
                <span>{ex.texto}</span>
                <ArrowRight size={14} color="#2563eb" />
              </button>
            ))}
          </div>
        </div>

        <div className="rag-form-group">
          <label htmlFor="rag-pergunta">Sua Dúvida de Compra ou Tendência:</label>
          <textarea id="rag-pergunta" className="rag-textarea" rows={4} maxLength={500}
            placeholder="Ex: Vale a pena comprar 30 unidades de camisa de linho para o final de ano?"
            value={pergunta} onChange={(e) => setPergunta(e.target.value)} />
        </div>

        <div className="grade-2">
          <div className="rag-form-group">
            <label htmlFor="rag-categoria">Filtrar Categoria:</label>
            <SelectCategoria id="rag-categoria" value={categoria} onChange={setCategoria} opcaoVazia="Todas as Categorias" />
          </div>
          <div className="rag-form-group">
            <label htmlFor="rag-produto">Vincular a Produto da Loja:</label>
            <select id="rag-produto" className="rag-select" value={produtoId} onChange={(e) => setProdutoId(e.target.value)}>
              <option value="">Nenhum (Análise Geral de Mercado)</option>
              {produtos.map((p) => (
                <option key={p.id} value={p.id}>{p.nome} (Estoque: {p.quantidade_estoque})</option>
              ))}
            </select>
          </div>
        </div>

        <button type="button" className="btn-primary" disabled={carregando || pergunta.trim().length < 5} onClick={() => consultar()}>
          {carregando
            ? <><RefreshCw className="animate-spin" size={18} /> Consultando Gemini & ChromaDB...</>
            : <><Sparkles size={18} /> Analisar Decisão com IA</>}
        </button>
      </div>

      <div>{resultado ? <ResultadoRag resultado={resultado} /> : <SemResultado />}</div>
    </div>
  );
}
