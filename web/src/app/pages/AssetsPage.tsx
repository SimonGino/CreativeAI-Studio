import { useEffect, useMemo, useState } from 'react'

import { api } from '../api/client'
import type { Asset } from '../api/types'
import { CardSelect } from '../components/CardSelect'

export function AssetsPage() {
  const [assets, setAssets] = useState<Asset[]>([])
  const [selected, setSelected] = useState<Asset | null>(null)
  const [mediaType, setMediaType] = useState<string>('')
  const [origin, setOrigin] = useState<string>('')
  const [error, setError] = useState<string | null>(null)

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
      if (selected) {
        const next = list.find((a) => a.id === selected.id) || null
        setSelected(next)
      }
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

  return (
    <div className="grid2" style={{ gridTemplateColumns: '1fr 1fr' }}>
      <section className="panel">
        <div className="panelHeader">资产</div>
        <div className="panelBody">
          <div className="row" style={{ marginBottom: 12 }}>
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

          <div className="field">
            <div className="labelRow">
              <div>上传</div>
              <button type="button" onClick={refresh}>
                刷新
              </button>
            </div>
            <input
              type="file"
              accept="image/*,video/*"
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

          <table className="table">
            <thead>
              <tr>
                <th>ID</th>
                <th>类型</th>
                <th>来源</th>
                <th>时间</th>
              </tr>
            </thead>
            <tbody>
              {assets.map((a) => (
                <tr
                  key={a.id}
                  style={{ cursor: 'pointer', background: selected?.id === a.id ? 'var(--rowSelectedBg)' : 'transparent' }}
                  onClick={() => setSelected(a)}
                >
                  <td style={{ fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace' }}>{a.id.slice(0, 10)}</td>
                  <td>{a.media_type}</td>
                  <td>{a.origin}</td>
                  <td>{a.created_at}</td>
                </tr>
              ))}
              {assets.length === 0 ? (
                <tr>
                  <td colSpan={4} className="muted">
                    暂无资产
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </section>

      <section className="panel">
        <div className="panelHeader">预览</div>
        <div className="panelBody">
          {selected ? (
            <>
              <div className="statusPill" style={{ marginBottom: 12 }}>
                <span className="statusDot statusDotOk" />
                <span>
                  {selected.media_type} · {selected.origin} · {selected.id.slice(0, 8)}
                </span>
              </div>
              <div className="preview" style={{ minHeight: 360 }}>
                {previewUrl ? (
                  selected.media_type === 'video' ? (
                    <video className="previewMedia" src={previewUrl} controls />
                  ) : (
                    <img className="previewMedia" src={previewUrl} alt={selected.id} />
                  )
                ) : null}
              </div>
              <div className="row">
                <a href={previewUrl || '#'} download style={{ flex: 1 }}>
                  <button type="button" style={{ width: '100%' }} disabled={!previewUrl}>
                    下载
                  </button>
                </a>
                <button
                  type="button"
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
            <div className="muted">从左侧选择一个资产以预览。</div>
          )}
        </div>
      </section>
    </div>
  )
}
