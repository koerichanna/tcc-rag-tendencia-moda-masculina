import { ShieldCheck } from 'lucide-react';

// Aparece quando o sistema corrigiu a resposta do LLM para respeitar o risco calculado
// a partir do Google Trends (ver coerencia.py no backend).
export default function AvisoAjuste({ ajustes }) {
  if (!ajustes?.length) return null;
  const partes = [];
  if (ajustes.includes('risco')) partes.push('o nível de risco');
  if (ajustes.includes('acao')) partes.push('a ação recomendada');
  return (
    <p role="note" style={{
      display: 'flex', gap: '0.5rem', alignItems: 'flex-start', fontSize: '0.8rem', color: '#92400e',
      background: '#fffbeb', border: '1px solid #fde68a', borderRadius: '8px', padding: '0.6rem 0.8rem', marginBottom: '1rem',
    }}>
      <ShieldCheck size={16} style={{ flexShrink: 0, marginTop: '0.1rem' }} />
      O sistema ajustou {partes.join(' e ')} da resposta da IA para respeitar o risco calculado a partir dos dados do Google Trends.
    </p>
  );
}
