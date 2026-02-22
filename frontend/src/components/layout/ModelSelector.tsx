import { useState, useRef, useEffect } from 'react';
import { ChevronDown, Check } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { ModelOption } from '@/types';

interface ModelSelectorProps {
  models: ModelOption[];
  value: string;
  onChange: (id: string) => void;
  label?: string;
}

export default function ModelSelector({ models, value, onChange, label }: ModelSelectorProps) {
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const selected = models.find((m) => m.id === value);

  useEffect(() => {
    if (!open) return;
    const handler = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [open]);

  return (
    <div ref={containerRef} className="relative">
      {label && (
        <label className="mb-1.5 block text-[12px] font-medium text-[var(--text-secondary)]">{label}</label>
      )}

      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className={cn(
          'flex w-full items-center justify-between rounded-[var(--radius)] border bg-[var(--bg)] px-3 py-2 text-[13px] text-[var(--text)]',
          open ? 'border-[var(--border-hover)]' : 'border-[var(--border)] hover:border-[var(--border-hover)]'
        )}
      >
        <span className="flex items-center gap-2 truncate">
          {selected?.name ?? 'Select model'}
          {selected && (
            <span className="rounded bg-[var(--bg-tertiary)] px-1.5 py-0.5 text-[10px] font-medium text-[var(--text-tertiary)]">
              {selected.provider}
            </span>
          )}
        </span>
        <ChevronDown className={cn('h-3.5 w-3.5 text-[var(--text-tertiary)]', open && 'rotate-180')} />
      </button>

      {open && (
        <ul className="absolute z-50 mt-1 w-full overflow-hidden rounded-[var(--radius)] border border-[var(--border)] bg-[var(--bg)] py-0.5 shadow-lg">
          {models.map((model) => {
            const isActive = model.id === value;
            return (
              <li key={model.id}>
                <button
                  type="button"
                  onClick={() => { onChange(model.id); setOpen(false); }}
                  className={cn(
                    'flex w-full items-center justify-between px-3 py-2 text-[13px]',
                    isActive ? 'bg-[var(--bg-secondary)] text-[var(--text)]' : 'text-[var(--text)] hover:bg-[var(--bg-secondary)]'
                  )}
                >
                  <span className="flex items-center gap-2">
                    {model.name}
                    <span className="rounded bg-[var(--bg-tertiary)] px-1.5 py-0.5 text-[10px] text-[var(--text-tertiary)]">
                      {model.provider}
                    </span>
                  </span>
                  {isActive && <Check className="h-3.5 w-3.5" />}
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
