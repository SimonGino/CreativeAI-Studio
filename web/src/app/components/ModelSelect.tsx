import { useEffect, useMemo, useRef, useState } from 'react'

import type { ModelInfo } from '../api/types'
import { providerLogoSrc } from '../ui/logo'

type BadgeTone = 'green' | 'blue' | 'amber'

type Badge = {
  label: string
  tone: BadgeTone
}

function buildBadges(model: ModelInfo): Badge[] {
  if (model.coming_soon) return [{ label: '即将上线', tone: 'amber' }]
  return []
}

function buildSubtitle(model: ModelInfo): string {
  const parts: string[] = []
  parts.push(model.model_id)
  if (model.media_type === 'image') {
    parts.push(model.reference_image_supported ? '支持参考图' : '文生图')
  } else {
    parts.push('视频生成')
  }
  return parts.join(' · ')
}

function toneClass(tone: BadgeTone): string {
  if (tone === 'green') return 'chip chipGreen'
  if (tone === 'blue') return 'chip chipBlue'
  return 'chip chipAmber'
}

type Props = {
  label?: string
  models: ModelInfo[]
  value: string
  onChange: (modelId: string) => void
}

export function ModelSelect({ label = '选择模型', models, value, onChange }: Props) {
  const [open, setOpen] = useState(false)
  const rootRef = useRef<HTMLDivElement | null>(null)

  const selected = useMemo(() => {
    return models.find((m) => m.model_id === value) || null
  }, [models, value])

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

  const title = selected?.display_name || selected?.model_id || label
  const subtitle = selected ? buildSubtitle(selected) : '未选择'

  return (
    <div className="modelSelect" ref={rootRef}>
      <button
        type="button"
        className={open ? 'modelSelectBtn modelSelectBtnOpen' : 'modelSelectBtn'}
        onClick={() => setOpen((v) => !v)}
        aria-haspopup="listbox"
        aria-expanded={open}
      >
        <div className="modelRow">
          <div className="modelIcon" aria-hidden>
            {selected?.provider_id ? (
              <img
                src={providerLogoSrc(selected.provider_id)}
                alt=""
                onError={(e) => {
                  e.currentTarget.style.display = 'none'
                }}
              />
            ) : null}
          </div>

          <div className="modelText">
            <div className="modelTitleRow">
              <div className="modelTitle">{title}</div>
              {selected ? (
                <div className="chips">
                  {buildBadges(selected).map((b) => (
                    <span key={b.label} className={toneClass(b.tone)}>
                      {b.label}
                    </span>
                  ))}
                </div>
              ) : null}
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
          {models.map((m) => {
            const isSelected = m.model_id === value
            const isDisabled = !!m.coming_soon
            return (
              <button
                key={m.model_id}
                type="button"
                role="option"
                aria-selected={isSelected}
                aria-disabled={isDisabled}
                disabled={isDisabled}
                className={[
                  'modelOption',
                  isSelected ? 'modelOptionSelected' : '',
                  isDisabled ? 'modelOptionDisabled' : '',
                ]
                  .filter(Boolean)
                  .join(' ')}
                onClick={() => {
                  if (isDisabled) return
                  onChange(m.model_id)
                  setOpen(false)
                }}
              >
                <div className="modelRow">
                  <div className="modelIcon" aria-hidden>
                    {m.provider_id ? (
                      <img
                        src={providerLogoSrc(m.provider_id)}
                        alt=""
                        onError={(e) => {
                          e.currentTarget.style.display = 'none'
                        }}
                      />
                    ) : null}
                  </div>
                  <div className="modelText">
                    <div className="modelTitleRow">
                      <div className="modelTitle">{m.display_name || m.model_id}</div>
                      <div className="chips">
                        {buildBadges(m).map((b) => (
                          <span key={`${m.model_id}-${b.label}`} className={toneClass(b.tone)}>
                            {b.label}
                          </span>
                        ))}
                      </div>
                    </div>
                    <div className="modelSubtitle">{buildSubtitle(m)}</div>
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
