import { useCallback, useEffect, useMemo, useState } from 'react'

import { api } from '../api/client'
import type { Asset } from '../api/types'
import { CardSelect } from './CardSelect'
import { Modal } from './Modal'

type OriginFilter = '' | 'generated' | 'upload'

type Props = {
  open: boolean
  title?: string
  selectedAssetId?: string | null
  defaultOrigin?: Exclude<OriginFilter, ''>
  onSelect: (asset: Asset) => void
  onClose: () => void
}

const LIMIT = 24

export function ImageAssetPickerModal({
  open,
  title = '选择图片资产',
  selectedAssetId,
  defaultOrigin = 'generated',
  onSelect,
  onClose,
}: Props) {
  const [origin, setOrigin] = useState<OriginFilter>(defaultOrigin)
  const [offset, setOffset] = useState(0)
  const [assets, setAssets] = useState<Asset[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (open) return
    setOffset(0)
  }, [open])

  function close() {
    setError(null)
    onClose()
  }

  const load = useCallback(async (isCanceled?: () => boolean) => {
    setLoading(true)
    setError(null)
    try {
      const list = await api.listAssets({
        media_type: 'image',
        origin: origin || undefined,
        limit: LIMIT,
        offset,
      })
      if (isCanceled?.()) return
      setAssets(list)
    } catch (e) {
      if (isCanceled?.()) return
      setError(e instanceof Error ? e.message : String(e))
      setAssets([])
    } finally {
      if (!isCanceled?.()) setLoading(false)
    }
  }, [offset, origin])

  useEffect(() => {
    if (!open) return
    let canceled = false
    load(() => canceled)
    return () => {
      canceled = true
    }
  }, [open, load])

  const page = useMemo(() => Math.floor(offset / LIMIT) + 1, [offset])
  const canPrev = offset > 0
  const canNext = assets.length === LIMIT

  return (
    <Modal
      open={open}
      title={title}
      ariaLabel={title}
      onClose={close}
      footer={
        <div className="modalFooterRow">
          <div className="muted">第 {page} 页</div>
          <div className="modalFooterActions">
            <button
              type="button"
              onClick={() => setOffset((v) => Math.max(0, v - LIMIT))}
              disabled={!canPrev || loading}
            >
              上一页
            </button>
            <button type="button" onClick={() => setOffset((v) => v + LIMIT)} disabled={!canNext || loading}>
              下一页
            </button>
            <button type="button" onClick={close}>
              关闭
            </button>
          </div>
        </div>
      }
    >
      <div className="modalControls">
        <div className="field" style={{ marginBottom: 0 }}>
          <div className="labelRow">
            <div>来源</div>
          </div>
          <CardSelect
            label="来源"
            value={origin}
            onChange={(v) => {
              setOrigin(v as OriginFilter)
              setOffset(0)
            }}
            options={[
              { value: 'generated', label: '生成', subtitle: '仅显示生成结果' },
              { value: 'upload', label: '上传', subtitle: '仅显示手动上传' },
              { value: '', label: '全部', subtitle: '生成 + 上传' },
            ]}
          />
        </div>
        <button
          type="button"
          onClick={() => load()}
          disabled={loading}
          style={{ flex: '0 0 auto' }}
        >
          刷新
        </button>
      </div>

      {error ? (
        <div className="statusPill danger" style={{ marginBottom: 12 }}>
          <span className="statusDot statusDotErr" />
          <span>{error}</span>
        </div>
      ) : null}

      {loading ? <div className="muted" style={{ marginBottom: 12 }}>加载中…</div> : null}

      <div className="assetGrid" aria-label="图片资产列表">
        {assets.map((a) => {
          const isSelected = a.id === selectedAssetId
          return (
            <button
              key={a.id}
              type="button"
              className={isSelected ? 'assetCard assetCardSelected' : 'assetCard'}
              onClick={() => {
                onSelect(a)
                close()
              }}
            >
              <img className="assetThumb" src={`/api/assets/${a.id}/content`} alt={a.id} loading="lazy" />
              <div className="assetMeta">
                <div className="assetId">{a.id.slice(0, 10)}</div>
                <div className="assetSub">
                  {a.origin} · {a.created_at}
                </div>
              </div>
            </button>
          )
        })}
      </div>

      {!loading && assets.length === 0 ? <div className="muted">暂无图片资产</div> : null}
    </Modal>
  )
}
