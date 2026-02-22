import { useState, useCallback, useRef, useEffect, type KeyboardEvent, type ChangeEvent } from 'react';
import { ArrowUp, ImagePlus, ChevronDown, Check, Image, Video } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAppStore } from '@/stores/appStore';
import { IMAGE_MODELS, VIDEO_MODELS, ASPECT_RATIOS } from '@/types';
import type { ModelOption } from '@/types';

interface ChatInputProps {
  onSend: (content: string) => void;
  disabled?: boolean;
}

const MAX_ROWS = 5;

function BottomDropdown({
  items,
  value,
  onChange,
  renderLabel,
}: {
  items: { id: string; label: string }[];
  value: string;
  onChange: (id: string) => void;
  renderLabel: (item: { id: string; label: string } | undefined) => React.ReactNode;
}) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [open]);

  const selected = items.find((i) => i.id === value);

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className={cn(
          'flex items-center gap-1 rounded-md px-2 py-0.5 text-[12px] font-medium',
          open
            ? 'bg-[var(--bg-hover)] text-[var(--text)]'
            : 'text-[var(--text-tertiary)] hover:bg-[var(--bg-tertiary)] hover:text-[var(--text-secondary)]'
        )}
      >
        {renderLabel(selected)}
        <ChevronDown className={cn('h-3 w-3', open && 'rotate-180')} />
      </button>

      {open && (
        <ul className="absolute bottom-full left-0 z-50 mb-1 min-w-[160px] overflow-hidden rounded-[var(--radius)] border border-[var(--border)] bg-[var(--bg)] py-0.5 shadow-lg">
          {items.map((item) => {
            const isActive = item.id === value;
            return (
              <li key={item.id}>
                <button
                  type="button"
                  onClick={() => { onChange(item.id); setOpen(false); }}
                  className={cn(
                    'flex w-full items-center justify-between px-3 py-1.5 text-[12px]',
                    isActive
                      ? 'bg-[var(--bg-secondary)] text-[var(--text)]'
                      : 'text-[var(--text)] hover:bg-[var(--bg-secondary)]'
                  )}
                >
                  {item.label}
                  {isActive && <Check className="h-3 w-3" />}
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}

export default function ChatInput({ onSend, disabled }: ChatInputProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const {
    mediaTab, setMediaTab,
    imageModel, setImageModel,
    videoModel, setVideoModel,
    aspectRatio, setAspectRatio,
  } = useAppStore();

  const currentModels = mediaTab === 'image' ? IMAGE_MODELS : VIDEO_MODELS;
  const currentModel = mediaTab === 'image' ? imageModel : videoModel;
  const setCurrentModel = mediaTab === 'image' ? setImageModel : setVideoModel;

  const modelItems = currentModels.map((m: ModelOption) => ({ id: m.id, label: m.name }));
  const ratioItems = ASPECT_RATIOS.map((r) => ({ id: r, label: r }));

  const handleInput = useCallback((e: ChangeEvent<HTMLTextAreaElement>) => {
    const el = e.target;
    el.style.height = 'auto';
    el.style.height = `${Math.min(el.scrollHeight, 24 * MAX_ROWS)}px`;
  }, []);

  const handleSend = useCallback(() => {
    const value = textareaRef.current?.value.trim();
    if (!value || disabled) return;
    onSend(value);
    if (textareaRef.current) {
      textareaRef.current.value = '';
      textareaRef.current.style.height = 'auto';
    }
  }, [disabled, onSend]);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
    },
    [handleSend],
  );

  return (
    <div className="shrink-0 px-4 pb-4">
      <div className="mx-auto max-w-3xl">
        <div className="overflow-hidden rounded-xl border border-[var(--border)] bg-[var(--bg)] focus-within:border-[var(--border-hover)]">
          <div className="flex items-end gap-2 px-3 py-2.5">
            <button
              type="button"
              className="mb-0.5 shrink-0 rounded-md p-1 text-[var(--text-tertiary)] hover:bg-[var(--bg-tertiary)] hover:text-[var(--text-secondary)]"
            >
              <ImagePlus className="h-4.5 w-4.5" />
            </button>

            <textarea
              ref={textareaRef}
              rows={1}
              placeholder="Describe what you want to create..."
              className="flex-1 resize-none bg-transparent py-1 text-[14px] text-[var(--text)] placeholder-[var(--text-placeholder)] outline-none"
              onChange={handleInput}
              onKeyDown={handleKeyDown}
              disabled={disabled}
            />

            <button
              type="button"
              onClick={handleSend}
              disabled={disabled}
              className={cn(
                'mb-0.5 shrink-0 rounded-lg p-1.5',
                disabled
                  ? 'cursor-not-allowed text-[var(--text-placeholder)]'
                  : 'bg-[var(--accent-bg)] text-[var(--accent-text)] hover:opacity-80 active:scale-95',
              )}
            >
              <ArrowUp className="h-4 w-4" />
            </button>
          </div>

          <div className="flex items-center gap-1.5 border-t border-[var(--border)] px-3 py-1.5">
            <BottomDropdown
              items={modelItems}
              value={currentModel}
              onChange={setCurrentModel}
              renderLabel={(item) => <span>{item?.label ?? 'Model'}</span>}
            />

            <BottomDropdown
              items={ratioItems}
              value={aspectRatio}
              onChange={setAspectRatio}
              renderLabel={(item) => <span>{item?.label ?? 'Ratio'}</span>}
            />

            <div className="ml-auto flex items-center gap-0.5 rounded-md bg-[var(--bg-secondary)] p-0.5">
              {([
                { type: 'image' as const, icon: Image, label: 'Image' },
                { type: 'video' as const, icon: Video, label: 'Video' },
              ]).map(({ type, icon: Icon, label }) => (
                <button
                  key={type}
                  type="button"
                  onClick={() => setMediaTab(type)}
                  className={cn(
                    'flex items-center gap-1 rounded px-2.5 py-0.5 text-[12px] font-medium',
                    mediaTab === type
                      ? 'bg-[var(--bg)] text-[var(--text)] shadow-sm'
                      : 'text-[var(--text-tertiary)] hover:text-[var(--text-secondary)]',
                  )}
                >
                  <Icon className="h-3 w-3" />
                  {label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
