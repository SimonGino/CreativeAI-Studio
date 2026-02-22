import { useState } from 'react';
import { Sparkles, Video, ImageIcon, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAppStore } from '@/stores/appStore';
import { useI18n } from '@/hooks/useI18n';
import {
  IMAGE_MODELS,
  VIDEO_MODELS,
  ASPECT_RATIOS,
  VIDEO_DURATIONS,
  type MediaType,
  type ModelOption,
} from '@/types';

interface ParamPanelProps {
  onGenerate: (prompt: string) => void;
  loading: boolean;
  mediaType: MediaType;
}

type VideoTab = 'text-to-video' | 'image-to-video';

export default function ParamPanel({ onGenerate, loading, mediaType }: ParamPanelProps) {
  const { t } = useI18n();
  const [prompt, setPrompt] = useState('');
  const [videoTab, setVideoTab] = useState<VideoTab>('text-to-video');

  const {
    imageModel, setImageModel,
    videoModel, setVideoModel,
    aspectRatio, setAspectRatio,
    duration, setDuration,
  } = useAppStore();

  const models = mediaType === 'image' ? IMAGE_MODELS : VIDEO_MODELS;
  const selectedModel = mediaType === 'image' ? imageModel : videoModel;
  const setSelectedModel = mediaType === 'image' ? setImageModel : setVideoModel;

  const handleGenerate = () => {
    const trimmed = prompt.trim();
    if (!trimmed || loading) return;
    onGenerate(trimmed);
  };

  const tabs = mediaType === 'video'
    ? [
        { key: 'text-to-video' as VideoTab, label: t('studio.textToVideo'), icon: Video },
        { key: 'image-to-video' as VideoTab, label: t('studio.imageToVideo'), icon: ImageIcon },
      ]
    : null;

  return (
    <div className="flex h-full flex-col gap-5 p-5">
      {/* Tab switch */}
      {tabs && (
        <div className="flex gap-0.5 rounded-lg bg-[var(--bg-secondary)] p-0.5">
          {tabs.map(({ key, label, icon: Icon }) => (
            <button
              key={key}
              onClick={() => setVideoTab(key)}
              className={cn(
                'flex flex-1 items-center justify-center gap-1.5 rounded-md py-2 px-3 text-[13px] font-medium',
                videoTab === key
                  ? 'bg-[var(--bg)] text-[var(--text)] shadow-sm'
                  : 'text-[var(--text-tertiary)] hover:text-[var(--text-secondary)]'
              )}
            >
              <Icon className="h-3.5 w-3.5" />
              {label}
            </button>
          ))}
        </div>
      )}

      {mediaType === 'image' && (
        <div className="flex rounded-lg bg-[var(--bg-secondary)] p-0.5">
          <div className="flex flex-1 items-center justify-center gap-1.5 rounded-md bg-[var(--bg)] py-2 px-3 text-[13px] font-medium text-[var(--text)] shadow-sm">
            <ImageIcon className="h-3.5 w-3.5" />
            {t('studio.imageGeneration')}
          </div>
        </div>
      )}

      {/* Model */}
      <section className="space-y-2.5">
        <h3 className="text-[12px] font-medium text-[var(--text-secondary)]">{t('studio.section.model')}</h3>
        <div className="grid grid-cols-2 gap-2">
          {models.map((model: ModelOption) => (
            <button
              key={model.id}
              onClick={() => setSelectedModel(model.id)}
              className={cn(
                'rounded-[var(--radius)] border p-3 text-left',
                selectedModel === model.id
                  ? 'border-[var(--text)] bg-[var(--bg-secondary)]'
                  : 'border-[var(--border)] hover:border-[var(--border-hover)] hover:bg-[var(--bg-secondary)]'
              )}
            >
              <div className="text-[13px] font-medium text-[var(--text)]">{model.name}</div>
              {model.variant && (
                <span className="mt-0.5 inline-block text-[11px] text-[var(--text-tertiary)]">{model.variant}</span>
              )}
              <div className="mt-0.5 text-[11px] text-[var(--text-tertiary)]">{model.provider}</div>
            </button>
          ))}
        </div>
      </section>

      {/* Prompt */}
      <section className="flex flex-1 flex-col gap-2">
        <h3 className="text-[12px] font-medium text-[var(--text-secondary)]">{t('studio.section.prompt')}</h3>
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder={mediaType === 'video' ? t('studio.prompt.videoPlaceholder') : t('studio.prompt.imagePlaceholder')}
          className="flex-1 min-h-[160px] w-full rounded-[var(--radius)] border border-[var(--border)] bg-[var(--bg)] p-3 text-[14px] text-[var(--text)] placeholder-[var(--text-placeholder)] resize-none outline-none focus:border-[var(--border-hover)]"
          onKeyDown={(e) => {
            if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) handleGenerate();
          }}
        />
      </section>

      {/* Parameters */}
      <section className="space-y-3">
        <h3 className="text-[12px] font-medium text-[var(--text-secondary)]">{t('studio.section.parameters')}</h3>

        <div className="space-y-1.5">
          <label className="text-[11px] text-[var(--text-tertiary)]">{t('studio.param.aspectRatio')}</label>
          <div className="flex flex-wrap gap-1.5">
            {ASPECT_RATIOS.map((ratio) => (
              <button
                key={ratio}
                onClick={() => setAspectRatio(ratio)}
                className={cn(
                  'rounded-md px-3 py-1.5 text-[12px] font-medium',
                  aspectRatio === ratio
                    ? 'bg-[var(--accent-bg)] text-[var(--accent-text)]'
                    : 'bg-[var(--bg-secondary)] text-[var(--text-tertiary)] hover:text-[var(--text-secondary)]'
                )}
              >
                {ratio}
              </button>
            ))}
          </div>
        </div>

        {mediaType === 'video' && (
          <div className="space-y-1.5">
            <label className="text-[11px] text-[var(--text-tertiary)]">{t('studio.param.duration')}</label>
            <div className="flex gap-1.5">
              {VIDEO_DURATIONS.map((d) => (
                <button
                  key={d}
                  onClick={() => setDuration(d)}
                  className={cn(
                    'rounded-md px-3 py-1.5 text-[12px] font-medium',
                    duration === d
                      ? 'bg-[var(--accent-bg)] text-[var(--accent-text)]'
                      : 'bg-[var(--bg-secondary)] text-[var(--text-tertiary)] hover:text-[var(--text-secondary)]'
                  )}
                >
                  {d}s
                </button>
              ))}
            </div>
          </div>
        )}
      </section>

      {/* Generate */}
      <button
        onClick={handleGenerate}
        disabled={loading || !prompt.trim()}
        className={cn(
          'flex w-full items-center justify-center gap-2 rounded-[var(--radius)] py-3 text-[14px] font-medium',
          loading || !prompt.trim()
            ? 'cursor-not-allowed bg-[var(--bg-tertiary)] text-[var(--text-placeholder)]'
            : 'bg-[var(--accent-bg)] text-[var(--accent-text)] hover:opacity-80 active:scale-[0.99]'
        )}
      >
        {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
        {loading ? t('studio.generating') : t('studio.generate')}
      </button>
    </div>
  );
}
