import { useEffect, useMemo, useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'

import { api } from '../api/client'
import type { Job, JobOutput, ModelInfo, Settings } from '../api/types'
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

  const [modelId, setModelId] = useState<string>('')
  const [prompt, setPrompt] = useState<string>('')
  const [aspectRatio, setAspectRatio] = useState<string>('auto')

  const [imageSize, setImageSize] = useState<string>('1k')
  const [outputImageCount, setOutputImageCount] = useState<number>(1)
  const [durationSeconds, setDurationSeconds] = useState<number>(5)

  const [referenceAssetIds, setReferenceAssetIds] = useState<string[]>([])
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
  const selectableModels = useMemo(() => filteredModels.filter((m) => !m.coming_soon), [filteredModels])

  const selectedModel = useMemo(() => {
    return filteredModels.find((m) => m.model_id === modelId) || null
  }, [filteredModels, modelId])

  const selectedProviderId = selectedModel?.provider_id || 'google'
  const modelAuthSupport = selectedModel?.auth_support || ['api_key']
  const effectiveAuthMode = modelAuthSupport.includes(defaultAuthMode)
    ? defaultAuthMode
    : (modelAuthSupport[0] || defaultAuthMode)
  const imageResolutionPresets = useMemo(() => {
    if (jobType !== 'image.generate') return []
    const presets = (selectedModel?.resolution_presets || []).map((v) => String(v))
    return presets.length > 0 ? presets : ['1k']
  }, [jobType, selectedModel])
  const supportsSequentialImageGeneration =
    jobType === 'image.generate' && !!selectedModel?.sequential_image_generation_supported
  const maxOutputImagesByModel = Math.max(1, Math.min(5, selectedModel?.max_output_images || 1))
  const maxOutputImagesByTotalLimit =
    selectedModel?.max_total_images != null
      ? Math.max(1, Math.min(5, selectedModel.max_total_images - referenceAssetIds.length))
      : maxOutputImagesByModel
  const maxOutputImageCount = Math.max(1, Math.min(maxOutputImagesByModel, maxOutputImagesByTotalLimit))
  const maxReferenceImages = Math.max(1, selectedModel?.max_reference_images || 1)

  useEffect(() => {
    setOutputImageCount((prev) => Math.max(1, Math.min(prev, maxOutputImageCount)))
  }, [maxOutputImageCount])

  useEffect(() => {
    if (jobType !== 'image.generate') return
    if (imageResolutionPresets.length === 0) return
    if (!imageResolutionPresets.includes(imageSize)) {
      setImageSize(imageResolutionPresets[0])
    }
  }, [jobType, imageResolutionPresets, imageSize])

  useEffect(() => {
    if (filteredModels.length === 0) return
    const current = filteredModels.find((m) => m.model_id === modelId) || null
    if (current && !current.coming_soon) return
    const next = selectableModels[0] || filteredModels[0]
    if (!next) return
    if (modelId !== next.model_id) setModelId(next.model_id)
  }, [filteredModels, selectableModels, modelId])

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

  function appendReferenceAssetId(nextId: string) {
    setReferenceAssetIds((prev) => {
      if (prev.includes(nextId)) return prev
      if (prev.length >= maxReferenceImages) {
        setError(`当前模型最多支持 ${maxReferenceImages} 张参考图。`)
        return prev
      }
      return [...prev, nextId]
    })
  }

  async function onCreate() {
    setError(null)
    setCreating(true)
    try {
      if (!settings) {
        throw new Error('设置未加载，请稍候重试。')
      }
      if (!selectedModel) {
        throw new Error('请先选择模型。')
      }
      if (selectedModel.coming_soon) {
        throw new Error('该模型即将推出，暂不可用。')
      }
      if (effectiveAuthMode === 'api_key' && selectedProviderId === 'google' && !settings.google_api_key_present) {
        throw new Error('该模型使用 Google API Key：请先在“设置”里保存 Google API Key。')
      }
      if (effectiveAuthMode === 'api_key' && selectedProviderId === 'volcengine_ark' && !settings.ark_api_key_present) {
        throw new Error('该模型使用 ARK API Key：请先在“设置”里保存 ARK API Key。')
      }
      const params: Record<string, unknown> = {
        prompt,
        aspect_ratio: aspectRatio,
      }
      if (jobType === 'image.generate') {
        params.image_size = imageSize
        if (selectedProviderId === 'volcengine_ark') params.watermark = false
        if (referenceAssetIds.length > 0) params.reference_image_asset_ids = referenceAssetIds
        if (supportsSequentialImageGeneration && outputImageCount > 1) {
          params.sequential_image_generation = 'auto'
          params.sequential_image_generation_options = { max_images: outputImageCount }
        } else {
          params.sequential_image_generation = 'disabled'
        }
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
        auth: { mode: effectiveAuthMode },
      }

      const created = await api.createJob(payload)
      setJob(created)
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setCreating(false)
    }
  }

  const resultOutputs = Array.isArray(job?.result?.outputs)
    ? job.result.outputs.filter((o): o is JobOutput => !!o && typeof o.asset_id === 'string')
    : []
  const fallbackOutputAssetId = (job?.result?.output_asset_id as string | undefined) || null
  const normalizedOutputs =
    resultOutputs.length > 0
      ? resultOutputs
      : fallbackOutputAssetId
        ? [{ asset_id: fallbackOutputAssetId, media_type: jobType === 'video.generate' ? 'video' : 'image', index: 0 }]
        : []
  const primaryOutput = normalizedOutputs[0] || null
  const outputUrl = primaryOutput ? `/api/assets/${primaryOutput.asset_id}/content` : null
  const isVideoOut = outputUrl && (primaryOutput?.media_type === 'video' || job?.job_type?.startsWith('video'))
  const imageOutputUrls = normalizedOutputs
    .filter((o) => (o.media_type || 'image') === 'image')
    .map((o) => ({ assetId: o.asset_id, url: `/api/assets/${o.asset_id}/content` }))

  return (
    <div className="grid2">
      <section className="panel">
        <div className="panelHeader">生成</div>
        <div className="panelBody">
          <div className="field">
            <div className="labelRow">
              <div>模型</div>
              {selectedModel?.provider_id ? <div className="muted">{selectedModel.provider_id}</div> : null}
            </div>
            <ModelSelect
              label="模型"
              models={filteredModels}
              value={modelId}
              onChange={(id) => setModelId(id)}
            />
            {selectedModel?.coming_soon ? (
              <div className="statusPill" style={{ marginTop: 8 }}>
                <span className="statusDot statusDotWarn" />
                <span>该模型即将推出，当前仅展示，不可选择生成。</span>
              </div>
            ) : null}
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
              <>
                <div className="field">
                  <div className="labelRow">
                    <div>分辨率</div>
                  </div>
                  <CardSelect
                    label="分辨率"
                    value={imageSize}
                    onChange={(v) => setImageSize(v)}
                    options={imageResolutionPresets.map((r) => ({
                      value: r,
                      label: r,
                    }))}
                  />
                </div>
                <div className="field">
                  <div className="labelRow">
                    <div>输出张数</div>
                    <div className="muted">
                      {supportsSequentialImageGeneration ? `1-${maxOutputImageCount}` : '仅 1 张'}
                    </div>
                  </div>
                  <CardSelect
                    label="输出张数"
                    value={String(outputImageCount)}
                    onChange={(v) => setOutputImageCount(Number(v))}
                    options={Array.from(
                      { length: supportsSequentialImageGeneration ? maxOutputImageCount : 1 },
                      (_, i) => String(i + 1),
                    ).map((n) => ({
                      value: n,
                      label: `${n} 张`,
                    }))}
                  />
                </div>
              </>
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
                <div className="muted">
                  最多 {maxReferenceImages} 张
                  {selectedModel?.max_total_images != null ? ` · 输入+输出 ≤ ${selectedModel.max_total_images}` : ''}
                </div>
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
                  if (f) {
                    uploadAndSet(
                      f,
                      (id) => {
                        if (id) appendReferenceAssetId(id)
                      },
                      'image',
                    )
                  }
                  e.currentTarget.value = ''
                }}
              />

              {referenceAssetIds.length === 0 ? (
                <div className="muted">未选择参考图</div>
              ) : (
                <div style={{ display: 'grid', gap: 8, marginTop: 10 }}>
                  {referenceAssetIds.map((refId, idx) => (
                    <div key={refId} className="assetInlinePreview">
                      <img
                        className="assetInlineThumb"
                        src={`/api/assets/${refId}/content`}
                        alt={`reference-${idx + 1}`}
                        loading="lazy"
                      />
                      <div className="assetInlineMeta">
                        <div className="assetInlineId">{refId}</div>
                        <div className="muted">参考图 #{idx + 1}</div>
                      </div>
                      <button
                        type="button"
                        onClick={() => setReferenceAssetIds((prev) => prev.filter((id) => id !== refId))}
                        style={{ flex: '0 0 auto' }}
                      >
                        移除
                      </button>
                    </div>
                  ))}
                  <div className="row">
                    <button type="button" onClick={() => setReferenceAssetIds([])}>
                      清空参考图
                    </button>
                  </div>
                </div>
              )}

              {selectedProviderId === 'volcengine_ark' && !settings?.ark_api_key_present ? (
                <div className="statusPill danger" style={{ marginTop: 8 }}>
                  <span className="statusDot statusDotErr" />
                  <span>未保存 ARK API Key：请到“设置”中配置。</span>
                </div>
              ) : null}

              <ImageAssetPickerModal
                open={referencePickerOpen}
                title="选择参考图"
                selectedAssetId={referenceAssetIds[referenceAssetIds.length - 1] || null}
                onSelect={(a) => appendReferenceAssetId(a.id)}
                onClose={() => setReferencePickerOpen(false)}
              />
            </div>
          ) : null}

          {jobType === 'video.generate' ? (
            <>
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
            </>
          ) : null}

          {error ? (
            <div className="statusPill danger" style={{ marginBottom: 12 }}>
              <span className="statusDot statusDotErr" />
              <span>{error}</span>
            </div>
          ) : null}

          <div className="row">
            <button
              type="button"
              className="btnPrimary"
              onClick={onCreate}
              disabled={creating || !selectedModel || !!selectedModel.coming_soon}
            >
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
              ) : imageOutputUrls.length > 1 ? (
                <div style={{ width: '100%', display: 'grid', gap: 10, gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))' }}>
                  {imageOutputUrls.map((item, idx) => (
                    <a key={item.assetId} href={item.url} target="_blank" rel="noreferrer" style={{ textDecoration: 'none' }}>
                      <div style={{ display: 'grid', gap: 6 }}>
                        <img
                          className="previewMedia"
                          src={item.url}
                          alt={`output-${idx + 1}`}
                          style={{ maxHeight: 220, width: '100%', objectFit: 'cover', borderRadius: 12 }}
                        />
                        <div className="muted" style={{ textAlign: 'center' }}>
                          输出 #{idx + 1}
                        </div>
                      </div>
                    </a>
                  ))}
                </div>
              ) : (
                <img className="previewMedia" src={outputUrl} alt="output" />
              )
            ) : (
              <div className="muted">暂无输出。创建任务后会在这里显示结果。</div>
            )}
          </div>
          {outputUrl ? (
            <div className="row" style={{ flexWrap: 'wrap' }}>
              <a href={outputUrl} download style={{ flex: 1 }}>
                <button type="button" style={{ width: '100%' }}>
                  下载首个输出
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
                复制首图链接
              </button>
            </div>
          ) : null}
        </div>
      </section>
    </div>
  )
}
