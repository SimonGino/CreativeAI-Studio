import { useEffect, useState } from 'react'

import { api } from '../api/client'
import type { Settings } from '../api/types'

export function SettingsPage() {
  const [settings, setSettings] = useState<Settings | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const [testing, setTesting] = useState(false)
  const [testResult, setTestResult] = useState<Record<string, { ok: boolean; error?: string; duration_ms?: number }> | null>(null)

  const [googleApiKey, setGoogleApiKey] = useState<string>('')
  const [arkApiKey, setArkApiKey] = useState<string>('')

  async function refresh() {
    setError(null)
    try {
      const s = await api.getSettings()
      setSettings(s)
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
      const payload: Record<string, unknown> = { default_auth_mode: 'api_key' }
      if (googleApiKey.trim()) payload.google_api_key = googleApiKey.trim()
      if (arkApiKey.trim()) payload.ark_api_key = arkApiKey.trim()
      const next = await api.putSettings(payload)
      setSettings(next)
      setGoogleApiKey('')
      setArkApiKey('')
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

          <div className="field">
            <div className="labelRow">
              <div>ARK API Key（Doubao， 可选）</div>
              <div className="muted">{settings?.ark_api_key_present ? '已保存' : '未保存'}</div>
            </div>
            <input
              type="password"
              value={arkApiKey}
              onChange={(e) => setArkApiKey(e.target.value)}
              placeholder="粘贴后保存（本机明文存储，MVP）"
            />
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
            {testResult ? (
              <div style={{ display: 'grid', gap: 8 }}>
                {[
                  ['google_api_key', 'Google API Key'],
                  ['ark_api_key', 'ARK API Key'],
                ].map(([key, label]) => {
                  const item = testResult[key]
                  return (
                    <div key={key} className={`statusPill ${item && !item.ok ? 'danger' : ''}`}>
                      <span className={['statusDot', item?.ok ? 'statusDotOk' : 'statusDotErr'].join(' ')} />
                      <span>
                        <strong>{label}</strong>
                        {item ? ` · ${item.ok ? '成功' : '失败'}` : ' · 未返回'}
                        {item?.error ? ` · ${item.error}` : ''}
                      </span>
                    </div>
                  )
                })}
              </div>
            ) : (
              <div className="muted">尚未执行测试</div>
            )}
          </div>

          <div className="field">
            <div className="labelRow">
              <div>测试结果（原始 JSON）</div>
            </div>
            <textarea readOnly value={testResult ? JSON.stringify(testResult, null, 2) : ''} />
          </div>
        </div>
      </section>
    </div>
  )
}
