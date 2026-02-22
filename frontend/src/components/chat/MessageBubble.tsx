import { cn } from '@/lib/utils';
import type { Message } from '@/types';

interface MessageBubbleProps {
  message: Message;
}

function formatTime(dateStr: string): string {
  return new Date(dateStr).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user';

  return (
    <div className={cn('flex w-full', isUser ? 'justify-end' : 'justify-start')}>
      <div
        className={cn(
          'max-w-[80%] rounded-xl px-4 py-2.5',
          isUser
            ? 'bg-[var(--accent-bg)] text-[var(--accent-text)]'
            : 'bg-[var(--bg-secondary)] text-[var(--text)]'
        )}
      >
        {!isUser && message.model && (
          <span className="mb-1 inline-block rounded bg-[var(--bg-tertiary)] px-1.5 py-0.5 text-[10px] font-medium text-[var(--text-tertiary)]">
            {message.model}
          </span>
        )}

        <p className="whitespace-pre-wrap text-[14px] leading-relaxed">{message.content}</p>

        {message.media_url && message.media_type === 'image' && (
          <img
            src={message.media_url}
            alt="Generated image"
            onClick={() => window.open(message.media_url!, '_blank')}
            className="mt-2 max-h-72 cursor-pointer rounded-lg object-contain"
          />
        )}

        {message.media_url && message.media_type === 'video' && (
          <video src={message.media_url} controls className="mt-2 max-h-72 rounded-lg" />
        )}

        <p className={cn(
          'mt-1 text-[10px]',
          isUser ? 'text-white/50' : 'text-[var(--text-tertiary)]'
        )}>
          {formatTime(message.created_at)}
        </p>
      </div>
    </div>
  );
}
