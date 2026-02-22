# UI Redesign Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Redesign CreativeAI Studio from chat-based UI to Seedance-style studio tool with left params panel + right preview, top navigation between Image/Video/History/Settings pages.

**Architecture:** Replace sidebar+header+chat layout with a NavHeader + page-routed architecture. Two generator pages (Image, Video) share the same left-right split layout. History page shows past generations in a grid. All business logic moves from monolithic `App.tsx` into per-page components.

**Tech Stack:** React, React Router, Tailwind CSS v4, Zustand, Lucide icons, Axios

**Design doc:** `docs/plans/2026-02-23-ui-redesign-design.md`

---

### Task 1: Update CSS variables and i18n

**Files:**
- Modify: `frontend/src/index.css`
- Modify: `frontend/src/lib/i18n.ts`

**Step 1: Update CSS variables**

In `frontend/src/index.css`, replace the `:root` block:

```css
:root {
  --bg: #ffffff;
  --bg-secondary: #f9fafb;
  --bg-tertiary: #f3f4f6;
  --bg-hover: #e5e7eb;

  --text: #111827;
  --text-secondary: #6b7280;
  --text-tertiary: #9ca3af;
  --text-placeholder: #c0c0c0;

  --border: #e5e7eb;
  --border-hover: #d1d5db;

  --accent: #2563eb;
  --accent-bg: #2563eb;
  --accent-text: #ffffff;

  --radius: 12px;
  --radius-sm: 8px;
}
```

**Step 2: Add new i18n keys**

In `frontend/src/lib/i18n.ts`, replace the entire `en` and `zhCN` objects with updated keys. Remove all `chat.*`, `sidebar.*`, `mode.*` keys. Add new keys:

```typescript
const en = {
  'language.zh': '中文',
  'language.en': 'EN',

  'nav.image': 'Image',
  'nav.video': 'Video',
  'nav.history': 'History',
  'nav.settings': 'Settings',

  'time.justNow': 'just now',
  'time.minutesAgo': '{count}m ago',
  'time.hoursAgo': '{count}h ago',
  'time.daysAgo': '{count}d ago',

  'image.model': 'AI Model',
  'image.prompt': 'Prompt',
  'image.prompt.placeholder': 'Describe the image you want to create...',
  'image.ratio': 'Aspect Ratio',
  'image.count': 'Count',
  'image.generate': 'Generate',
  'image.generating': 'Generating...',
  'image.empty.title': 'Ready to Create',
  'image.empty.subtitle': 'Describe the image you want to create',

  'video.tab.i2v': 'Image to Video',
  'video.tab.t2v': 'Text to Video',
  'video.model': 'AI Model',
  'video.version': 'Model Version',
  'video.upload': 'Reference Image',
  'video.upload.hint': 'Click to upload image',
  'video.upload.formats': 'PNG, JPG, JPEG, WEBP',
  'video.upload.noImage': 'No image? Generate with AI →',
  'video.prompt': 'Prompt',
  'video.prompt.i2v.placeholder': 'Describe how you want the image to animate...',
  'video.prompt.t2v.placeholder': 'Describe the video you want to create...',
  'video.ratio': 'Aspect Ratio',
  'video.duration': 'Duration',
  'video.resolution': 'Resolution',
  'video.generate': 'Generate',
  'video.generating': 'Generating...',
  'video.empty.title': 'Ready to Create',
  'video.empty.subtitle': 'Configure parameters and generate a video',
  'video.status.pending': 'Waiting to start...',
  'video.status.processing': 'Generating video... {progress}%',
  'video.status.completed': 'Video generated',
  'video.status.failed': 'Failed: {error}',

  'history.title': 'Generation History',
  'history.filter.all': 'All',
  'history.filter.image': 'Image',
  'history.filter.video': 'Video',
  'history.empty': 'No generation history yet',
  'history.prompt': 'Prompt',

  'settings.title': 'Settings',
  'settings.saved': 'Settings saved successfully.',
  'settings.saveFailed': 'Failed to save settings.',
  'settings.connectionOk': 'Connection OK.',
  'settings.noAuth': 'No API key or service account configured.',
  'settings.connectionFailed': 'Connection failed.',
  'settings.section.gemini.title': 'Gemini API',
  'settings.section.gemini.desc': 'Enter your Google Gemini API key for image and video generation.',
  'settings.field.apiKey': 'API Key',
  'settings.placeholder.apiKey': 'Enter your Gemini API key',
  'settings.section.vertex.title': 'Vertex AI',
  'settings.section.vertex.desc': 'Set VERTEX_AI_SERVICE_ACCOUNT_JSON in .env to the JSON file path.',
  'settings.button.testConnection': 'Test Connection',
  'settings.button.save': 'Save Settings',
} as const;

export type I18nKey = keyof typeof en;

const zhCN: Record<I18nKey, string> = {
  'language.zh': '中文',
  'language.en': 'EN',

  'nav.image': '图片生成',
  'nav.video': '视频生成',
  'nav.history': '历史记录',
  'nav.settings': '设置',

  'time.justNow': '刚刚',
  'time.minutesAgo': '{count} 分钟前',
  'time.hoursAgo': '{count} 小时前',
  'time.daysAgo': '{count} 天前',

  'image.model': 'AI 模型',
  'image.prompt': '提示词',
  'image.prompt.placeholder': '详细描述你想创建的图像…',
  'image.ratio': '比例',
  'image.count': '生成数量',
  'image.generate': '生成',
  'image.generating': '生成中…',
  'image.empty.title': '准备好创作',
  'image.empty.subtitle': '描述你想要创建的图像',

  'video.tab.i2v': '图片转视频',
  'video.tab.t2v': '文字转视频',
  'video.model': 'AI 模型',
  'video.version': '模型版本',
  'video.upload': '参考图片',
  'video.upload.hint': '点击上传图片',
  'video.upload.formats': 'PNG, JPG, JPEG, WEBP',
  'video.upload.noImage': '没有图片？使用 AI 生成图片 →',
  'video.prompt': '提示词',
  'video.prompt.i2v.placeholder': '描述你希望图片如何动画化…',
  'video.prompt.t2v.placeholder': '描述你想生成的视频…',
  'video.ratio': '比例',
  'video.duration': '时长',
  'video.resolution': '分辨率',
  'video.generate': '生成',
  'video.generating': '生成中…',
  'video.empty.title': '准备好创作',
  'video.empty.subtitle': '配置参数后生成视频',
  'video.status.pending': '等待开始…',
  'video.status.processing': '正在生成视频… {progress}%',
  'video.status.completed': '视频已生成',
  'video.status.failed': '失败：{error}',

  'history.title': '生成历史',
  'history.filter.all': '全部',
  'history.filter.image': '图片',
  'history.filter.video': '视频',
  'history.empty': '还没有生成记录',
  'history.prompt': '提示词',

  'settings.title': '设置',
  'settings.saved': '设置已保存。',
  'settings.saveFailed': '保存失败。',
  'settings.connectionOk': '连接正常。',
  'settings.noAuth': '未配置 API Key 或服务账号。',
  'settings.connectionFailed': '连接失败。',
  'settings.section.gemini.title': 'Gemini API',
  'settings.section.gemini.desc': '填写 Google Gemini API Key，用于图片/视频生成。',
  'settings.field.apiKey': 'API Key',
  'settings.placeholder.apiKey': '请输入 Gemini API Key',
  'settings.section.vertex.title': 'Vertex AI',
  'settings.section.vertex.desc': '在 .env 中设置 VERTEX_AI_SERVICE_ACCOUNT_JSON 为 JSON 文件路径。',
  'settings.button.testConnection': '测试连接',
  'settings.button.save': '保存设置',
};
```

**Step 3: Update types — remove UIMode**

In `frontend/src/types/index.ts`, remove the `UIMode` type (line 5: `export type UIMode = 'chat' | 'studio';`). Add `VideoMode` type:

```typescript
export type VideoMode = 'image-to-video' | 'text-to-video';
```

**Step 4: Update store — remove obsolete state, add new state**

In `frontend/src/stores/appStore.ts`:
- Remove imports of `UIMode`
- Remove: `uiMode`, `setUIMode`, `mediaTab`, `setMediaTab`, `currentConversationId`, `setCurrentConversationId`, `sidebarOpen`, `setSidebarOpen`
- Add: `videoMode: VideoMode`, `setVideoMode`, `imageCount: number`, `setImageCount`

New store interface:

```typescript
import type { MediaType, AuthType, VideoMode } from '@/types';

interface AppState {
  locale: Locale;
  setLocale: (locale: Locale) => void;

  imageModel: string;
  setImageModel: (model: string) => void;
  videoModel: string;
  setVideoModel: (model: string) => void;

  aspectRatio: string;
  setAspectRatio: (ratio: string) => void;
  duration: number;
  setDuration: (d: number) => void;
  resolution: string;
  setResolution: (r: string) => void;
  imageCount: number;
  setImageCount: (n: number) => void;

  videoMode: VideoMode;
  setVideoMode: (mode: VideoMode) => void;

  authType: AuthType;
  setAuthType: (t: AuthType) => void;
  geminiApiKey: string;
  setGeminiApiKey: (key: string) => void;
}
```

Default values: `imageCount: 1`, `videoMode: 'text-to-video'`.

**Step 5: Build verification**

Run: `cd /Users/wqq/Code/Freelance/CreativeAI-Studio/.worktrees/ui-polish/frontend && npx vite build 2>&1 | tail -5`

Note: Build will fail at this point because App.tsx still references removed components/state. This is expected — we fix it in subsequent tasks.

**Step 6: Commit**

```bash
git add frontend/src/index.css frontend/src/lib/i18n.ts frontend/src/types/index.ts frontend/src/stores/appStore.ts
git commit -m "refactor: update CSS vars, i18n keys, types, and store for redesign"
```

---

### Task 2: Create NavHeader component

**Files:**
- Create: `frontend/src/components/layout/NavHeader.tsx`

**Step 1: Create NavHeader**

```tsx
import { Link, useLocation } from 'react-router-dom';
import { Sparkles, Settings, Globe } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAppStore } from '@/stores/appStore';
import { useI18n } from '@/hooks/useI18n';

const NAV_ITEMS = [
  { path: '/image', labelKey: 'nav.image' as const },
  { path: '/video', labelKey: 'nav.video' as const },
  { path: '/history', labelKey: 'nav.history' as const },
];

const LOCALE_OPTIONS = [
  { value: 'zh-CN' as const, label: '中文' },
  { value: 'en' as const, label: 'EN' },
];

export default function NavHeader() {
  const { locale, setLocale, t } = useI18n();
  const location = useLocation();

  return (
    <header className="flex h-14 items-center justify-between border-b border-[var(--border)] bg-[var(--bg)] px-6">
      <Link to="/image" className="flex items-center gap-2 text-[var(--text)]">
        <Sparkles className="h-5 w-5" />
        <span className="text-[15px] font-semibold">CreativeAI Studio</span>
      </Link>

      <nav className="flex items-center gap-1">
        {NAV_ITEMS.map((item) => {
          const isActive = location.pathname === item.path;
          return (
            <Link
              key={item.path}
              to={item.path}
              className={cn(
                'rounded-lg px-4 py-2 text-[14px] font-medium',
                isActive
                  ? 'bg-[var(--bg-tertiary)] text-[var(--text)]'
                  : 'text-[var(--text-secondary)] hover:text-[var(--text)] hover:bg-[var(--bg-tertiary)]'
              )}
            >
              {t(item.labelKey)}
            </Link>
          );
        })}
      </nav>

      <div className="flex items-center gap-3">
        <div className="flex items-center gap-1 text-[13px]">
          <Globe className="h-3.5 w-3.5 text-[var(--text-tertiary)]" />
          {LOCALE_OPTIONS.map((opt, idx) => (
            <span key={opt.value}>
              {idx > 0 && <span className="text-[var(--text-placeholder)]"> / </span>}
              <button
                onClick={() => setLocale(opt.value)}
                className={cn(
                  'font-medium',
                  locale === opt.value
                    ? 'text-[var(--text)]'
                    : 'text-[var(--text-tertiary)] hover:text-[var(--text-secondary)]'
                )}
              >
                {opt.label}
              </button>
            </span>
          ))}
        </div>
        <Link
          to="/settings"
          className={cn(
            'rounded-lg p-2 text-[var(--text-tertiary)] hover:bg-[var(--bg-tertiary)] hover:text-[var(--text-secondary)]',
            location.pathname === '/settings' && 'bg-[var(--bg-tertiary)] text-[var(--text)]'
          )}
        >
          <Settings className="h-4 w-4" />
        </Link>
      </div>
    </header>
  );
}
```

**Step 2: Commit**

```bash
git add frontend/src/components/layout/NavHeader.tsx
git commit -m "feat: add NavHeader component with navigation and language switcher"
```

---

### Task 3: Create shared UI components

**Files:**
- Create: `frontend/src/components/shared/EmptyState.tsx`
- Create: `frontend/src/components/shared/AspectRatioSelector.tsx`
- Create: `frontend/src/components/shared/SegmentedControl.tsx`

**Step 1: Create EmptyState**

```tsx
import type { ReactNode } from 'react';

interface EmptyStateProps {
  icon: ReactNode;
  title: string;
  subtitle?: string;
}

export default function EmptyState({ icon, title, subtitle }: EmptyStateProps) {
  return (
    <div className="flex h-full flex-col items-center justify-center gap-4 text-[var(--text-placeholder)]">
      <div className="rounded-2xl border border-[var(--border)] bg-[var(--bg)] p-6">
        {icon}
      </div>
      <div className="text-center">
        <p className="text-[16px] font-medium text-[var(--text-tertiary)]">{title}</p>
        {subtitle && (
          <p className="mt-1 text-[13px] text-[var(--text-placeholder)]">{subtitle}</p>
        )}
      </div>
    </div>
  );
}
```

**Step 2: Create AspectRatioSelector**

```tsx
import { cn } from '@/lib/utils';
import { ASPECT_RATIOS } from '@/types';

interface AspectRatioSelectorProps {
  value: string;
  onChange: (ratio: string) => void;
}

const RATIO_ICONS: Record<string, { w: number; h: number }> = {
  '1:1': { w: 14, h: 14 },
  '3:4': { w: 12, h: 16 },
  '4:3': { w: 16, h: 12 },
  '9:16': { w: 10, h: 18 },
  '16:9': { w: 18, h: 10 },
};

export default function AspectRatioSelector({ value, onChange }: AspectRatioSelectorProps) {
  return (
    <div className="flex gap-2">
      {ASPECT_RATIOS.map((ratio) => {
        const icon = RATIO_ICONS[ratio] ?? { w: 14, h: 14 };
        return (
          <button
            key={ratio}
            onClick={() => onChange(ratio)}
            className={cn(
              'flex flex-col items-center gap-1.5 rounded-[var(--radius-sm)] border px-3 py-2.5',
              value === ratio
                ? 'border-[var(--accent)] bg-blue-50 text-[var(--accent)]'
                : 'border-[var(--border)] text-[var(--text-tertiary)] hover:border-[var(--border-hover)] hover:text-[var(--text-secondary)]'
            )}
          >
            <div
              className={cn(
                'rounded-sm border',
                value === ratio ? 'border-[var(--accent)]' : 'border-[var(--text-placeholder)]'
              )}
              style={{ width: icon.w, height: icon.h }}
            />
            <span className="text-[11px] font-medium">{ratio}</span>
          </button>
        );
      })}
    </div>
  );
}
```

**Step 3: Create SegmentedControl**

```tsx
import { cn } from '@/lib/utils';

interface SegmentedControlProps<T extends string | number> {
  items: { value: T; label: string }[];
  value: T;
  onChange: (value: T) => void;
}

export default function SegmentedControl<T extends string | number>({
  items,
  value,
  onChange,
}: SegmentedControlProps<T>) {
  return (
    <div className="flex gap-1.5">
      {items.map((item) => (
        <button
          key={String(item.value)}
          onClick={() => onChange(item.value)}
          className={cn(
            'rounded-[var(--radius-sm)] border px-4 py-2 text-[13px] font-medium',
            value === item.value
              ? 'border-[var(--accent)] bg-blue-50 text-[var(--accent)]'
              : 'border-[var(--border)] text-[var(--text-tertiary)] hover:border-[var(--border-hover)] hover:text-[var(--text-secondary)]'
          )}
        >
          {item.label}
        </button>
      ))}
    </div>
  );
}
```

**Step 4: Commit**

```bash
git add frontend/src/components/shared/
git commit -m "feat: add shared UI components — EmptyState, AspectRatioSelector, SegmentedControl"
```

---

### Task 4: Create ImageGenerator page

**Files:**
- Create: `frontend/src/components/image/ImageGenerator.tsx`

**Step 1: Create ImageGenerator**

This is the main image generation page with left params panel + right preview.

The component should:
- Use `useAppStore` for `imageModel`, `aspectRatio`, `imageCount`, `authType`, `geminiApiKey`
- Have local state for `prompt`, `loading`, `results` (string array of image URLs)
- Left panel (~420px): model selector (cards), prompt textarea with char count, aspect ratio selector, count segmented control (1/2/4), generate button
- Right panel: EmptyState or image grid
- On generate: call `generateImage` API, save result to conversation via `createConversation` + `addMessage`, show images
- Model selector: grid of cards from `IMAGE_MODELS`, each shows name + provider, active has accent border

Complete component code (full implementation with all imports, state, handlers, and JSX) should be written as a single file. Reference the existing `ParamPanel.tsx` and `PreviewPanel.tsx` for patterns.

Key patterns to reuse:
- Model card grid from `ParamPanel.tsx:87-106`
- Image preview from `PreviewPanel.tsx:29-76`
- Generate button pattern from `ParamPanel.tsx:171-183`
- API call pattern from `App.tsx:114-125` (image generation flow)
- Conversation creation from `App.tsx:71-77`

**Step 2: Build verification**

Run: `cd /Users/wqq/Code/Freelance/CreativeAI-Studio/.worktrees/ui-polish/frontend && npx vite build 2>&1 | tail -5`

**Step 3: Commit**

```bash
git add frontend/src/components/image/ImageGenerator.tsx
git commit -m "feat: add ImageGenerator page with params panel and preview"
```

---

### Task 5: Create VideoGenerator page

**Files:**
- Create: `frontend/src/components/video/ImageUpload.tsx`
- Create: `frontend/src/components/video/VideoGenerator.tsx`

**Step 1: Create ImageUpload component**

Dashed-border upload zone that:
- Accepts PNG, JPG, JPEG, WEBP via click or drag-and-drop
- Shows thumbnail after upload with remove button
- Converts file to base64 data URL for preview
- Has link "没有图片？使用 AI 生成图片 →" that navigates to `/image`

```tsx
import { useRef, useState, useCallback } from 'react';
import { Upload, X } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useI18n } from '@/hooks/useI18n';

interface ImageUploadProps {
  value: string | null;
  onChange: (dataUrl: string | null) => void;
}

export default function ImageUpload({ value, onChange }: ImageUploadProps) {
  const { t } = useI18n();
  const inputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);

  const handleFile = useCallback((file: File) => {
    if (!file.type.startsWith('image/')) return;
    const reader = new FileReader();
    reader.onload = () => onChange(reader.result as string);
    reader.readAsDataURL(file);
  }, [onChange]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  }, [handleFile]);

  if (value) {
    return (
      <div className="relative inline-block">
        <img src={value} alt="Reference" className="max-h-40 rounded-[var(--radius-sm)] border border-[var(--border)]" />
        <button
          onClick={() => onChange(null)}
          className="absolute -right-2 -top-2 rounded-full border border-[var(--border)] bg-[var(--bg)] p-1 text-[var(--text-tertiary)] hover:text-[var(--text)]"
        >
          <X className="h-3 w-3" />
        </button>
      </div>
    );
  }

  return (
    <div>
      <button
        type="button"
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        className={`flex w-full flex-col items-center gap-2 rounded-[var(--radius)] border-2 border-dashed px-6 py-8 ${
          isDragging ? 'border-[var(--accent)] bg-blue-50' : 'border-[var(--border)] hover:border-[var(--border-hover)]'
        }`}
      >
        <Upload className="h-6 w-6 text-[var(--text-tertiary)]" />
        <span className="text-[13px] font-medium text-[var(--text-secondary)]">{t('video.upload.hint')}</span>
        <span className="text-[11px] text-[var(--text-placeholder)]">{t('video.upload.formats')}</span>
      </button>
      <input
        ref={inputRef}
        type="file"
        accept="image/png,image/jpeg,image/webp"
        className="hidden"
        onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFile(f); }}
      />
      <Link to="/image" className="mt-2 inline-block text-[12px] text-[var(--accent)] hover:underline">
        {t('video.upload.noImage')}
      </Link>
    </div>
  );
}
```

**Step 2: Create VideoGenerator**

This page has:
- Tab switch: Image to Video / Text to Video (using `videoMode` from store)
- Left params panel: model selector, model version segmented control, image upload (i2v only), prompt textarea, aspect ratio, duration, resolution, generate button
- Right preview: EmptyState, progress indicator, or video player
- On generate: call `generateVideo` API with SSE for progress, save to conversation

Key patterns to reuse:
- Video generation + SSE from `App.tsx:86-112`
- Model cards from `ParamPanel.tsx`
- Tab switch from `ParamPanel.tsx:55-73`

**Step 3: Build verification**

Run: `cd /Users/wqq/Code/Freelance/CreativeAI-Studio/.worktrees/ui-polish/frontend && npx vite build 2>&1 | tail -5`

**Step 4: Commit**

```bash
git add frontend/src/components/video/
git commit -m "feat: add VideoGenerator page with image upload and SSE progress"
```

---

### Task 6: Create HistoryPage

**Files:**
- Create: `frontend/src/components/history/HistoryPage.tsx`

**Step 1: Create HistoryPage**

This page:
- Fetches all conversations via `listConversations()` on mount
- For each conversation, fetches details via `getConversation(id)` to get messages with media
- Shows a filter bar: All / Image / Video
- Displays a responsive grid (3-4 columns) of cards
- Each card shows: thumbnail (first media_url from messages), type badge, prompt (first user message content, truncated), model name, timestamp
- Empty state when no history

Data flow:
- On mount: `listConversations()` → for each, `getConversation(id)` → extract first user message (prompt) and first assistant message with media_url (thumbnail)
- Filter by `media_type` from messages

**Step 2: Build verification**

Run: `cd /Users/wqq/Code/Freelance/CreativeAI-Studio/.worktrees/ui-polish/frontend && npx vite build 2>&1 | tail -5`

**Step 3: Commit**

```bash
git add frontend/src/components/history/HistoryPage.tsx
git commit -m "feat: add HistoryPage with grid view and type filters"
```

---

### Task 7: Rewrite App.tsx routing and clean up old components

**Files:**
- Modify: `frontend/src/App.tsx` (complete rewrite)
- Delete: `frontend/src/components/layout/Sidebar.tsx`
- Delete: `frontend/src/components/layout/Header.tsx`
- Delete: `frontend/src/components/chat/ChatView.tsx`
- Delete: `frontend/src/components/chat/ChatInput.tsx`
- Delete: `frontend/src/components/chat/MessageBubble.tsx`
- Delete: `frontend/src/components/studio/StudioView.tsx`
- Delete: `frontend/src/components/studio/ParamPanel.tsx`
- Delete: `frontend/src/components/studio/PreviewPanel.tsx`
- Modify: `frontend/src/components/settings/SettingsPage.tsx` (update back link to `/image`)

**Step 1: Rewrite App.tsx**

```tsx
import { useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAppStore } from '@/stores/appStore';
import NavHeader from '@/components/layout/NavHeader';
import ImageGenerator from '@/components/image/ImageGenerator';
import VideoGenerator from '@/components/video/VideoGenerator';
import HistoryPage from '@/components/history/HistoryPage';
import { SettingsPage } from '@/components/settings/SettingsPage';

function AppLayout({ children }: { children: React.ReactNode }) {
  const locale = useAppStore((s) => s.locale);

  useEffect(() => {
    document.documentElement.lang = locale;
  }, [locale]);

  return (
    <div className="flex h-screen flex-col overflow-hidden bg-[var(--bg)]">
      <NavHeader />
      <main className="flex flex-1 min-h-0 overflow-hidden">
        {children}
      </main>
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/image" replace />} />
      <Route path="/image" element={<AppLayout><ImageGenerator /></AppLayout>} />
      <Route path="/video" element={<AppLayout><VideoGenerator /></AppLayout>} />
      <Route path="/history" element={<AppLayout><HistoryPage /></AppLayout>} />
      <Route path="/settings" element={<AppLayout><SettingsPage /></AppLayout>} />
    </Routes>
  );
}
```

**Step 2: Delete old components**

Delete all files listed above (Sidebar, Header, ChatView, ChatInput, MessageBubble, StudioView, ParamPanel, PreviewPanel).

**Step 3: Update SettingsPage**

In `SettingsPage.tsx` line 53, change `navigate('/')` to `navigate('/image')`.

**Step 4: Remove unused ModelSelector**

Delete `frontend/src/components/layout/ModelSelector.tsx` (was used by old Header, now model selection is inline in each page).

**Step 5: Build verification**

Run: `cd /Users/wqq/Code/Freelance/CreativeAI-Studio/.worktrees/ui-polish/frontend && npx vite build 2>&1 | tail -5`
Expected: Build succeeds with no errors.

**Step 6: Commit**

```bash
git add -A
git commit -m "refactor: replace chat/studio layout with routed pages, remove old components"
```

---

### Task 8: End-to-end verification

**Step 1: Start dev server**

Run: `cd /Users/wqq/Code/Freelance/CreativeAI-Studio/.worktrees/ui-polish/frontend && npx vite --host 2>&1 &`

**Step 2: Verify all routes**

- `/` → redirects to `/image`
- `/image` → shows image generator with left params + right empty state
- `/video` → shows video generator with tabs + params + empty state
- `/history` → shows history grid (may be empty)
- `/settings` → shows settings page with back button

**Step 3: Verify functionality**

- Language switcher toggles all text between zh-CN and EN
- Model selection works on both image and video pages
- Aspect ratio selector highlights correctly
- Image upload zone accepts drag-and-drop on video page
- Generate button is disabled when prompt is empty
- Navigate between pages preserves state (model selection, etc.)
