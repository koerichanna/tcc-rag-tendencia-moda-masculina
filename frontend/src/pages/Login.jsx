import { useState } from 'react';
import { Lock, LogIn, ShoppingBag, User } from 'lucide-react';

export default function Login({ onEntrar }) {
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
    } catch (err) {
      setErro(err.message);
      setSenha('');
    } finally {
      setEnviando(false);
    }
  };

  return (
    <main className="login-page">
      <section className="login-card" aria-labelledby="login-titulo">
        <div className="login-brand">
          <div className="brand-icon"><ShoppingBag size={26} /></div>
          <div>
            <h1 id="login-titulo" className="brand-title">Moda Inteligente</h1>
            <p className="brand-subtitle">Inteligência de mercado para o varejo masculino</p>
          </div>
        </div>

        <form onSubmit={enviar} className="login-form">
          <div className="rag-form-group">
            <label htmlFor="login-nome">Usuário</label>
            <div className="login-campo">
              <User size={16} aria-hidden="true" />
              <input id="login-nome" className="rag-input" autoComplete="username" required autoFocus
                value={nome} onChange={(e) => setNome(e.target.value)} />
            </div>
          </div>
          <div className="rag-form-group">
            <label htmlFor="login-senha">Senha</label>
            <div className="login-campo">
              <Lock size={16} aria-hidden="true" />
              <input id="login-senha" type="password" className="rag-input" autoComplete="current-password" required
                value={senha} onChange={(e) => setSenha(e.target.value)} />
            </div>
          </div>

          {erro && <p role="alert" className="login-erro">{erro}</p>}

          <button type="submit" className="btn-primary" disabled={enviando}>
            <LogIn size={18} /> {enviando ? 'Entrando...' : 'Entrar'}
          </button>
        </form>

        <p className="login-ajuda">
          Não tem acesso? Peça a um administrador para cadastrar seu usuário.
        </p>
      </section>
    </main>
  );
}
