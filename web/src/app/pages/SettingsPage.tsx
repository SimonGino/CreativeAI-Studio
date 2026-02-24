import { useEffect, useState } from 'react'

import { api } from '../api/client'
import type { AuthMode, Settings } from '../api/types'
import { CardSelect } from '../components/CardSelect'

export function SettingsPage() {
  const [settings, setSettings] = useState<Settings | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const [testing, setTesting] = useState(false)
  const [testResult, setTestResult] = useState<Record<string, { ok: boolean; error?: string }> | null>(null)

  const [defaultAuthMode, setDefaultAuthMode] = useState<AuthMode>('api_key')
  const [googleApiKey, setGoogleApiKey] = useState<string>('')
  const [vertexProjectId, setVertexProjectId] = useState<string>('')
  const [vertexLocation, setVertexLocation] = useState<string>('')
  const [vertexGcsBucket, setVertexGcsBucket] = useState<string>('')

  async function refresh() {
    setError(null)
    try {
      const s = await api.getSettings()
      setSettings(s)
      setDefaultAuthMode(s.default_auth_mode)
      setVertexProjectId(s.vertex_project_id || '')
      setVertexLocation(s.vertex_location || '')
      setVertexGcsBucket(s.vertex_gcs_bucket || '')
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    }
  }

  useEffect(() => {
    refresh()
  }, [])

  async function onSave() {
    setSaving(true)
    setError(null)
    try {
      const payload: Record<string, unknown> = {
        default_auth_mode: defaultAuthMode,
        vertex_project_id: vertexProjectId || null,
        vertex_location: vertexLocation || null,
        vertex_gcs_bucket: vertexGcsBucket || null,
      }
      if (googleApiKey.trim()) payload.google_api_key = googleApiKey.trim()
      const next = await api.putSettings(payload)
      setSettings(next)
      setGoogleApiKey('')
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setSaving(false)
    }
  }

  async function onTest() {
    setTesting(true)
    setError(null)
    try {
      const r = await api.testSettings()
      setTestResult(r)
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setTesting(false)
    }
  }

  return (
    <div className="grid2" style={{ gridTemplateColumns: '1fr 1fr' }}>
      <section className="panel">
        <div className="panelHeader">设置</div>
        <div className="panelBody">
          {error ? (
            <div className="statusPill danger" style={{ marginBottom: 12 }}>
              <span className="statusDot statusDotErr" />
              <span>{error}</span>
            </div>
          ) : null}

          <div className="field">
            <div className="labelRow">
              <div>默认鉴权模式</div>
            </div>
            <CardSelect
              label="默认鉴权模式"
              value={defaultAuthMode}
              onChange={(v) => setDefaultAuthMode(v as AuthMode)}
              options={[
                { value: 'api_key', label: 'API Key' },
                { value: 'vertex', label: 'Vertex' },
              ]}
            />
          </div>

          <div className="field">
            <div className="labelRow">
              <div>Google API Key（可选）</div>
              <div className="muted">{settings?.google_api_key_present ? '已保存' : '未保存'}</div>
            </div>
            <input
              type="password"
              value={googleApiKey}
              onChange={(e) => setGoogleApiKey(e.target.value)}
              placeholder="粘贴后保存（本机明文存储，MVP）"
            />
          </div>

          <div className="panel" style={{ marginTop: 12 }}>
            <div className="panelHeader">Vertex</div>
            <div className="panelBody">
              <div className="field">
                <div className="labelRow">
                  <div>Service Account JSON</div>
                  <div className="muted">{settings?.vertex_sa_present ? '已上传' : '未上传'}</div>
                </div>
                <input
                  type="file"
                  accept="application/json"
                  onChange={async (e) => {
                    const f = e.target.files?.[0]
                    if (!f) return
                    setError(null)
                    try {
                      await api.uploadVertexSa(f)
                      await refresh()
                    } catch (err) {
                      setError(err instanceof Error ? err.message : String(err))
                    } finally {
                      e.currentTarget.value = ''
                    }
                  }}
                />
              </div>

              <div className="row">
                <div className="field">
                  <div className="labelRow">
                    <div>Project ID</div>
                  </div>
                  <input value={vertexProjectId} onChange={(e) => setVertexProjectId(e.target.value)} />
                </div>
                <div className="field">
                  <div className="labelRow">
                    <div>Location</div>
                  </div>
                  <input value={vertexLocation} onChange={(e) => setVertexLocation(e.target.value)} placeholder="例如 us-central1" />
                </div>
              </div>

              <div className="field">
                <div className="labelRow">
                  <div>VERTEX_GCS_BUCKET</div>
                  <div className="muted">不含 gs://</div>
                </div>
                <input value={vertexGcsBucket} onChange={(e) => setVertexGcsBucket(e.target.value)} />
              </div>
            </div>
          </div>

          <div className="row" style={{ marginTop: 12 }}>
            <button type="button" className="btnPrimary" onClick={onSave} disabled={saving}>
              {saving ? '保存中…' : '保存'}
            </button>
            <button type="button" onClick={onTest} disabled={testing}>
              {testing ? '测试中…' : '测试连接'}
            </button>
          </div>
        </div>
      </section>

      <section className="panel">
        <div className="panelHeader">状态</div>
        <div className="panelBody">
          <div className="field">
            <div className="labelRow">
              <div>当前设置</div>
              <button type="button" onClick={refresh}>
                刷新
              </button>
            </div>
            <textarea readOnly value={settings ? JSON.stringify(settings, null, 2) : ''} />
          </div>

          <div className="field">
            <div className="labelRow">
              <div>测试结果</div>
            </div>
            <textarea readOnly value={testResult ? JSON.stringify(testResult, null, 2) : ''} />
          </div>
        </div>
      </section>
    </div>
  )
}
