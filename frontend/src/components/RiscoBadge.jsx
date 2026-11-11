export default function RiscoBadge({ risco, prefixo = '', style }) {
  if (!risco) return null;
  return (
    <span className={`badge badge-risk-${risco.toLowerCase()}`} style={style}>
      {prefixo}{risco}
    </span>
  );
}
