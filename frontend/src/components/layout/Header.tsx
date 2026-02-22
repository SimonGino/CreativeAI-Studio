import { Link } from 'react-router-dom';
import { Sparkles, Settings, PanelLeft } from 'lucide-react';
import { useAppStore } from '@/stores/appStore';
import { cn } from '@/lib/utils';
import { useI18n } from '@/hooks/useI18n';
import type { UIMode } from '@/types';

const MODE_OPTIONS: { value: UIMode; labelKey: 'mode.chat' | 'mode.studio' }[] = [
  { value: 'chat', labelKey: 'mode.chat' },
  { value: 'studio', labelKey: 'mode.studio' },
];

const LOCALE_OPTIONS = [
  { value: 'zh-CN' as const, labelKey: 'language.zh' as const },
  { value: 'en' as const, labelKey: 'language.en' as const },
];

export default function Header() {
  const { locale, setLocale, t } = useI18n();
  const uiMode = useAppStore((s) => s.uiMode);
  const setUIMode = useAppStore((s) => s.setUIMode);
  const sidebarOpen = useAppStore((s) => s.sidebarOpen);
  const setSidebarOpen = useAppStore((s) => s.setSidebarOpen);

  return (
    <header className="flex h-12 items-center justify-between border-b border-[var(--border)] bg-[var(--bg)] px-4">
      <div className="flex items-center gap-2.5">
        {!sidebarOpen && (
          <button
            onClick={() => setSidebarOpen(true)}
            className="rounded-md p-1.5 text-[var(--text-tertiary)] hover:bg-[var(--bg-tertiary)]"
          >
            <PanelLeft className="h-4 w-4" />
          </button>
        )}
        <Link to="/" className="flex items-center gap-2 text-[var(--text)]">
          <Sparkles className="h-4 w-4" />
          <span className="text-[14px] font-semibold">CreativeAI Studio</span>
        </Link>
      </div>

      <div className="flex items-center gap-0.5 rounded-lg bg-[var(--bg-secondary)] p-0.5">
        {MODE_OPTIONS.map((opt) => (
          <button
            key={opt.value}
            onClick={() => setUIMode(opt.value)}
            className={cn(
              'rounded-md px-4 py-1 text-[13px] font-medium',
              uiMode === opt.value
                ? 'bg-[var(--bg)] text-[var(--text)] shadow-sm'
                : 'text-[var(--text-tertiary)] hover:text-[var(--text-secondary)]'
            )}
          >
            {t(opt.labelKey)}
          </button>
        ))}
      </div>

      <div className="flex items-center gap-2">
        <div className="flex items-center gap-0.5 rounded-lg bg-[var(--bg-secondary)] p-0.5">
          {LOCALE_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              onClick={() => setLocale(opt.value)}
              className={cn(
                'rounded-md px-2.5 py-1 text-[12px] font-medium',
                locale === opt.value
                  ? 'bg-[var(--bg)] text-[var(--text)] shadow-sm'
                  : 'text-[var(--text-tertiary)] hover:text-[var(--text-secondary)]',
              )}
            >
              {t(opt.labelKey)}
            </button>
          ))}
        </div>
        <Link
          to="/settings"
          className="rounded-md p-1.5 text-[var(--text-tertiary)] hover:bg-[var(--bg-tertiary)] hover:text-[var(--text-secondary)]"
        >
          <Settings className="h-4 w-4" />
        </Link>
      </div>
    </header>
  );
}
