import { cn } from '@/lib/utils';

interface ImagePreviewProps {
  src: string;
  alt?: string;
  className?: string;
}

export default function ImagePreview({ src, alt = 'Preview', className }: ImagePreviewProps) {
  return (
    <img
      src={src}
      alt={alt}
      onClick={() => window.open(src, '_blank')}
      className={cn('cursor-pointer rounded-xl transition-transform hover:scale-[1.01]', className)}
    />
  );
}

