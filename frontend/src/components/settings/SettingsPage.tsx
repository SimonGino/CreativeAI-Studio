import { useState } from 'react';
import { Eye, EyeOff, Save, Plug, Loader2, ArrowLeft } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { cn } from '@/lib/utils';
import { getSettings, updateSettings } from '@/lib/api';

export function SettingsPage() {
  const navigate = useNavigate();
  const [geminiApiKey, setGeminiApiKey] = useState('');
  const [showApiKey, setShowApiKey] = useState(false);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const handleSave = async () => {
    setSaving(true);
    setMessage(null);
    try {
      await updateSettings({ gemini_api_key: geminiApiKey || undefined });
      setMessage({ type: 'success', text: 'Settings saved successfully.' });
      setGeminiApiKey('');
    } catch {
      setMessage({ type: 'error', text: 'Failed to save settings.' });
    } finally {
      setSaving(false);
    }
  };

  const handleTestConnection = async () => {
    setTesting(true);
    setMessage(null);
    try {
      const s = await getSettings();
      if (s.gemini_api_key_configured || s.vertex_ai_configured) {
        setMessage({ type: 'success', text: 'Connection OK.' });
      } else {
        setMessage({ type: 'error', text: 'No API key or service account configured.' });
      }
    } catch {
      setMessage({ type: 'error', text: 'Connection failed.' });
    } finally {
      setTesting(false);
    }
  };

  return (
    <div className="min-h-screen bg-[var(--bg)] flex items-start justify-center py-16 px-4">
      <div className="w-full max-w-lg space-y-5">
        <div className="flex items-center gap-2.5">
          <button
            onClick={() => navigate('/')}
            className="rounded-md p-1.5 text-[var(--text-tertiary)] hover:bg-[var(--bg-tertiary)]"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <h1 className="text-lg font-semibold text-[var(--text)]">Settings</h1>
        </div>

        {message && (
          <div className={cn(
            'px-3 py-2.5 rounded-[var(--radius)] text-[13px] border',
            message.type === 'success'
              ? 'bg-green-50 text-green-700 border-green-200'
              : 'bg-red-50 text-red-700 border-red-200'
          )}>
            {message.text}
          </div>
        )}

        <div className="rounded-[var(--radius)] border border-[var(--border)] bg-[var(--bg)] p-5 space-y-3">
          <div>
            <h2 className="text-[14px] font-medium text-[var(--text)]">Gemini API</h2>
            <p className="mt-0.5 text-[12px] text-[var(--text-tertiary)]">
              Enter your Google Gemini API key for image and video generation.
            </p>
          </div>
          <div className="space-y-1.5">
            <label className="text-[12px] font-medium text-[var(--text-secondary)]">API Key</label>
            <div className="relative">
              <input
                type={showApiKey ? 'text' : 'password'}
                value={geminiApiKey}
                onChange={(e) => setGeminiApiKey(e.target.value)}
                placeholder="Enter your Gemini API key"
                className="w-full rounded-[var(--radius)] border border-[var(--border)] bg-[var(--bg)] px-3 py-2.5 pr-10 text-[13px] text-[var(--text)] placeholder-[var(--text-placeholder)] outline-none focus:border-[var(--border-hover)]"
              />
              <button
                type="button"
                onClick={() => setShowApiKey(!showApiKey)}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[var(--text-tertiary)] hover:text-[var(--text-secondary)]"
              >
                {showApiKey ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
              </button>
            </div>
          </div>
        </div>

        <div className="rounded-[var(--radius)] border border-[var(--border)] bg-[var(--bg)] p-5 space-y-1.5">
          <h2 className="text-[14px] font-medium text-[var(--text)]">Vertex AI</h2>
          <p className="text-[12px] text-[var(--text-tertiary)] leading-relaxed">
            Set <code className="rounded bg-[var(--bg-secondary)] px-1 py-0.5 text-[11px] text-[var(--text-secondary)]">VERTEX_AI_SERVICE_ACCOUNT_JSON</code> in
            <code className="rounded bg-[var(--bg-secondary)] px-1 py-0.5 text-[11px] text-[var(--text-secondary)]"> .env</code> to the JSON file path.
          </p>
        </div>

        <div className="flex gap-2.5">
          <button
            onClick={handleTestConnection}
            disabled={testing}
            className={cn(
              'flex-1 flex items-center justify-center gap-1.5 rounded-[var(--radius)] py-2.5 text-[13px] font-medium border',
              testing
                ? 'border-[var(--border)] text-[var(--text-placeholder)] cursor-not-allowed'
                : 'border-[var(--border)] text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)] hover:text-[var(--text)]'
            )}
          >
            {testing ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Plug className="w-3.5 h-3.5" />}
            Test Connection
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className={cn(
              'flex-1 flex items-center justify-center gap-1.5 rounded-[var(--radius)] py-2.5 text-[13px] font-medium',
              saving
                ? 'bg-[var(--bg-tertiary)] text-[var(--text-placeholder)] cursor-not-allowed'
                : 'bg-[var(--accent-bg)] text-[var(--accent-text)] hover:opacity-80 active:scale-[0.99]'
            )}
          >
            {saving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
            Save Settings
          </button>
        </div>
      </div>
    </div>
  );
}
