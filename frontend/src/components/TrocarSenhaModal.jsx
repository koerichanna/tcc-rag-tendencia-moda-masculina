import { useState } from 'react';
import { KeyRound } from 'lucide-react';
import { api } from '../api';
import Modal from './Modal';

const SENHA_MINIMA = 10;

export default function TrocarSenhaModal({ onFechar }) {
  const [atual, setAtual] = useState('');
  const [nova, setNova] = useState('');
  const [confirmacao, setConfirmacao] = useState('');
  const [erro, setErro] = useState('');
  const [sucesso, setSucesso] = useState(false);
  const [enviando, setEnviando] = useState(false);

  const enviar = async (e) => {
    e.preventDefault();
    if (nova !== confirmacao) {
      setErro('A confirmação não confere com a nova senha');
      return;
    }
    setEnviando(true);
    setErro('');
    try {
      await api.trocarSenha(atual, nova);
      setSucesso(true);
    } catch (err) {
      setErro(err.message);
    } finally {
      setEnviando(false);
    }
  };

  return (
    <Modal titulo="Trocar senha" maxWidth="420px">
      <h3 style={{ fontSize: '1.15rem', fontWeight: 700, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <KeyRound size={20} color="#2563eb" /> Trocar minha senha
      </h3>
      {sucesso ? (
        <>
          <p style={{ marginBottom: '1.25rem' }}>Senha alterada. Use a nova senha no próximo login.</p>
          <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
            <button type="button" className="btn-acao" onClick={onFechar}>Fechar</button>
          </div>
        </>
      ) : (
        <form onSubmit={enviar}>
          <div className="rag-form-group">
            <label htmlFor="senha-atual">Senha atual</label>
            <input id="senha-atual" type="password" className="rag-input" required autoFocus
              autoComplete="current-password" value={atual} onChange={(e) => setAtual(e.target.value)} />
          </div>
          <div className="rag-form-group">
            <label htmlFor="senha-nova">Nova senha</label>
            <input id="senha-nova" type="password" className="rag-input" required minLength={SENHA_MINIMA} maxLength={72}
              autoComplete="new-password" value={nova} onChange={(e) => setNova(e.target.value)}
              placeholder={`mínimo ${SENHA_MINIMA} caracteres`} />
          </div>
          <div className="rag-form-group">
            <label htmlFor="senha-confirmacao">Confirme a nova senha</label>
            <input id="senha-confirmacao" type="password" className="rag-input" required
              autoComplete="new-password" value={confirmacao} onChange={(e) => setConfirmacao(e.target.value)} />
          </div>
          {erro && <p role="alert" className="login-erro">{erro}</p>}
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
            <button type="button" className="btn-acao" onClick={onFechar}>Cancelar</button>
            <button type="submit" className="btn-acao" disabled={enviando}
              style={{ background: '#2563eb', color: 'white' }}>
              {enviando ? 'Salvando...' : 'Salvar'}
            </button>
          </div>
        </form>
      )}
    </Modal>
  );
}
