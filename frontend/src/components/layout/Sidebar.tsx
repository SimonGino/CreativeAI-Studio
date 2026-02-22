import { Plus, Trash2, MessageSquare, PanelLeftClose } from 'lucide-react';
import { useAppStore } from '@/stores/appStore';
import { cn } from '@/lib/utils';
import type { Conversation } from '@/types';

interface SidebarProps {
  conversations: Conversation[];
  onNewConversation: () => void;
  onSelectConversation: (id: string) => void;
  onDeleteConversation: (id: string) => void;
}

function relativeTime(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const minutes = Math.floor(diff / 60_000);
  if (minutes < 1) return 'just now';
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

export default function Sidebar({
  conversations,
  onNewConversation,
  onSelectConversation,
  onDeleteConversation,
}: SidebarProps) {
  const currentId = useAppStore((s) => s.currentConversationId);
  const sidebarOpen = useAppStore((s) => s.sidebarOpen);
  const setSidebarOpen = useAppStore((s) => s.setSidebarOpen);

  if (!sidebarOpen) return null;

  return (
    <aside className="flex w-[240px] shrink-0 flex-col border-r border-[var(--border)] bg-[var(--bg-secondary)]">
      <div className="flex items-center justify-between px-4 py-3">
        <span className="text-[12px] font-medium text-[var(--text-tertiary)]">History</span>
        <button
          onClick={() => setSidebarOpen(false)}
          className="rounded-md p-1 text-[var(--text-tertiary)] hover:bg-[var(--bg-hover)] hover:text-[var(--text-secondary)]"
        >
          <PanelLeftClose className="h-4 w-4" />
        </button>
      </div>

      <div className="px-3 pb-2">
        <button
          onClick={onNewConversation}
          className="flex w-full items-center justify-center gap-1.5 rounded-[var(--radius)] border border-[var(--border)] bg-[var(--bg)] px-3 py-2 text-[13px] font-medium text-[var(--text)] hover:bg-[var(--bg-tertiary)]"
        >
          <Plus className="h-3.5 w-3.5" />
          New Chat
        </button>
      </div>

      <nav className="flex-1 overflow-y-auto px-2 pb-2">
        {conversations.map((conv) => {
          const isActive = conv.id === currentId;
          return (
            <button
              key={conv.id}
              onClick={() => onSelectConversation(conv.id)}
              className={cn(
                'group flex w-full items-start gap-2 rounded-lg px-2.5 py-2 text-left',
                isActive
                  ? 'bg-[var(--bg-hover)] text-[var(--text)]'
                  : 'text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)]'
              )}
            >
              <MessageSquare className="mt-0.5 h-3.5 w-3.5 shrink-0 text-[var(--text-tertiary)]" />
              <div className="min-w-0 flex-1">
                <p className="truncate text-[13px] font-medium">{conv.title}</p>
                <p className="text-[11px] text-[var(--text-tertiary)]">{relativeTime(conv.updated_at)}</p>
              </div>
              <button
                onClick={(e) => { e.stopPropagation(); onDeleteConversation(conv.id); }}
                className="mt-0.5 hidden shrink-0 rounded p-0.5 text-[var(--text-tertiary)] hover:bg-red-50 hover:text-red-500 group-hover:block"
              >
                <Trash2 className="h-3 w-3" />
              </button>
            </button>
          );
        })}
      </nav>
    </aside>
  );
}
