import ParamPanel from './ParamPanel';
import PreviewPanel from './PreviewPanel';
import type { MediaType } from '@/types';

interface StudioViewProps {
  onGenerate: (prompt: string) => void;
  loading: boolean;
  results: string[];
  mediaType: MediaType;
}

export default function StudioView({ onGenerate, loading, results, mediaType }: StudioViewProps) {
  return (
    <div className="flex h-full min-h-0">
      <div className="w-[400px] shrink-0 overflow-y-auto border-r border-[var(--border)] bg-[var(--bg)]">
        <ParamPanel onGenerate={onGenerate} loading={loading} mediaType={mediaType} />
      </div>
      <div className="min-w-0 flex-1 overflow-y-auto bg-[var(--bg-secondary)]">
        <PreviewPanel results={results} mediaType={mediaType} />
      </div>
    </div>
  );
}
