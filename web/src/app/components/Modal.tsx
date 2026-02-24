import type { ReactNode } from 'react'
import { useEffect, useRef } from 'react'

type Props = {
  open: boolean
  title?: string
  ariaLabel?: string
  children: ReactNode
  footer?: ReactNode
  onClose: () => void
}

export function Modal({ open, title, ariaLabel, children, footer, onClose }: Props) {
  const panelRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    if (!open) return
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', onKeyDown)
    return () => document.removeEventListener('keydown', onKeyDown)
  }, [open, onClose])

  useEffect(() => {
    if (!open) return
    const prevOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => {
      document.body.style.overflow = prevOverflow
    }
  }, [open])

  useEffect(() => {
    if (!open) return
    const t = window.setTimeout(() => panelRef.current?.focus(), 0)
    return () => window.clearTimeout(t)
  }, [open])

  if (!open) return null

  const label = ariaLabel || title || 'Dialog'

  return (
    <div
      className="modalOverlay"
      role="dialog"
      aria-modal="true"
      aria-label={label}
      onPointerDown={() => onClose()}
    >
      <div
        className="modalPanel"
        ref={panelRef}
        tabIndex={-1}
        onPointerDown={(e) => {
          e.stopPropagation()
        }}
      >
        <div className="modalHeader">
          <div className="modalTitle">{title || ''}</div>
          <button type="button" className="modalCloseBtn" onClick={onClose} aria-label="关闭">
            ×
          </button>
        </div>
        <div className="modalBody">{children}</div>
        {footer ? <div className="modalFooter">{footer}</div> : null}
      </div>
    </div>
  )
}

