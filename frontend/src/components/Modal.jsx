// maxWidth e zIndex variam por modal, por isso ficam no style; o resto está em App.css.
export default function Modal({ children, maxWidth = '520px', zIndex = 60, titulo }) {
  return (
    <div role="dialog" aria-modal="true" aria-label={titulo} className="modal-fundo" style={{ zIndex }}>
      <div className="modal-caixa" style={{ maxWidth }}>
        {children}
      </div>
    </div>
  );
}
