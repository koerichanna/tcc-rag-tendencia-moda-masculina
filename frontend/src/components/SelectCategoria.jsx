import { CATEGORIAS } from '../constants';

export default function SelectCategoria({ id, value, onChange, opcaoVazia }) {
  return (
    <select id={id} className="rag-select" value={value} onChange={(e) => onChange(e.target.value)}>
      {opcaoVazia && <option value="">{opcaoVazia}</option>}
      {CATEGORIAS.map((c) => (
        <option key={c} value={c}>{c}</option>
      ))}
    </select>
  );
}
