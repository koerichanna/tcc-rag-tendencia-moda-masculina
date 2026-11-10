import { useState } from 'react';
import { AlertTriangle, CheckCircle2, Package, PlusCircle, RefreshCw, Sparkles } from 'lucide-react';
import { api } from '../api';
import { PRODUTO_VAZIO } from '../constants';
import Modal from '../components/Modal';
import RiscoBadge from '../components/RiscoBadge';
import SelectCategoria from '../components/SelectCategoria';

function ModalNovoProduto({ onFechar, onSalvo }) {
  const [produto, setProduto] = useState(PRODUTO_VAZIO);
  const alterar = (campo) => (e) => setProduto({ ...produto, [campo]: e.target.value });

  const salvar = async (e) => {
    e.preventDefault();
    try {
      await api.criarProduto({
        nome: produto.nome,
        categoria: produto.categoria,
        preco_medio: parseFloat(produto.preco_medio) || 0,
        custo_aquisicao: parseFloat(produto.custo_aquisicao) || 0,
        quantidade_estoque: parseInt(produto.quantidade_estoque) || 0,
        estoque_minimo: parseInt(produto.estoque_minimo) || 0,
        tendencia_score: parseFloat(produto.tendencia_score) || 50,
      });
      onSalvo();
    } catch (err) {
      alert('Não foi possível cadastrar o produto:\n' + err.message);
    }
  };

  return (
    <Modal titulo="Cadastrar produto" maxWidth="500px" zIndex={50}>
      <h3 style={{ fontSize: '1.2rem', fontWeight: 700, marginBottom: '1.25rem' }}>
        Cadastrar Produto no Estoque
      </h3>
      <form onSubmit={salvar}>
        <div className="rag-form-group">
          <label htmlFor="prod-nome">Nome do Produto:</label>
          <input id="prod-nome" className="rag-input" required minLength={2} maxLength={200}
            placeholder="Ex: Camiseta Oversized Algodão Heavy"
            value={produto.nome} onChange={alterar('nome')} />
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
          <div className="rag-form-group">
            <label htmlFor="prod-categoria">Categoria:</label>
            <SelectCategoria id="prod-categoria" value={produto.categoria}
              onChange={(categoria) => setProduto({ ...produto, categoria })} />
          </div>
          <div className="rag-form-group">
            <label htmlFor="prod-preco">Preço de Venda (R$):</label>
            <input id="prod-preco" type="number" step="0.01" min="0" className="rag-input" required
              value={produto.preco_medio} onChange={alterar('preco_medio')} />
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
          <div className="rag-form-group">
            <label htmlFor="prod-estoque">Estoque Atual:</label>
            <input id="prod-estoque" type="number" min="0" className="rag-input" required
              value={produto.quantidade_estoque} onChange={alterar('quantidade_estoque')} />
          </div>
          <div className="rag-form-group">
            <label htmlFor="prod-minimo">Estoque Mínimo:</label>
            <input id="prod-minimo" type="number" min="0" className="rag-input" required
              value={produto.estoque_minimo} onChange={alterar('estoque_minimo')} />
          </div>
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1.5rem' }}>
          <button type="button" onClick={onFechar}
            style={{ padding: '0.6rem 1.25rem', borderRadius: '6px', background: '#f1f5f9', color: '#475569', fontWeight: 600 }}>
            Cancelar
          </button>
          <button type="submit"
            style={{ padding: '0.6rem 1.25rem', borderRadius: '6px', background: '#2563eb', color: 'white', fontWeight: 600 }}>
            Salvar Produto
          </button>
        </div>
      </form>
    </Modal>
  );
}

function ModalAvaliacao({ avaliacao, onFechar }) {
  return (
    <Modal titulo={`Avaliação de ${avaliacao.produto_nome}`} maxWidth="580px">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Sparkles size={22} color="#4338ca" />
          <h3 style={{ fontSize: '1.2rem', fontWeight: 700 }}>Avaliação Gemini: {avaliacao.produto_nome}</h3>
        </div>
        <RiscoBadge risco={avaliacao.nivel_risco} prefixo="Risco: " />
      </div>

      <div className="action-highlight-box">
        <div className="action-title">Ação Recomendada pela IA</div>
        <div className="action-value">{avaliacao.acao_recomendada}</div>
        <div style={{ marginTop: '0.3rem', fontSize: '0.85rem', color: '#4338ca', fontWeight: 600 }}>
          Score de Tendência Atualizado: {avaliacao.novo_score_tendencia} / 100
        </div>
      </div>

      <div style={{ marginBottom: '1rem' }}>
        <h5 style={{ fontSize: '0.85rem', fontWeight: 700, color: '#334155', marginBottom: '0.2rem' }}>Diagnóstico de Mercado:</h5>
        <p style={{ fontSize: '0.9rem', color: '#1e293b', lineHeight: 1.5 }}>{avaliacao.diagnostico}</p>
      </div>

      <div style={{ background: '#f8fafc', padding: '1rem', borderRadius: '8px', border: '1px solid #e2e8f0', marginBottom: '1.5rem' }}>
        <h5 style={{ fontSize: '0.85rem', fontWeight: 700, color: '#334155', marginBottom: '0.3rem' }}>Justificativa Explicável:</h5>
        <p style={{ fontSize: '0.85rem', color: '#475569', lineHeight: 1.5 }}>{avaliacao.justificativa_explicavel}</p>
      </div>

      <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
        <button type="button" onClick={onFechar}
          style={{ padding: '0.6rem 1.5rem', borderRadius: '6px', background: '#2563eb', color: 'white', fontWeight: 600 }}>
          Entendido
        </button>
      </div>
    </Modal>
  );
}

function LinhaProduto({ produto, avaliando, onAvaliar }) {
  const estoqueCritico = produto.quantidade_estoque <= produto.estoque_minimo;
  return (
    <tr>
      <td>#{produto.id}</td>
      <td style={{ fontWeight: 600 }}>{produto.nome}</td>
      <td>{produto.categoria}</td>
      <td>R$ {produto.preco_medio.toFixed(2)}</td>
      <td style={{ fontWeight: 700, color: estoqueCritico ? '#dc2626' : '#1e293b' }}>{produto.quantidade_estoque} un</td>
      <td>{produto.estoque_minimo} un</td>
      <td>
        <span className="badge" style={{ background: '#ede9fe', color: '#6d28d9' }}>
          {produto.tendencia_score} / 100
        </span>
      </td>
      <td>
        {estoqueCritico ? (
          <span className="badge badge-risk-alto"><AlertTriangle size={12} /> Crítico</span>
        ) : (
          <span className="badge badge-risk-baixo"><CheckCircle2 size={12} /> Adequado</span>
        )}
      </td>
      <td>
        <button type="button" className="badge" disabled={avaliando} onClick={onAvaliar}
          style={{ background: '#4338ca', color: 'white', cursor: 'pointer', padding: '0.4rem 0.65rem' }}>
          {avaliando
            ? <><RefreshCw className="animate-spin" size={12} /> Avaliando...</>
            : <><Sparkles size={12} /> Avaliar com IA</>}
        </button>
      </td>
    </tr>
  );
}

export default function Produtos({ produtos, onAtualizar }) {
  const [modalAberto, setModalAberto] = useState(false);
  const [avaliandoId, setAvaliandoId] = useState(null);
  const [avaliacao, setAvaliacao] = useState(null);

  const avaliar = async (id) => {
    setAvaliandoId(id);
    try {
      setAvaliacao(await api.analisarProduto(id));
      onAtualizar();
    } catch (err) {
      alert('Erro ao analisar produto:\n' + err.message);
    } finally {
      setAvaliandoId(null);
    }
  };

  return (
    <div className="panel-card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h2 className="panel-title" style={{ marginBottom: '0.25rem' }}>
            <Package size={22} color="#059669" /> Catálogo da Loja & Análise Automatizada por IA
          </h2>
          <p style={{ fontSize: '0.85rem', color: '#64748b' }}>
            Avalie o potencial de mercado e os riscos de cada produto com um clique no botão <strong>Avaliar com IA</strong>.
          </p>
        </div>
        <button type="button" className="badge" onClick={() => setModalAberto(true)}
          style={{ background: '#2563eb', color: 'white', padding: '0.6rem 1rem', fontSize: '0.85rem', cursor: 'pointer' }}>
          <PlusCircle size={16} /> Novo Produto
        </button>
      </div>

      {produtos.length === 0 ? (
        <p style={{ color: '#64748b' }}>Nenhum produto cadastrado na loja.</p>
      ) : (
        <div className="table-container">
          <table className="custom-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Produto</th>
                <th>Categoria</th>
                <th>Preço Venda</th>
                <th>Estoque Atual</th>
                <th>Estoque Mínimo</th>
                <th>Score Tendência (IA)</th>
                <th>Status Estoque</th>
                <th>Ações com IA</th>
              </tr>
            </thead>
            <tbody>
              {produtos.map((p) => (
                <LinhaProduto key={p.id} produto={p} avaliando={avaliandoId === p.id} onAvaliar={() => avaliar(p.id)} />
              ))}
            </tbody>
          </table>
        </div>
      )}

      {avaliacao && <ModalAvaliacao avaliacao={avaliacao} onFechar={() => setAvaliacao(null)} />}
      {modalAberto && (
        <ModalNovoProduto
          onFechar={() => setModalAberto(false)}
          onSalvo={() => { setModalAberto(false); onAtualizar(); }}
        />
      )}
    </div>
  );
}
