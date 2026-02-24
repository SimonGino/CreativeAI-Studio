import { useEffect, useMemo, useRef, useState } from 'react'

import { api } from '../api/client'
import type { Asset } from '../api/types'
import { CardSelect } from '../components/CardSelect'

function formatBytes(size: number | null | undefined): string {
  const n = Number(size || 0)
  if (!Number.isFinite(n) || n <= 0) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  let value = n
  let idx = 0
  while (value >= 1024 && idx < units.length - 1) {
    value /= 1024
    idx += 1
  }
  return `${value >= 100 || idx === 0 ? value.toFixed(0) : value.toFixed(1)} ${units[idx]}`
}

function formatDateText(v: string | null | undefined): string {
  if (!v) return '-'
  const d = new Date(v)
  if (Number.isNaN(d.getTime())) return String(v)
  return d.toLocaleString()
}

function formatDims(a: Asset | null): string {
  if (!a) return '-'
  if (a.width && a.height) return `${a.width} × ${a.height}`
  return '-'
}

export function AssetsPage() {
  const [assets, setAssets] = useState<Asset[]>([])
  const [selected, setSelected] = useState<Asset | null>(null)
  const [mediaType, setMediaType] = useState<string>('')
  const [origin, setOrigin] = useState<string>('')
  const [error, setError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement | null>(null)

  async function refresh() {
    setError(null)
    try {
      const list = await api.listAssets({
        media_type: mediaType || undefined,
        origin: origin || undefined,
        limit: 50,
        offset: 0,
      })
      setAssets(list)
      setSelected((prev) => {
        if (prev) return list.find((a) => a.id === prev.id) || list[0] || null
        return list[0] || null
      })
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    }
  }

  useEffect(() => {
    refresh()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mediaType, origin])

  const previewUrl = useMemo(() => {
    if (!selected) return null
    return `/api/assets/${selected.id}/content`
  }, [selected])

  const selectedMetadataText = useMemo(() => {
    if (!selected) return ''
    const meta = selected.metadata || {}
    if (Object.keys(meta).length === 0) return ''
    return JSON.stringify(meta, null, 2)
  }, [selected])

  return (
    <div className="grid2 pageAssets" style={{ gridTemplateColumns: '1fr 1fr' }}>
      <section className="panel">
        <div className="panelHeader panelHeaderStack">
          <div className="panelTitle">资产</div>
        </div>
        <div className="panelBody">
          <div className="surfaceSubCard" style={{ marginBottom: 12 }}>
            <div className="labelRow" style={{ marginBottom: 10 }}>
              <div>筛选</div>
              <button type="button" className="btnPillSoft" onClick={refresh}>
                刷新
              </button>
            </div>
            <div className="row">
              <div className="field" style={{ marginBottom: 0 }}>
                <div className="labelRow">
                  <div>类型</div>
                </div>
                <CardSelect
                  label="类型"
                  value={mediaType}
                  onChange={(v) => setMediaType(v)}
                  options={[
                    { value: '', label: '全部' },
                    { value: 'image', label: '图片' },
                    { value: 'video', label: '视频' },
                  ]}
                />
              </div>
              <div className="field" style={{ marginBottom: 0 }}>
                <div className="labelRow">
                  <div>来源</div>
                </div>
                <CardSelect
                  label="来源"
                  value={origin}
                  onChange={(v) => setOrigin(v)}
                  options={[
                    { value: '', label: '全部' },
                    { value: 'upload', label: '上传' },
                    { value: 'generated', label: '生成' },
                  ]}
                />
              </div>
            </div>
          </div>

          <div className="field dropzoneCard">
            <div className="labelRow">
              <div>上传</div>
              <div className="muted">支持 image / video</div>
            </div>
            <button
              type="button"
              className="dropzoneInner dropzoneTrigger"
              onClick={() => fileInputRef.current?.click()}
              aria-label="选择文件上传"
            >
              <div className="dropzoneIcon">
                <span />
              </div>
              <div className="dropzoneText">拖拽文件到这里，或点击选择文件</div>
            </button>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*,video/*"
              hidden
              onChange={async (e) => {
                const f = e.target.files?.[0]
                if (!f) return
                setError(null)
                try {
                  await api.uploadAsset(f)
                  await refresh()
                } catch (err) {
                  setError(err instanceof Error ? err.message : String(err))
                } finally {
                  e.currentTarget.value = ''
                }
              }}
            />
          </div>

          {error ? (
            <div className="statusPill danger" style={{ marginBottom: 12 }}>
              <span className="statusDot statusDotErr" />
              <span>{error}</span>
            </div>
          ) : null}

          <div className="labelRow" style={{ marginBottom: 8 }}>
            <div>缩略图预览</div>
            <div>{assets.length} 项</div>
          </div>
          {assets.length > 0 ? (
            <div className="assetGallery">
              {assets.map((a) => {
                const thumbUrl = `/api/assets/${a.id}/content`
                const videoThumbUrl = `${thumbUrl}#t=0.1`
                const active = selected?.id === a.id
                const sourceModelLabel = a.source_model_name || a.source_model_id
                return (
                  <button
                    key={a.id}
                    type="button"
                    className={`assetThumbBtn${active ? ' assetThumbBtnActive' : ''}`}
                    onClick={() => setSelected(a)}
                    title={a.id}
                  >
                    {active ? <div className="assetThumbCornerTag">已选中</div> : null}
                    <div className="assetThumbFrame">
                      {a.media_type === 'image' ? (
                        <img className="assetThumbImg" src={thumbUrl} alt={a.id} loading="lazy" />
                      ) : (
                        <video
                          className="assetThumbImg"
                          src={videoThumbUrl}
                          muted
                          playsInline
                          preload="metadata"
                          aria-label={`${a.id} 视频缩略图`}
                        />
                      )}
                      <div className="assetThumbBadge">{a.media_type === 'image' ? '图片' : '视频'}</div>
                    </div>
                    <div className="assetThumbMeta">
                      <div className="assetThumbId">{a.id.slice(0, 10)}</div>
                      <div className="assetThumbSub">
                        {a.origin}
                        {a.origin === 'generated' && sourceModelLabel ? ` · ${sourceModelLabel}` : ''}
                        {' · '}
                        {formatDateText(a.created_at)}
                      </div>
                    </div>
                  </button>
                )
              })}
            </div>
          ) : (
            <div className="muted">暂无资产</div>
          )}
        </div>
      </section>

      <section className="panel">
        <div className="panelHeader panelHeaderInline">预览</div>
        <div className="panelBody">
          {selected ? (
            <>
              <div className="statusPill" style={{ marginBottom: 12 }}>
                <span className="statusDot statusDotOk" />
                <span>
                  {selected.media_type} · {selected.origin} · {selected.id.slice(0, 8)}
                </span>
              </div>
              <div className="preview previewCard" style={{ minHeight: 360 }}>
                {previewUrl ? (
                  selected.media_type === 'video' ? (
                    <video className="previewMedia" src={previewUrl} controls />
                  ) : (
                    <img className="previewMedia" src={previewUrl} alt={selected.id} />
                  )
                ) : null}
              </div>
              <div className="assetDetailGrid" style={{ marginBottom: 12 }}>
                <div className="assetDetailItem assetDetailItemPrimary">
                  <div className="assetDetailKey">ID</div>
                  <div className="assetDetailValue mono">{selected.id}</div>
                </div>
                <div className="assetDetailItem assetDetailItemPrimary">
                  <div className="assetDetailKey">类型</div>
                  <div className="assetDetailValue">{selected.media_type}</div>
                </div>
                <div className="assetDetailItem">
                  <div className="assetDetailKey">来源</div>
                  <div className="assetDetailValue">{selected.origin}</div>
                </div>
                <div className="assetDetailItem">
                  <div className="assetDetailKey">MIME</div>
                  <div className="assetDetailValue mono">{selected.mime_type}</div>
                </div>
                <div className="assetDetailItem">
                  <div className="assetDetailKey">大小</div>
                  <div className="assetDetailValue">{formatBytes(selected.size_bytes)}</div>
                </div>
                <div className="assetDetailItem">
                  <div className="assetDetailKey">尺寸</div>
                  <div className="assetDetailValue">{formatDims(selected)}</div>
                </div>
                <div className="assetDetailItem">
                  <div className="assetDetailKey">时长</div>
                  <div className="assetDetailValue">
                    {selected.duration_seconds != null ? `${selected.duration_seconds}s` : '-'}
                  </div>
                </div>
                <div className="assetDetailItem">
                  <div className="assetDetailKey">创建时间</div>
                  <div className="assetDetailValue">{formatDateText(selected.created_at)}</div>
                </div>
                <div className="assetDetailItem">
                  <div className="assetDetailKey">文件路径</div>
                  <div className="assetDetailValue mono">{selected.file_path || '-'}</div>
                </div>
                <div className="assetDetailItem">
                  <div className="assetDetailKey">源任务</div>
                  <div className="assetDetailValue mono">{selected.source_job_id || '-'}</div>
                </div>
                <div className="assetDetailItem">
                  <div className="assetDetailKey">生成模型</div>
                  <div className="assetDetailValue">
                    {selected.source_model_name || selected.source_model_id || '-'}
                  </div>
                </div>
                <div className="assetDetailItem">
                  <div className="assetDetailKey">父资产</div>
                  <div className="assetDetailValue mono">{selected.parent_asset_id || '-'}</div>
                </div>
              </div>
              {selectedMetadataText ? (
                <div className="field codeCard" style={{ marginBottom: 12 }}>
                  <div className="labelRow">
                    <div>Metadata</div>
                  </div>
                  <textarea className="codeArea" readOnly value={selectedMetadataText} style={{ minHeight: 90 }} />
                </div>
              ) : null}
              <div className="row actionBar">
                <a href={previewUrl || '#'} download style={{ flex: 1 }}>
                  <button type="button" style={{ width: '100%' }} disabled={!previewUrl}>
                    下载
                  </button>
                </a>
                <button
                  type="button"
                  className="btnPillSoft"
                  onClick={async () => {
                    if (!previewUrl) return
                    try {
                      await navigator.clipboard.writeText(previewUrl)
                    } catch (e) {
                      setError(e instanceof Error ? e.message : String(e))
                    }
                  }}
                  disabled={!previewUrl}
                >
                  复制链接
                </button>
              </div>
            </>
          ) : (
            <div className="emptyState emptyStateTall">
              <div className="emptyStateIcon" aria-hidden>
                <span />
              </div>
              <div className="emptyStateTitle">未选择资产</div>
              <div className="emptyStateText">从左侧缩略图列表选择一个资产以查看预览与元信息。</div>
            </div>
          )}
        </div>
      </section>
    </div>
  )
}
