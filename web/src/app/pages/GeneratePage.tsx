import { useEffect, useMemo, useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'

import { api } from '../api/client'
import type { Job, ModelInfo, Settings } from '../api/types'
import { CardSelect } from '../components/CardSelect'
import { ImageAssetPickerModal } from '../components/ImageAssetPickerModal'
import { ModelSelect } from '../components/ModelSelect'

type JobType = 'image.generate' | 'video.generate'

export function GeneratePage() {
  const [searchParams] = useSearchParams()
  const mode = searchParams.get('mode') === 'video' ? 'video' : 'image'
  const jobType: JobType = mode === 'video' ? 'video.generate' : 'image.generate'

  const [models, setModels] = useState<ModelInfo[]>([])
  const [settings, setSettings] = useState<Settings | null>(null)
  const [error, setError] = useState<string | null>(null)

  const defaultAuthMode = settings?.default_auth_mode || 'api_key'
  const vertexReady =
    !!settings?.vertex_sa_present && !!settings?.vertex_project_id && !!settings?.vertex_location

  const [modelId, setModelId] = useState<string>('')
  const [prompt, setPrompt] = useState<string>('')
  const [aspectRatio, setAspectRatio] = useState<string>('auto')

  const [imageSize, setImageSize] = useState<string>('1k')
  const [durationSeconds, setDurationSeconds] = useState<number>(5)

  const [referenceAssetId, setReferenceAssetId] = useState<string | null>(null)
  const referenceFileRef = useRef<HTMLInputElement | null>(null)
  const [referencePickerOpen, setReferencePickerOpen] = useState(false)
  const [startAssetId, setStartAssetId] = useState<string | null>(null)
  const startFileRef = useRef<HTMLInputElement | null>(null)
  const [startPickerOpen, setStartPickerOpen] = useState(false)
  const [endAssetId, setEndAssetId] = useState<string | null>(null)
  const endFileRef = useRef<HTMLInputElement | null>(null)
  const [endPickerOpen, setEndPickerOpen] = useState(false)

  const [job, setJob] = useState<Job | null>(null)
  const [creating, setCreating] = useState(false)

  useEffect(() => {
    let canceled = false
    async function run() {
      try {
        const [m, s] = await Promise.all([api.getModels(), api.getSettings()])
        if (canceled) return
        setModels(m)
        setSettings(s)
      } catch (e) {
        if (canceled) return
        setError(e instanceof Error ? e.message : String(e))
      }
    }
    run()
    return () => {
      canceled = true
    }
  }, [])

  const filteredModels = useMemo(() => {
    const mediaType = mode === 'video' ? 'video' : 'image'
    return models.filter((m) => m.media_type === mediaType)
  }, [models, mode])

  const selectedModel = useMemo(() => {
    return filteredModels.find((m) => m.model_id === modelId) || null
  }, [filteredModels, modelId])

  useEffect(() => {
    if (filteredModels.length === 0) return
    const exists = filteredModels.some((m) => m.model_id === modelId)
    if (!modelId || !exists) setModelId(filteredModels[0].model_id)
  }, [filteredModels, modelId])

  useEffect(() => {
    const id = job?.id
    if (!id) return
    if (job.status !== 'queued' && job.status !== 'running') return

    const t = window.setInterval(async () => {
      try {
        const next = await api.getJob(id)
        setJob(next)
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e))
      }
    }, 1000)
    return () => window.clearInterval(t)
  }, [job?.id, job?.status])

  async function uploadAndSet(
    file: File,
    setter: (id: string | null) => void,
    expectedMediaType: 'image' | 'video',
  ) {
    setError(null)
    try {
      const a = await api.uploadAsset(file)
      if (a.media_type !== expectedMediaType) {
        setError(`上传类型不匹配：期望 ${expectedMediaType}，实际 ${a.media_type}`)
        return
      }
      setter(a.id)
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    }
  }

  async function onCreate() {
    setError(null)
    setCreating(true)
    try {
      if (!settings) {
        throw new Error('设置未加载，请稍候重试。')
      }
      if (defaultAuthMode === 'api_key' && !settings?.google_api_key_present) {
        throw new Error('默认鉴权为 API Key：请先在“设置”里保存 Google API Key。')
      }
      if (defaultAuthMode === 'vertex' && !vertexReady) {
        throw new Error('默认鉴权为 Vertex：请先在“设置”里上传 Service Account JSON，并填写 project/location。')
      }

      const params: Record<string, unknown> = {
        prompt,
        aspect_ratio: aspectRatio,
      }
      if (jobType === 'image.generate') {
        params.image_size = imageSize
        if (referenceAssetId) params.reference_image_asset_id = referenceAssetId
      }
      if (jobType === 'video.generate') {
        params.duration_seconds = durationSeconds
        if (startAssetId) params.start_image_asset_id = startAssetId
        if (endAssetId) params.end_image_asset_id = endAssetId
      }

      const payload: Record<string, unknown> = {
        job_type: jobType,
        model_id: modelId,
        params,
      }

      const created = await api.createJob(payload)
      setJob(created)
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setCreating(false)
    }
  }

  const outputAssetId = (job?.result?.output_asset_id as string | undefined) || null
  const outputUrl = outputAssetId ? `/api/assets/${outputAssetId}/content` : null
  const isVideoOut = outputUrl && job?.job_type?.startsWith('video')

  return (
    <div className="grid2">
      <section className="panel">
        <div className="panelHeader">
          生成{' '}
          {settings?.default_auth_mode ? (
            <span className="statusPill" style={{ marginLeft: 10 }}>
              <span className="statusDot statusDotOk" />
              <span>默认鉴权：{settings.default_auth_mode}</span>
            </span>
          ) : null}
        </div>
        <div className="panelBody">
          <div className="field">
            <div className="labelRow">
              <div>模型</div>
            </div>
            <ModelSelect
              label="模型"
              models={filteredModels}
              value={modelId}
              onChange={(id) => setModelId(id)}
            />
          </div>

          <div className="field">
            <div className="labelRow">
              <div>提示词</div>
              <div className="muted">{selectedModel?.prompt_max_chars ? `≤ ${selectedModel.prompt_max_chars}` : ''}</div>
            </div>
            <textarea value={prompt} onChange={(e) => setPrompt(e.target.value)} placeholder="写点清晰具体的描述…" />
          </div>

          <div className="row">
            <div className="field">
              <div className="labelRow">
                <div>长宽比</div>
              </div>
              <CardSelect
                label="长宽比"
                value={aspectRatio}
                onChange={(v) => setAspectRatio(v)}
                options={(selectedModel?.aspect_ratios || ['auto', '1:1', '16:9', '9:16']).map((r) => ({
                  value: r,
                  label: r,
                }))}
              />
            </div>

            {jobType === 'image.generate' ? (
              <div className="field">
                <div className="labelRow">
                  <div>分辨率</div>
                </div>
                <CardSelect
                  label="分辨率"
                  value={imageSize}
                  onChange={(v) => setImageSize(v)}
                  options={(selectedModel?.resolution_presets || ['1k']).map((r) => ({
                    value: r,
                    label: r,
                  }))}
                />
              </div>
            ) : null}

            {jobType === 'video.generate' ? (
              <div className="field">
                <div className="labelRow">
                  <div>时长（秒）</div>
                </div>
                <CardSelect
                  label="时长（秒）"
                  value={String(durationSeconds)}
                  onChange={(v) => setDurationSeconds(Number(v))}
                  options={(selectedModel?.duration_seconds || [5, 10]).map((s) => ({
                    value: String(s),
                    label: String(s),
                  }))}
                />
              </div>
            ) : null}
          </div>

          {jobType === 'image.generate' ? (
            <div className="field">
              <div className="labelRow">
                <div>参考图（可选）</div>
                <div className="muted">{referenceAssetId ? `asset: ${referenceAssetId}` : ''}</div>
              </div>

              <div className="row">
                <button
                  type="button"
                  onClick={() => referenceFileRef.current?.click()}
                  disabled={creating}
                >
                  上传参考图
                </button>
                <button type="button" onClick={() => setReferencePickerOpen(true)} disabled={creating}>
                  从资产选择
                </button>
              </div>

              <input
                ref={referenceFileRef}
                type="file"
                accept="image/*"
                style={{ display: 'none' }}
                onChange={(e) => {
                  const f = e.target.files?.[0]
                  if (f) uploadAndSet(f, setReferenceAssetId, 'image')
                  e.currentTarget.value = ''
                }}
              />

              {referenceAssetId ? (
                <div className="assetInlinePreview" style={{ marginTop: 10 }}>
                  <img
                    className="assetInlineThumb"
                    src={`/api/assets/${referenceAssetId}/content`}
                    alt="reference"
                    loading="lazy"
                  />
                  <div className="assetInlineMeta">
                    <div className="assetInlineId">{referenceAssetId}</div>
                    <div className="muted">已选择参考图</div>
                  </div>
                  <button type="button" onClick={() => setReferenceAssetId(null)} style={{ flex: '0 0 auto' }}>
                    清除
                  </button>
                </div>
              ) : (
                <div className="muted">未选择参考图</div>
              )}

              <div className="muted">
                参考图跟随默认鉴权：{defaultAuthMode === 'vertex' ? 'Vertex（Imagen edit）' : 'API Key（Gemini 多模态）'}
              </div>
              {defaultAuthMode === 'vertex' && !vertexReady ? (
                <div className="statusPill danger" style={{ marginTop: 8 }}>
                  <span className="statusDot statusDotErr" />
                  <span>未配置 Vertex：请到“设置”完善后再使用参考图。</span>
                </div>
              ) : null}

              <ImageAssetPickerModal
                open={referencePickerOpen}
                title="选择参考图"
                selectedAssetId={referenceAssetId}
                onSelect={(a) => setReferenceAssetId(a.id)}
                onClose={() => setReferencePickerOpen(false)}
              />
            </div>
          ) : null}

          {jobType === 'video.generate' ? (
            <div className="row">
              <div className="field">
                <div className="labelRow">
                  <div>首帧（可选）</div>
                </div>

                <div className="row">
                  <button
                    type="button"
                    onClick={() => startFileRef.current?.click()}
                    disabled={creating}
                  >
                    上传首帧
                  </button>
                  <button type="button" onClick={() => setStartPickerOpen(true)} disabled={creating}>
                    从资产选择
                  </button>
                </div>

                <input
                  ref={startFileRef}
                  type="file"
                  accept="image/*"
                  style={{ display: 'none' }}
                  onChange={(e) => {
                    const f = e.target.files?.[0]
                    if (f) uploadAndSet(f, setStartAssetId, 'image')
                    e.currentTarget.value = ''
                  }}
                />

                {startAssetId ? (
                  <div className="assetInlinePreview" style={{ marginTop: 10 }}>
                    <img
                      className="assetInlineThumb"
                      src={`/api/assets/${startAssetId}/content`}
                      alt="start"
                      loading="lazy"
                    />
                    <div className="assetInlineMeta">
                      <div className="assetInlineId">{startAssetId}</div>
                      <div className="muted">已选择首帧</div>
                    </div>
                    <button type="button" onClick={() => setStartAssetId(null)} style={{ flex: '0 0 auto' }}>
                      清除
                    </button>
                  </div>
                ) : (
                  <div className="muted">未选择首帧</div>
                )}

                <ImageAssetPickerModal
                  open={startPickerOpen}
                  title="选择首帧图片"
                  selectedAssetId={startAssetId}
                  onSelect={(a) => setStartAssetId(a.id)}
                  onClose={() => setStartPickerOpen(false)}
                />
              </div>
              <div className="field">
                <div className="labelRow">
                  <div>尾帧（可选）</div>
                </div>

                <div className="row">
                  <button
                    type="button"
                    onClick={() => endFileRef.current?.click()}
                    disabled={creating}
                  >
                    上传尾帧
                  </button>
                  <button type="button" onClick={() => setEndPickerOpen(true)} disabled={creating}>
                    从资产选择
                  </button>
                </div>

                <input
                  ref={endFileRef}
                  type="file"
                  accept="image/*"
                  style={{ display: 'none' }}
                  onChange={(e) => {
                    const f = e.target.files?.[0]
                    if (f) uploadAndSet(f, setEndAssetId, 'image')
                    e.currentTarget.value = ''
                  }}
                />

                {endAssetId ? (
                  <div className="assetInlinePreview" style={{ marginTop: 10 }}>
                    <img
                      className="assetInlineThumb"
                      src={`/api/assets/${endAssetId}/content`}
                      alt="end"
                      loading="lazy"
                    />
                    <div className="assetInlineMeta">
                      <div className="assetInlineId">{endAssetId}</div>
                      <div className="muted">已选择尾帧</div>
                    </div>
                    <button type="button" onClick={() => setEndAssetId(null)} style={{ flex: '0 0 auto' }}>
                      清除
                    </button>
                  </div>
                ) : (
                  <div className="muted">未选择尾帧</div>
                )}

                <ImageAssetPickerModal
                  open={endPickerOpen}
                  title="选择尾帧图片"
                  selectedAssetId={endAssetId}
                  onSelect={(a) => setEndAssetId(a.id)}
                  onClose={() => setEndPickerOpen(false)}
                />
              </div>
            </div>
          ) : null}

          {error ? (
            <div className="statusPill danger" style={{ marginBottom: 12 }}>
              <span className="statusDot statusDotErr" />
              <span>{error}</span>
            </div>
          ) : null}

          <div className="row">
            <button type="button" className="btnPrimary" onClick={onCreate} disabled={creating}>
              {creating ? '创建中…' : '开始'}
            </button>
            <button
              type="button"
              onClick={async () => {
                if (!job?.id) return
                try {
                  await api.cancelJob(job.id)
                  const next = await api.getJob(job.id)
                  setJob(next)
                } catch (e) {
                  setError(e instanceof Error ? e.message : String(e))
                }
              }}
              disabled={!job || (job.status !== 'queued' && job.status !== 'running')}
            >
              取消
            </button>
          </div>
        </div>
      </section>

      <section className="panel">
        <div className="panelHeader">
          预览{' '}
          {job ? (
            <span className="statusPill" style={{ marginLeft: 10 }}>
              <span
                className={[
                  'statusDot',
                  job.status === 'succeeded'
                    ? 'statusDotOk'
                    : job.status === 'failed'
                      ? 'statusDotErr'
                      : job.status === 'running'
                        ? 'statusDotWarn'
                        : '',
                ].join(' ')}
              />
              <span>
                {job.status} · {job.id.slice(0, 8)}
              </span>
            </span>
          ) : null}
        </div>
        <div className="panelBody">
          <div className="preview">
            {outputUrl ? (
              isVideoOut ? (
                <video className="previewMedia" src={outputUrl} controls />
              ) : (
                <img className="previewMedia" src={outputUrl} alt="output" />
              )
            ) : (
              <div className="muted">暂无输出。创建任务后会在这里显示结果。</div>
            )}
          </div>
          {outputUrl ? (
            <div className="row">
              <a href={outputUrl} download style={{ flex: 1 }}>
                <button type="button" style={{ width: '100%' }}>
                  下载
                </button>
              </a>
              <button
                type="button"
                onClick={async () => {
                  try {
                    await navigator.clipboard.writeText(outputUrl)
                  } catch (e) {
                    setError(e instanceof Error ? e.message : String(e))
                  }
                }}
              >
                复制链接
              </button>
            </div>
          ) : null}
        </div>
      </section>
    </div>
  )
}
