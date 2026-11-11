import { useCallback, useEffect, useState } from 'react';
import { KeyRound, Shield, Trash2, UserCheck, UserPlus, Users, UserX } from 'lucide-react';
import { api } from '../api';
import Modal from '../components/Modal';

const SENHA_MINIMA = 10;
const ROTULO_PERFIL = { admin: 'Administrador', usuario: 'Usuário' };

function formatarData(iso) {
  return iso ? new Date(iso).toLocaleDateString('pt-BR') : '—';
}

function FormNovoUsuario({ onCriado }) {
  const [nome, setNome] = useState('');
  const [senha, setSenha] = useState('');
  const [perfil, setPerfil] = useState('usuario');
  const [erro, setErro] = useState('');
  const [enviando, setEnviando] = useState(false);

  const enviar = async (e) => {
    e.preventDefault();
    setEnviando(true);
    setErro('');
    try {
      await api.criarUsuario({ nome_usuario: nome, senha, perfil });
      setNome('');
      setSenha('');
      setPerfil('usuario');
      onCriado();
    } catch (err) {
      setErro(err.message);
    } finally {
      setEnviando(false);
    }
  };

  return (
    <form onSubmit={enviar}>
      <div className="usuarios-form">
        <div className="rag-form-group">
          <label htmlFor="novo-nome">Usuário</label>
          <input id="novo-nome" className="rag-input" required minLength={3} maxLength={50}
            pattern="[A-Za-z0-9._\-]+" title="Letras, números, ponto, hífen ou sublinhado" autoComplete="off"
            value={nome} onChange={(e) => setNome(e.target.value)} placeholder="ex.: maria.silva" />
        </div>
        <div className="rag-form-group">
          <label htmlFor="novo-senha">Senha inicial</label>
          <input id="novo-senha" type="password" className="rag-input" required minLength={SENHA_MINIMA} maxLength={72}
            autoComplete="new-password" value={senha} onChange={(e) => setSenha(e.target.value)}
            placeholder={`mínimo ${SENHA_MINIMA} caracteres`} />
        </div>
        <div className="rag-form-group">
          <label htmlFor="novo-perfil">Perfil</label>
          <select id="novo-perfil" className="rag-select" value={perfil} onChange={(e) => setPerfil(e.target.value)}>
            <option value="usuario">Usuário</option>
            <option value="admin">Administrador</option>
          </select>
        </div>
        <button type="submit" className="btn-primary" disabled={enviando}>
          <UserPlus size={16} /> {enviando ? 'Cadastrando...' : 'Cadastrar'}
        </button>
      </div>
      {erro && <p role="alert" className="login-erro">{erro}</p>}
    </form>
  );
}

function RedefinirSenhaModal({ usuario, onFechar }) {
  const [senha, setSenha] = useState('');
  const [erro, setErro] = useState('');
  const [enviando, setEnviando] = useState(false);

  const enviar = async (e) => {
    e.preventDefault();
    setEnviando(true);
    setErro('');
    try {
      await api.atualizarUsuario(usuario.id, { senha });
      onFechar();
    } catch (err) {
      setErro(err.message);
      setEnviando(false);
    }
  };

  return (
    <Modal titulo="Redefinir senha" maxWidth="420px">
      <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '1rem' }}>
        Nova senha para <strong>{usuario.nome_usuario}</strong>
      </h3>
      <form onSubmit={enviar}>
        <div className="rag-form-group">
          <label htmlFor="redefinir-senha">Nova senha</label>
          <input id="redefinir-senha" type="password" className="rag-input" required autoFocus
            minLength={SENHA_MINIMA} maxLength={72} autoComplete="new-password"
            value={senha} onChange={(e) => setSenha(e.target.value)} />
        </div>
        {erro && <p role="alert" className="login-erro">{erro}</p>}
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
          <button type="button" className="btn-acao" onClick={onFechar}>Cancelar</button>
          <button type="submit" className="btn-acao" disabled={enviando}
            style={{ background: '#2563eb', color: 'white' }}>
            {enviando ? 'Salvando...' : 'Salvar senha'}
          </button>
        </div>
      </form>
    </Modal>
  );
}

function LinhaUsuario({ usuario, ehVoce, onAlterar, onRedefinirSenha, onExcluir }) {
  const avisoPropria = ehVoce ? 'Não é possível alterar a própria conta' : undefined;
  const outroPerfil = usuario.perfil === 'admin' ? 'usuario' : 'admin';

  return (
    <tr className={usuario.ativo ? undefined : 'usuario-inativo'}>
      <td style={{ fontWeight: 600 }}>
        {usuario.nome_usuario} {ehVoce && <span style={{ color: '#64748b', fontWeight: 400 }}>(você)</span>}
      </td>
      <td>
        <span className="badge" style={usuario.perfil === 'admin'
          ? { background: '#ede9fe', color: '#6d28d9' } : { background: '#f1f5f9', color: '#475569' }}>
          {ROTULO_PERFIL[usuario.perfil]}
        </span>
      </td>
      <td>
        <span className={`badge ${usuario.ativo ? 'badge-risk-baixo' : 'badge-risk-alto'}`}>
          {usuario.ativo ? 'Ativo' : 'Inativo'}
        </span>
      </td>
      <td>{formatarData(usuario.criado_em)}</td>
      <td>
        <div className="acoes-usuario">
          <button type="button" className="btn-acao" onClick={onRedefinirSenha}>
            <KeyRound size={13} /> Senha
          </button>
          <button type="button" className="btn-acao" disabled={ehVoce} title={avisoPropria}
            onClick={() => onAlterar({ perfil: outroPerfil })}>
            <Shield size={13} /> {outroPerfil === 'admin' ? 'Tornar admin' : 'Tornar usuário'}
          </button>
          <button type="button" className="btn-acao" disabled={ehVoce} title={avisoPropria}
            onClick={() => onAlterar({ ativo: !usuario.ativo })}>
            {usuario.ativo ? <><UserX size={13} /> Desativar</> : <><UserCheck size={13} /> Reativar</>}
          </button>
          <button type="button" className="btn-acao perigo" disabled={ehVoce} title={avisoPropria}
            onClick={onExcluir}>
            <Trash2 size={13} /> Excluir
          </button>
        </div>
      </td>
    </tr>
  );
}

export default function Usuarios({ usuarioLogado }) {
  const [usuarios, setUsuarios] = useState([]);
  const [erro, setErro] = useState('');
  const [redefinindo, setRedefinindo] = useState(null);

  const carregar = useCallback(() => {
    api.usuarios().then(setUsuarios).catch((err) => setErro(err.message));
  }, []);

  useEffect(() => { carregar(); }, [carregar]);

  const executar = async (acao) => {
    setErro('');
    try {
      await acao();
      carregar();
    } catch (err) {
      setErro(err.message);
    }
  };

  const excluir = (usuario) => {
    if (!window.confirm(`Excluir o usuário "${usuario.nome_usuario}"? Prefira desativar se quiser manter o registro.`)) return;
    executar(() => api.excluirUsuario(usuario.id));
  };

  return (
    <div className="panel-card">
      <h2 className="panel-title" style={{ marginBottom: '0.25rem' }}>
        <Users size={22} color="#4338ca" /> Gestão de Usuários
      </h2>
      <p style={{ fontSize: '0.85rem', color: '#64748b', marginBottom: '1.5rem' }}>
        Cadastre quem pode acessar a plataforma. Desativar corta o acesso na hora e mantém o registro;
        administradores também podem gerenciar usuários.
      </p>

      <FormNovoUsuario onCriado={carregar} />

      {erro && <p role="alert" className="login-erro">{erro}</p>}

      <div className="table-container">
        <table className="custom-table">
          <thead>
            <tr>
              <th>Usuário</th>
              <th>Perfil</th>
              <th>Situação</th>
              <th>Criado em</th>
              <th>Ações</th>
            </tr>
          </thead>
          <tbody>
            {usuarios.map((u) => (
              <LinhaUsuario key={u.id} usuario={u} ehVoce={u.nome_usuario === usuarioLogado.nome_usuario}
                onAlterar={(dados) => executar(() => api.atualizarUsuario(u.id, dados))}
                onRedefinirSenha={() => setRedefinindo(u)}
                onExcluir={() => excluir(u)} />
            ))}
          </tbody>
        </table>
      </div>

      {redefinindo && <RedefinirSenhaModal usuario={redefinindo} onFechar={() => setRedefinindo(null)} />}
    </div>
  );
}
