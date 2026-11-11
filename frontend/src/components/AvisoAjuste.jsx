import { ShieldCheck } from 'lucide-react';

// Aparece quando o sistema corrigiu a resposta do LLM para respeitar o risco calculado
// a partir do Google Trends (ver coerencia.py no backend).
export default function AvisoAjuste({ ajustes }) {
  if (!ajustes?.length) return null;
  const partes = [];
  if (ajustes.includes('risco')) partes.push('o nível de risco');
  if (ajustes.includes('acao')) partes.push('a ação recomendada');
  return (
    <p role="note" className="aviso-ajuste">
      <ShieldCheck size={16} />
      O sistema ajustou {partes.join(' e ')} da resposta da IA para respeitar o risco calculado a partir dos dados do Google Trends.
    </p>
  );
}
