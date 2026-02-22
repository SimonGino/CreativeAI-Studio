# CreativeAI Studio UI & i18n Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 修复主界面高度/分栏布局问题（Chat 输入框贴底、空状态居中、Studio 分栏占满高度），并新增简体中文/英文双语（Header 右上角语言切换 + `localStorage` 记住），全程不使用渐变。

**Architecture:** 使用轻量 i18n（内置字典 + `t(key)` + 简单插值），`locale` 存在 zustand store 并持久化；各 UI 组件通过 `useI18n()` 获取 `t` 与 `locale`；通过 `useEffect` 同步 `<html lang>`；布局通过补齐 flex 高度链路（`min-h-0` / `h-full` / `flex-col`）修复。

**Tech Stack:** React 19 + TypeScript + Vite + Tailwind CSS v4 + Zustand + React Router

**Working Directory:** 本计划默认你在 **worktree 根目录** 执行命令，例如：
```bash
cd /Users/wqq/Code/Freelance/CreativeAI-Studio-ui-i18n
```

---

## Preflight（推荐）

### Task 0: 确认分支 + 安装依赖 + 基线构建

**Files:** 无

**Step 1: 确认当前在 `ui-i18n` 分支**

Run:
```bash
git status -sb
```

Expected: 第一行类似 `## ui-i18n`

**Step 2: 安装前端依赖**

Run:
```bash
pnpm -C frontend install
```

Expected: 安装成功（无需把 `node_modules/` 提交到 git）

**Step 3: 跑一次前端构建，确认 worktree 起点干净**

Run:
```bash
pnpm -C frontend build
```

Expected: build 成功

---

## i18n 基础能力

### Task 1: 新增轻量 i18n 模块（字典 + t + 相对时间）

**Files:**
- Create: `frontend/src/lib/i18n.ts`

**Step 1: 创建 `i18n.ts`（完整代码）**

```ts
export type Locale = 'zh-CN' | 'en'

const en = {
  'mode.chat': 'Chat',
  'mode.studio': 'Studio',
  'language.zh': '中文',
  'language.en': 'EN',

  'sidebar.history': 'History',
  'sidebar.newChat': 'New Chat',

  'time.justNow': 'just now',
  'time.minutesAgo': '{count}m ago',
  'time.hoursAgo': '{count}h ago',
  'time.daysAgo': '{count}d ago',

  'chat.empty.title': 'What would you like to create?',
  'chat.empty.subtitle': 'Generate images with Gemini or videos with Veo 3.1',
  'chat.suggestion.1': 'A dreamy watercolor landscape',
  'chat.suggestion.2': 'A cat playing piano',
  'chat.suggestion.3': 'Cyberpunk city at sunset',
  'chat.input.placeholder': 'Describe what you want to create...',
  'chat.input.model': 'Model',
  'chat.input.ratio': 'Ratio',
  'chat.input.image': 'Image',
  'chat.input.video': 'Video',

  'studio.imageGeneration': 'Image Generation',
  'studio.textToVideo': 'Text to Video',
  'studio.imageToVideo': 'Image to Video',
  'studio.section.model': 'Model',
  'studio.section.prompt': 'Prompt',
  'studio.section.parameters': 'Parameters',
  'studio.param.aspectRatio': 'Aspect Ratio',
  'studio.param.duration': 'Duration',
  'studio.prompt.imagePlaceholder': 'Describe the image...',
  'studio.prompt.videoPlaceholder': 'Describe the video...',
  'studio.generate': 'Generate',
  'studio.generating': 'Generating...',

  'preview.empty.title.images': 'No images yet',
  'preview.empty.title.videos': 'No videos yet',
  'preview.empty.subtitle': 'Configure parameters and click Generate',

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

  'assistant.generatingVideo': 'Generating video...',
  'assistant.videoGenerated': 'Video generated',
  'assistant.imageGenerated': 'Image generated',
  'assistant.failed': 'Failed: {error}',
} as const

export type I18nKey = keyof typeof en

const zhCN: Record<I18nKey, string> = {
  'mode.chat': '聊天',
  'mode.studio': '工作室',
  'language.zh': '中文',
  'language.en': 'EN',

  'sidebar.history': '历史',
  'sidebar.newChat': '新建对话',

  'time.justNow': '刚刚',
  'time.minutesAgo': '{count} 分钟前',
  'time.hoursAgo': '{count} 小时前',
  'time.daysAgo': '{count} 天前',

  'chat.empty.title': '你想创作什么？',
  'chat.empty.subtitle': '用 Gemini 生成图片，或用 Veo 3.1 生成视频',
  'chat.suggestion.1': '梦幻水彩风景',
  'chat.suggestion.2': '一只弹钢琴的猫',
  'chat.suggestion.3': '日落时分的赛博朋克城市',
  'chat.input.placeholder': '描述你想生成的内容…',
  'chat.input.model': '模型',
  'chat.input.ratio': '比例',
  'chat.input.image': '图片',
  'chat.input.video': '视频',

  'studio.imageGeneration': '图片生成',
  'studio.textToVideo': '文生视频',
  'studio.imageToVideo': '图生视频',
  'studio.section.model': '模型',
  'studio.section.prompt': '提示词',
  'studio.section.parameters': '参数',
  'studio.param.aspectRatio': '画面比例',
  'studio.param.duration': '时长',
  'studio.prompt.imagePlaceholder': '描述你想要的图片…',
  'studio.prompt.videoPlaceholder': '描述你想要的视频…',
  'studio.generate': '生成',
  'studio.generating': '生成中…',

  'preview.empty.title.images': '还没有图片',
  'preview.empty.title.videos': '还没有视频',
  'preview.empty.subtitle': '配置参数后点击“生成”',

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

  'assistant.generatingVideo': '正在生成视频…',
  'assistant.videoGenerated': '视频已生成',
  'assistant.imageGenerated': '图片已生成',
  'assistant.failed': '失败：{error}',
}

const DICT: Record<Locale, Record<I18nKey, string>> = { en, 'zh-CN': zhCN }

export function t(locale: Locale, key: I18nKey, vars?: Record<string, string | number>) {
  const template = DICT[locale]?.[key] ?? DICT.en[key] ?? String(key)
  if (!vars) return template
  return template.replace(/\{(\w+)\}/g, (_, k) => String(vars[k] ?? `{${k}}`))
}

export function formatRelativeTime(locale: Locale, dateStr: string): string {
  const ts = new Date(dateStr).getTime()
  if (!Number.isFinite(ts)) return ''
  const diff = Date.now() - ts
  const minutes = Math.floor(diff / 60_000)
  if (minutes < 1) return t(locale, 'time.justNow')
  if (minutes < 60) return t(locale, 'time.minutesAgo', { count: minutes })
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return t(locale, 'time.hoursAgo', { count: hours })
  const days = Math.floor(hours / 24)
  return t(locale, 'time.daysAgo', { count: days })
}
```

**Step 2: 快速编译检查**

Run:
```bash
pnpm -C frontend build
```

Expected: TypeScript 编译通过（无报错）。

**Step 3: Commit**

```bash
git add frontend/src/lib/i18n.ts
git commit -m "feat(frontend): add lightweight i18n core"
```

---

### Task 2: 在 zustand store 增加 `locale` + `localStorage` 持久化

**Files:**
- Modify: `frontend/src/stores/appStore.ts:4`

**Step 1: 增加 locale 状态与初始化逻辑（示例代码）**

- 引入类型：`import type { Locale } from '@/lib/i18n';`
- 新增 `locale` / `setLocale` 到 `AppState`
- 新增 `getInitialLocale()`：优先读 `localStorage`，否则根据 `navigator.language` 粗略判断（`zh*` => `zh-CN`）
- `setLocale()` 写回 `localStorage`

Run（不需要完全一致，但核心逻辑保持）:
```ts
const LOCALE_STORAGE_KEY = 'creativeai-studio:locale'

function getInitialLocale(): Locale {
  if (typeof window === 'undefined') return 'en'
  const saved = window.localStorage.getItem(LOCALE_STORAGE_KEY)
  if (saved === 'en' || saved === 'zh-CN') return saved
  return window.navigator.language.toLowerCase().startsWith('zh') ? 'zh-CN' : 'en'
}
```

**Step 2: 编译检查**

Run:
```bash
pnpm -C frontend build
```

Expected: PASS

**Step 3: Commit**

```bash
git add frontend/src/stores/appStore.ts
git commit -m "feat(frontend): persist locale in app store"
```

---

### Task 3: 新增 `useI18n()` hook（减少重复样板代码）

**Files:**
- Create: `frontend/src/hooks/useI18n.ts`

**Step 1: 创建 hook（完整代码）**

```ts
import { useCallback } from 'react'
import { useAppStore } from '@/stores/appStore'
import { t as translate, type I18nKey } from '@/lib/i18n'

export function useI18n() {
  const locale = useAppStore((s) => s.locale)
  const setLocale = useAppStore((s) => s.setLocale)

  const t = useCallback(
    (key: I18nKey, vars?: Record<string, string | number>) => translate(locale, key, vars),
    [locale],
  )

  return { locale, setLocale, t }
}
```

**Step 2: 编译检查**

Run:
```bash
pnpm -C frontend build
```

Expected: PASS

**Step 3: Commit**

```bash
git add frontend/src/hooks/useI18n.ts
git commit -m "feat(frontend): add useI18n hook"
```

---

## 布局修复 + 文案替换

### Task 4: 修复主区域高度链路（Chat/Studio 占满高度）

**Files:**
- Modify: `frontend/src/App.tsx:169`

**Step 1: 调整 `<main>` 为 flex 容器**

- 把 `App.tsx:179` 的 `main` 从：
  - `className="flex-1 overflow-hidden"`
  - 改成类似：`className="flex flex-1 min-h-0 flex-col overflow-hidden"`
- 目标：确保内部 `ChatView` / `StudioView` 的 `h-full` / `flex-1` 可以正确生效。

**Step 2: 编译检查**

Run:
```bash
pnpm -C frontend build
```

Expected: PASS

**Step 3: Commit**

```bash
git add frontend/src/App.tsx
git commit -m "fix(frontend): make main layout flex for full-height views"
```

---

### Task 5: Header 增加语言切换 + 文案本地化

**Files:**
- Modify: `frontend/src/components/layout/Header.tsx:7`

**Step 1: 用 `useI18n()` 替换硬编码**

- `MODE_OPTIONS` 的 label 改为 i18n key（或直接在渲染时 `t('mode.chat')` / `t('mode.studio')`）
- 新增语言切换 segmented control（放在 Settings icon 左侧或右侧均可，保持尺寸一致）
- 语言切换按钮文案用 `t('language.zh')` / `t('language.en')`

**Step 2: 同步 `<html lang>`**

- 在 `App.tsx:21` 的 `MainPage()` 内新增：
  - `const locale = useAppStore((s) => s.locale)`
  - `useEffect(() => { document.documentElement.lang = locale }, [locale])`

**Step 3: 编译检查 + Commit**

Run:
```bash
pnpm -C frontend build
```

Commit:
```bash
git add frontend/src/components/layout/Header.tsx frontend/src/App.tsx
git commit -m "feat(frontend): add language switch and localize header"
```

---

### Task 6: Sidebar 文案本地化 + 相对时间本地化

**Files:**
- Modify: `frontend/src/components/layout/Sidebar.tsx:13`

**Step 1: 替换文案与时间格式**

- 引入：`import { formatRelativeTime } from '@/lib/i18n'`
- 使用：`const { locale, t } = useI18n()`
- 替换：
  - `History` -> `t('sidebar.history')`
  - `New Chat` -> `t('sidebar.newChat')`
  - `relativeTime(conv.updated_at)` -> `formatRelativeTime(locale, conv.updated_at)`

**Step 2: 编译检查 + Commit**

Run:
```bash
pnpm -C frontend build
```

Commit:
```bash
git add frontend/src/components/layout/Sidebar.tsx
git commit -m "feat(frontend): localize sidebar and relative time"
```

---

### Task 7: ChatView/ChatInput 文案本地化 + Chat 视图贴底修复

**Files:**
- Modify: `frontend/src/components/chat/ChatView.tsx:20`
- Modify: `frontend/src/components/chat/ChatInput.tsx:127`

**Step 1: ChatView 空状态文案替换**

- 使用 `useI18n()` 替换：
  - `ChatView.tsx:30-33` -> `t('chat.empty.title')` / `t('chat.empty.subtitle')`
  - 建议 chips 文案改为 `t('chat.suggestion.1')` 等

**Step 2: ChatView 高度链路**

- 把 `ChatView.tsx:21` 的根容器从 `flex flex-1 ...` 调整为：
  - `className="flex h-full min-h-0 flex-col overflow-hidden ..."`
- 给消息滚动容器补 `min-h-0`（避免 flex 子项无法收缩）

**Step 3: ChatInput 文案替换**

- `ChatInput.tsx:142` placeholder -> `t('chat.input.placeholder')`
- `BottomDropdown` label fallback：
  - `ChatInput.tsx:169` `'Model'` -> `t('chat.input.model')`
  - `ChatInput.tsx:176` `'Ratio'` -> `t('chat.input.ratio')`
- Tab：
  - `ChatInput.tsx:181-183` `'Image'/'Video'` -> `t('chat.input.image')` / `t('chat.input.video')`

**Step 4: 编译检查 + Commit**

Run:
```bash
pnpm -C frontend build
```

Commit:
```bash
git add frontend/src/components/chat/ChatView.tsx frontend/src/components/chat/ChatInput.tsx
git commit -m "feat(frontend): localize chat UI and fix chat layout"
```

---

### Task 8: Studio（ParamPanel/PreviewPanel）文案本地化

**Files:**
- Modify: `frontend/src/components/studio/ParamPanel.tsx:43`
- Modify: `frontend/src/components/studio/PreviewPanel.tsx:79`

**Step 1: ParamPanel 文案替换**

- tabs：
  - `ParamPanel.tsx:45-47` -> `t('studio.textToVideo')` / `t('studio.imageToVideo')`
- image 标题：
  - `ParamPanel.tsx:77` -> `t('studio.imageGeneration')`
- section 标题：
  - `ParamPanel.tsx:84` -> `t('studio.section.model')`
  - `ParamPanel.tsx:109` -> `t('studio.section.prompt')`
  - `ParamPanel.tsx:123` -> `t('studio.section.parameters')`
- labels / placeholder / button：
  - `ParamPanel.tsx:113` -> `t('studio.prompt.videoPlaceholder')` / `t('studio.prompt.imagePlaceholder')`
  - `ParamPanel.tsx:126` -> `t('studio.param.aspectRatio')`
  - `ParamPanel.tsx:147` -> `t('studio.param.duration')`
  - `ParamPanel.tsx:180` -> `t('studio.generating')` / `t('studio.generate')`

**Step 2: PreviewPanel 空状态文案替换**

- `PreviewPanel.tsx:88-92` 替换为：
  - title：`mediaType === 'video' ? t('preview.empty.title.videos') : t('preview.empty.title.images')`
  - subtitle：`t('preview.empty.subtitle')`

**Step 3: 编译检查 + Commit**

Run:
```bash
pnpm -C frontend build
```

Commit:
```bash
git add frontend/src/components/studio/ParamPanel.tsx frontend/src/components/studio/PreviewPanel.tsx
git commit -m "feat(frontend): localize studio UI"
```

---

### Task 9: SettingsPage 文案本地化

**Files:**
- Modify: `frontend/src/components/settings/SettingsPage.tsx:15`

**Step 1: 替换所有硬编码文案**

- 标题：`SettingsPage.tsx:56` -> `t('settings.title')`
- toast/message：把 `handleSave` / `handleTestConnection` 的英文字符串替换为 `t('settings.*')`
- 表单区：label/placeholder/button 全部替换为 i18n key
- Vertex 文案：`settings.section.vertex.desc`

**Step 2: 编译检查 + Commit**

Run:
```bash
pnpm -C frontend build
```

Commit:
```bash
git add frontend/src/components/settings/SettingsPage.tsx
git commit -m "feat(frontend): localize settings page"
```

---

### Task 10: App 内部生成状态文案本地化（Chat/Studio）

**Files:**
- Modify: `frontend/src/App.tsx:62`

**Step 1: 替换生成状态字符串**

- `App.tsx:86-88` `'Generating video...'` -> `t('assistant.generatingVideo')`
- `App.tsx:96-97` `'Video generated'` -> `t('assistant.videoGenerated')`
- `App.tsx:101-102` `Failed: ...` -> `t('assistant.failed', { error: data.error ?? '' })`
- `App.tsx:115-117` `'Image generated'` -> `t('assistant.imageGenerated')`

**Step 2: 编译检查 + Commit**

Run:
```bash
pnpm -C frontend build
```

Commit:
```bash
git add frontend/src/App.tsx
git commit -m "feat(frontend): localize assistant status messages"
```

---

### Task 11: 全局字体回退（改善中文显示），保持无渐变

**Files:**
- Modify: `frontend/src/index.css:4`

**Step 1: 更新 `--font-sans`**

把 `index.css:4` 改为类似：
```css
--font-sans: 'DM Sans', system-ui, -apple-system, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', 'Noto Sans CJK SC', sans-serif;
```

**Step 2: 编译检查 + Commit**

Run:
```bash
pnpm -C frontend build
```

Commit:
```bash
git add frontend/src/index.css
git commit -m "style(frontend): improve font fallback for zh-CN"
```

---

## 最终验证

### Task 12: Lint/Build + 手工验收

**Step 1: Lint**

Run:
```bash
pnpm -C frontend lint
```

Expected: 无 eslint 错误。

**Step 2: Build**

Run:
```bash
pnpm -C frontend build
```

Expected: build 成功。

**Step 3: 手工验收（关键路径）**

- 进入 `/`：切换 Chat/Studio，观察内容是否占满高度；空状态是否居中。
- Chat：发送消息后滚动到底部；输入框始终贴底；切换侧边栏开关不破版。
- Studio：左侧参数滚动；右侧空状态居中；生成后预览区显示正常。
- Settings：切换中英文；按钮/提示文案是否覆盖完整；刷新后语言是否保持。
- 全站：确认没有任何渐变样式。
