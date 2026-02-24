import { useCallback, useEffect, useMemo, useState } from 'react'

import { api } from '../api/client'
import type { Job, ModelInfo } from '../api/types'
import { providerLogoSrc } from '../ui/logo'

export function HistoryPage() {
  const [jobs, setJobs] = useState<Job[]>([])
  const [selected, setSelected] = useState<Job | null>(null)
  const [models, setModels] = useState<ModelInfo[]>([])
  const [error, setError] = useState<string | null>(null)

  const refresh = useCallback(async (selectedId?: string) => {
    try {
      const list = await api.listJobs({ limit: 50, offset: 0 })
      setJobs(list)
      if (selectedId) {
        const next = await api.getJob(selectedId)
        setSelected(next)
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    }
  }, [])

  useEffect(() => {
    let canceled = false
    async function bootstrap() {
      try {
        const [m, j] = await Promise.all([api.getModels(), api.listJobs({ limit: 50, offset: 0 })])
        if (canceled) return
        setModels(m)
        setJobs(j)
      } catch (e) {
        if (canceled) return
        setError(e instanceof Error ? e.message : String(e))
      }
    }
    bootstrap()
    return () => {
      canceled = true
    }
  }, [])

  const selectedModel = useMemo(() => {
    if (!selected) return null
    return models.find((m) => m.model_id === selected.model_id) || null
  }, [models, selected])

  const rawOutputs = Array.isArray(selected?.result?.outputs)
    ? selected.result.outputs.filter((o) => !!o && typeof o.asset_id === 'string')
    : []
  const fallbackOutputAssetId = (selected?.result?.output_asset_id as string | undefined) || null
  const normalizedOutputs =
    rawOutputs.length > 0
      ? rawOutputs
      : fallbackOutputAssetId
        ? [{ asset_id: fallbackOutputAssetId, media_type: selected?.job_type?.startsWith('video') ? 'video' : 'image' }]
        : []
  const primaryOutput = normalizedOutputs[0] || null
  const outputUrl = primaryOutput ? `/api/assets/${primaryOutput.asset_id}/content` : null
  const isVideoOut = outputUrl && (primaryOutput?.media_type === 'video' || selected?.job_type?.startsWith('video'))
  const imageOutputUrls = normalizedOutputs
    .filter((o) => (o.media_type || 'image') === 'image')
    .map((o) => ({ assetId: o.asset_id, url: `/api/assets/${o.asset_id}/content` }))

  const canCancel = selected && (selected.status === 'queued' || selected.status === 'running')

  const statusText = useMemo(() => {
    if (!selected) return null
    const modelText = selectedModel?.display_name ? `${selectedModel.display_name} · ${selected.model_id}` : selected.model_id
    return `${selected.status} · ${selected.job_type} · ${modelText}`
  }, [selected, selectedModel])

  return (
    <div className="grid2" style={{ gridTemplateColumns: '1fr 1fr' }}>
      <section className="panel">
        <div className="panelHeader">历史</div>
        <div className="panelBody">
          <div className="row" style={{ marginBottom: 12 }}>
            <button
              type="button"
              onClick={async () => {
                setError(null)
                await refresh(selected?.id)
              }}
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

          <table className="table">
            <thead>
              <tr>
                <th>ID</th>
                <th>类型</th>
                <th>状态</th>
                <th>时间</th>
              </tr>
            </thead>
            <tbody>
              {jobs.map((j) => (
                <tr
                  key={j.id}
                  style={{ cursor: 'pointer', background: selected?.id === j.id ? 'var(--rowSelectedBg)' : 'transparent' }}
                  onClick={async () => {
                    try {
                      const full = await api.getJob(j.id)
                      setSelected(full)
                    } catch (e) {
                      setError(e instanceof Error ? e.message : String(e))
                    }
                  }}
                >
                  <td style={{ fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace' }}>{j.id.slice(0, 10)}</td>
                  <td>{j.job_type}</td>
                  <td>{j.status}</td>
                  <td>{j.created_at}</td>
                </tr>
              ))}
              {jobs.length === 0 ? (
                <tr>
                  <td colSpan={4} className="muted">
                    暂无任务
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </section>

      <section className="panel">
        <div className="panelHeader">详情</div>
        <div className="panelBody">
          {selected ? (
            <>
              <div className="statusPill" style={{ marginBottom: 12 }}>
                <span
                  className={[
                    'statusDot',
                    selected.status === 'succeeded'
                      ? 'statusDotOk'
                      : selected.status === 'failed'
                        ? 'statusDotErr'
                        : selected.status === 'running'
                          ? 'statusDotWarn'
                          : '',
                  ].join(' ')}
                />
                <span>{statusText}</span>
              </div>

              {selectedModel?.provider_id ? (
                <div className="providerBadge" style={{ marginBottom: 12 }} title={selectedModel.provider_id}>
                  <img
                    className="providerLogo"
                    src={providerLogoSrc(selectedModel.provider_id)}
                    alt={selectedModel.provider_id}
                  />
                  <span>{selectedModel.provider_id}</span>
                </div>
              ) : null}

              <div className="row" style={{ marginBottom: 12 }}>
                <button
                  type="button"
                  onClick={async () => {
                    try {
                      if (!selected) return
                      setError(null)
                      await api.cloneJob(selected.id, {})
                      await refresh(selected.id)
                    } catch (e) {
                      setError(e instanceof Error ? e.message : String(e))
                    }
                  }}
                >
                  克隆再跑
                </button>
                <button
                  type="button"
                  onClick={async () => {
                    try {
                      if (!selected) return
                      await api.cancelJob(selected.id)
                      const next = await api.getJob(selected.id)
                      setSelected(next)
                    } catch (e) {
                      setError(e instanceof Error ? e.message : String(e))
                    }
                  }}
                  disabled={!canCancel}
                >
                  取消
                </button>
              </div>

              {selected.error_message ? (
                <div className="statusPill danger" style={{ marginBottom: 12 }}>
                  <span className="statusDot statusDotErr" />
                  <span>{selected.error_message}</span>
                </div>
              ) : null}

              <div className="field">
                <div className="labelRow">
                  <div>参数</div>
                </div>
                <textarea readOnly value={JSON.stringify(selected.params, null, 2)} />
              </div>

              <div className="field">
                <div className="labelRow">
                  <div>关联资产</div>
                </div>
                <textarea readOnly value={JSON.stringify(selected.job_assets || [], null, 2)} />
              </div>

              <div className="panel" style={{ marginTop: 12 }}>
                <div className="panelHeader">输出预览</div>
                <div className="panelBody">
                  <div className="preview" style={{ minHeight: 300 }}>
                    {outputUrl ? (
                      isVideoOut ? (
                        <video className="previewMedia" src={outputUrl} controls />
                      ) : imageOutputUrls.length > 1 ? (
                        <div style={{ width: '100%', display: 'grid', gap: 10, gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))' }}>
                          {imageOutputUrls.map((item, idx) => (
                            <div key={item.assetId} style={{ display: 'grid', gap: 6 }}>
                              <img className="previewMedia" src={item.url} alt={`output-${idx + 1}`} />
                              <div className="muted" style={{ textAlign: 'center' }}>
                                输出 #{idx + 1}
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <img className="previewMedia" src={outputUrl} alt="output" />
                      )
                    ) : (
                      <div className="muted">暂无输出</div>
                    )}
                  </div>
                </div>
              </div>
            </>
          ) : (
            <div className="muted">从左侧选择一个任务查看详情。</div>
          )}
        </div>
      </section>
    </div>
  )
}
