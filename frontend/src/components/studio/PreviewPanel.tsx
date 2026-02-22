import { useState } from 'react';
import { ChevronLeft, ChevronRight, ImageIcon, VideoIcon } from 'lucide-react';
import { cn } from '@/lib/utils';
import ImagePreview from '@/components/media/ImagePreview';
import type { MediaType } from '@/types';

interface PreviewPanelProps {
  results: string[];
  mediaType: MediaType;
}

export default function PreviewPanel({ results, mediaType }: PreviewPanelProps) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const safeIndex = results.length > 0 ? Math.min(currentIndex, results.length - 1) : 0;

  if (results.length === 0) return <EmptyState mediaType={mediaType} />;

  if (mediaType === 'video') {
    return (
      <div className="flex h-full items-center justify-center p-8">
        <div className="w-full max-w-3xl">
          <video src={results[0]} controls autoPlay className="w-full rounded-xl shadow-md" />
        </div>
      </div>
    );
  }

  if (results.length === 1) {
    return (
      <div className="flex h-full items-center justify-center p-8">
        <ImagePreview src={results[0]} alt="Generated image" className="max-h-[80vh] rounded-xl shadow-md" />
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      <div className="relative flex flex-1 items-center justify-center p-8">
        <ImagePreview
          src={results[safeIndex]}
          alt={`Generated image ${safeIndex + 1}`}
          className="max-h-[70vh] rounded-xl shadow-md"
        />
        {safeIndex > 0 && (
          <button
            onClick={() => setCurrentIndex(safeIndex - 1)}
            className="absolute left-4 top-1/2 -translate-y-1/2 rounded-full border border-[var(--border)] bg-[var(--bg)] p-2 text-[var(--text-secondary)] shadow-sm hover:bg-[var(--bg-secondary)]"
          >
            <ChevronLeft className="h-4 w-4" />
          </button>
        )}
        {safeIndex < results.length - 1 && (
          <button
            onClick={() => setCurrentIndex(safeIndex + 1)}
            className="absolute right-4 top-1/2 -translate-y-1/2 rounded-full border border-[var(--border)] bg-[var(--bg)] p-2 text-[var(--text-secondary)] shadow-sm hover:bg-[var(--bg-secondary)]"
          >
            <ChevronRight className="h-4 w-4" />
          </button>
        )}
      </div>
      <div className="flex justify-center gap-2 border-t border-[var(--border)] p-3">
        {results.map((src, i) => (
          <button
            key={i}
            onClick={() => setCurrentIndex(i)}
            className={cn(
              'h-14 w-14 overflow-hidden rounded-lg border-2',
              i === safeIndex ? 'border-[var(--text)] opacity-100' : 'border-transparent opacity-50 hover:opacity-75'
            )}
          >
            <img src={src} alt={`Thumbnail ${i + 1}`} className="h-full w-full object-cover" />
          </button>
        ))}
      </div>
    </div>
  );
}

function EmptyState({ mediaType }: { mediaType: MediaType }) {
  const Icon = mediaType === 'video' ? VideoIcon : ImageIcon;
  return (
    <div className="flex h-full flex-col items-center justify-center gap-4 text-[var(--text-placeholder)]">
      <div className="rounded-xl border border-[var(--border)] bg-[var(--bg)] p-5">
        <Icon className="h-10 w-10" strokeWidth={1} />
      </div>
      <div className="text-center">
        <p className="text-[14px] font-medium text-[var(--text-tertiary)]">
          No {mediaType === 'video' ? 'videos' : 'images'} yet
        </p>
        <p className="mt-0.5 text-[12px] text-[var(--text-placeholder)]">
          Configure parameters and click Generate
        </p>
      </div>
    </div>
  );
}
