import { useState } from 'react';
import { LogIn } from 'lucide-react';
import Modal from './Modal';

export default function LoginModal({ onEntrar, onFechar }) {
  const [nome, setNome] = useState('');
  const [senha, setSenha] = useState('');
  const [erro, setErro] = useState('');
  const [enviando, setEnviando] = useState(false);

  const enviar = async (e) => {
    e.preventDefault();
    setEnviando(true);
    setErro('');
    try {
      await onEntrar(nome, senha);
      onFechar();
    } catch (err) {
      setErro(err.message);
    } finally {
      setEnviando(false);
    }
  };

  return (
    <Modal titulo="Entrar" maxWidth="400px">
      <h3 style={{ fontSize: '1.2rem', fontWeight: 700, marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <LogIn size={20} color="#2563eb" /> Entrar
      </h3>
      <p style={{ fontSize: '0.85rem', color: '#64748b', marginBottom: '1.25rem' }}>
        Necessário para cadastrar produtos e usar as ações de IA que alteram dados.
      </p>
      <form onSubmit={enviar}>
        <div className="rag-form-group">
          <label htmlFor="login-nome">Usuário:</label>
          <input id="login-nome" className="rag-input" autoComplete="username" required autoFocus
            value={nome} onChange={(e) => setNome(e.target.value)} />
        </div>
        <div className="rag-form-group">
          <label htmlFor="login-senha">Senha:</label>
          <input id="login-senha" type="password" className="rag-input" autoComplete="current-password" required
            value={senha} onChange={(e) => setSenha(e.target.value)} />
        </div>
        {erro && <p role="alert" style={{ color: '#dc2626', fontSize: '0.85rem', marginBottom: '0.75rem' }}>{erro}</p>}
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1rem' }}>
          <button type="button" onClick={onFechar}
            style={{ padding: '0.6rem 1.25rem', borderRadius: '6px', background: '#f1f5f9', color: '#475569', fontWeight: 600 }}>
            Cancelar
          </button>
          <button type="submit" disabled={enviando}
            style={{ padding: '0.6rem 1.25rem', borderRadius: '6px', background: '#2563eb', color: 'white', fontWeight: 600 }}>
            {enviando ? 'Entrando...' : 'Entrar'}
          </button>
        </div>
      </form>
    </Modal>
  );
}
