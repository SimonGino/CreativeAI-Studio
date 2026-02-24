import { useEffect, useMemo, useRef, useState } from 'react'

export type CardSelectOption = {
  value: string
  label: string
  subtitle?: string
}

type Props = {
  label: string
  options: CardSelectOption[]
  value: string
  onChange: (value: string) => void
  placeholder?: string
  disabled?: boolean
}

export function CardSelect({
  label,
  options,
  value,
  onChange,
  placeholder = '请选择',
  disabled = false,
}: Props) {
  const [open, setOpen] = useState(false)
  const rootRef = useRef<HTMLDivElement | null>(null)

  const selected = useMemo(() => {
    return options.find((o) => o.value === value) || null
  }, [options, value])

  useEffect(() => {
    if (!open) return
    function onPointerDown(e: PointerEvent) {
      const el = rootRef.current
      if (!el) return
      const target = e.target as Node | null
      if (!target) return
      if (el.contains(target)) return
      setOpen(false)
    }
    document.addEventListener('pointerdown', onPointerDown)
    return () => document.removeEventListener('pointerdown', onPointerDown)
  }, [open])

  useEffect(() => {
    if (!open) return
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape') setOpen(false)
    }
    document.addEventListener('keydown', onKeyDown)
    return () => document.removeEventListener('keydown', onKeyDown)
  }, [open])

  const title = selected?.label || placeholder
  const subtitle = selected?.subtitle || label

  return (
    <div className="modelSelect" ref={rootRef}>
      <button
        type="button"
        className={open ? 'modelSelectBtn modelSelectBtnOpen' : 'modelSelectBtn'}
        onClick={() => setOpen((v) => !v)}
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-label={label}
        disabled={disabled}
      >
        <div className="modelRow">
          <div className="modelText">
            <div className="modelTitleRow">
              <div className="modelTitle">{title}</div>
            </div>
            <div className="modelSubtitle">{subtitle}</div>
          </div>
        </div>
        <div className="modelChevron" aria-hidden>
          ▾
        </div>
      </button>

      {open ? (
        <div className="modelMenu" role="listbox" aria-label={label}>
          {options.map((o) => {
            const isSelected = o.value === value
            return (
              <button
                key={o.value}
                type="button"
                role="option"
                aria-selected={isSelected}
                className={isSelected ? 'modelOption modelOptionSelected' : 'modelOption'}
                onClick={() => {
                  onChange(o.value)
                  setOpen(false)
                }}
              >
                <div className="modelRow">
                  <div className="modelText">
                    <div className="modelTitleRow">
                      <div className="modelTitle">{o.label}</div>
                    </div>
                    {o.subtitle ? <div className="modelSubtitle">{o.subtitle}</div> : null}
                  </div>
                </div>
                <div className="modelCheck" aria-hidden>
                  {isSelected ? '✓' : ''}
                </div>
              </button>
            )
          })}
        </div>
      ) : null}
    </div>
  )
}

