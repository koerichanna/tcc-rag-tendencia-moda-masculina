export default function Modal({ children, maxWidth = '520px', zIndex = 60, titulo }) {
  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label={titulo}
      style={{
        position: 'fixed',
        top: 0, left: 0, right: 0, bottom: 0,
        backgroundColor: 'rgba(15, 23, 42, 0.6)',
        display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex,
      }}
    >
      <div style={{ background: 'white', borderRadius: '12px', padding: '2rem', maxWidth, width: '90%' }}>
        {children}
      </div>
    </div>
  );
}
