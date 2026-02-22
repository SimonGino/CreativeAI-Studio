import { useEffect, useRef } from 'react';
import { Sparkles, ImageIcon, VideoIcon } from 'lucide-react';
import type { Message } from '@/types';
import { useI18n } from '@/hooks/useI18n';
import MessageBubble from './MessageBubble';
import ChatInput from './ChatInput';

interface ChatViewProps {
  messages: Message[];
  loading: boolean;
  onSendMessage: (content: string, mediaType?: string) => void;
}

export default function ChatView({ messages, loading, onSendMessage }: ChatViewProps) {
  const { t } = useI18n();
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages.length]);

  return (
    <div className="flex h-full min-h-0 flex-col overflow-hidden bg-[var(--bg)]">
      <div className="flex-1 min-h-0 overflow-y-auto">
        {messages.length === 0 && !loading ? (
          <div className="flex h-full flex-col items-center justify-center px-4 text-center">
            <div className="space-y-5">
              <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-[var(--bg-secondary)] border border-[var(--border)]">
                <Sparkles className="h-5 w-5 text-[var(--text-tertiary)]" />
              </div>
              <div className="space-y-1.5">
                <h2 className="text-lg font-semibold text-[var(--text)]">{t('chat.empty.title')}</h2>
                <p className="text-[13px] text-[var(--text-tertiary)]">
                  {t('chat.empty.subtitle')}
                </p>
              </div>
              <div className="flex flex-wrap justify-center gap-2 pt-1">
                {[
                  { icon: ImageIcon, textKey: 'chat.suggestion.1' as const },
                  { icon: VideoIcon, textKey: 'chat.suggestion.2' as const },
                  { icon: ImageIcon, textKey: 'chat.suggestion.3' as const },
                ].map(({ icon: Icon, textKey }) => {
                  const text = t(textKey);
                  return (
                  <button
                    key={textKey}
                    onClick={() => onSendMessage(text)}
                    className="flex items-center gap-1.5 rounded-full border border-[var(--border)] bg-[var(--bg)] px-3.5 py-1.5 text-[12px] text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)] hover:text-[var(--text)]"
                  >
                    <Icon className="h-3 w-3" />
                    {text}
                  </button>
                  );
                })}
              </div>
            </div>
          </div>
        ) : (
          <div className="mx-auto flex max-w-3xl flex-col gap-4 px-4 py-6">
            {messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))}

            {loading && (
              <div className="flex justify-start">
                <div className="rounded-xl bg-[var(--bg-secondary)] px-4 py-3">
                  <div className="flex gap-1">
                    {[0, 1, 2].map((i) => (
                      <span
                        key={i}
                        className="h-1.5 w-1.5 rounded-full bg-[var(--text-tertiary)]"
                        style={{
                          animation: 'pulse 1.2s ease-in-out infinite',
                          animationDelay: `${i * 200}ms`,
                        }}
                      />
                    ))}
                  </div>
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>
        )}
      </div>

      <ChatInput onSend={(content) => onSendMessage(content)} disabled={loading} />
    </div>
  );
}
