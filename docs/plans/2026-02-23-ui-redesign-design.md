# CreativeAI Studio UI Redesign Design

## Context

Current UI uses a chat-based interface (sidebar + header + chat view / studio view). The user wants to redesign it as a professional creative tool, referencing Seedance 2's layout: left parameter panel + right preview area, with top navigation between pages.

**Two core features:**
1. Text-to-Image (Gemini models)
2. Image-to-Video (Veo models, supports image upload as reference frame)

**Additional requirements:**
- History page showing all past generations
- Multi-language support (zh-CN / en)
- Settings page
- Light theme

---

## Navigation Structure

**Header (top bar, ~56px)**

```
| Logo "CreativeAI Studio"  |  图片生成  视频生成  历史记录  |  🌐 中文 ▾   ⚙ Settings |
```

- Left: Logo + app name
- Center: Navigation links (active state: bold + underline or accent color)
- Right: Language dropdown (中文/EN) + Settings icon link
- Routes: `/image`, `/video`, `/history`, `/settings`
- Default route `/` redirects to `/image`

**Removed:**
- Left sidebar (240px conversation list)
- Chat/Studio mode toggle
- Chat-style conversation UI

---

## Page 1: Image Generation (`/image`)

**Layout:** Left panel (~420px fixed) + Right preview (flex-1), full viewport height minus header.

### Left Panel — Parameters

From top to bottom:

1. **AI Model selector**
   - Dropdown card showing: model icon + name + description
   - Models: Gemini 2.5 Flash, Gemini 2.0 Flash, Gemini 3 Pro (from existing `IMAGE_MODELS`)

2. **Prompt textarea**
   - Section label: "提示词" / "Prompt"
   - Multi-line textarea, min-height ~160px, max ~320px
   - Bottom-right: character count `0/5000`
   - Placeholder: "详细描述你想创建的图像..." / "Describe the image you want to create..."

3. **Aspect Ratio selector**
   - Section label: "比例" / "Aspect Ratio"
   - Icon card group (horizontal): 1:1, 3:4, 4:3, 9:16, 16:9
   - Each card shows a proportional rectangle icon + ratio text
   - Active state: border accent color

4. **Number of images**
   - Section label: "生成数量" / "Count"
   - Segmented control: 1, 2, 4
   - Default: 1

5. **Generate button**
   - Full-width primary button at bottom
   - Text: "生成" / "Generate"
   - Loading state: spinner + "生成中..." / "Generating..."
   - Disabled when prompt is empty

### Right Panel — Preview

- **Empty state:** Centered icon (palette/sparkles) + title "准备好创作" / "Ready to Create" + subtitle "描述你想要创建的图像" / "Describe the image you want to create"
- **Generated state:** Image grid (1 image = centered large; 2+ = 2-column grid), each image clickable to enlarge in modal
- **Loading state:** Skeleton placeholder with shimmer animation

---

## Page 2: Video Generation (`/video`)

**Layout:** Same left-right split as image page.

### Left Panel — Parameters

1. **Mode tabs** (top of panel)
   - Two tabs: "图片转视频" / "Image to Video" | "文字转视频" / "Text to Video"
   - Active tab: filled background; inactive: text only

2. **AI Model selector**
   - Same dropdown card style
   - Models: Veo 3.1 Fast, Veo 3.1 (from existing `VIDEO_MODELS`)

3. **Model version** (segmented control)
   - Veo 3.1 Fast: "更快的生成速度" / "Faster generation"
   - Veo 3.1: "高品质视频生成" / "High quality generation"

4. **Image upload** (only in "Image to Video" mode)
   - Section label: "参考图片" / "Reference Image"
   - Dashed border upload zone, supports drag & drop
   - Accepted: PNG, JPG, JPEG, WEBP
   - After upload: show thumbnail with remove button
   - Below: "没有图片？使用 AI 生成图片 →" link to `/image`

5. **Prompt textarea**
   - Same as image page but with video-specific placeholder
   - Placeholder: "描述你希望图片如何动画化..." / "Describe how you want the image to animate..."
   - For text-to-video mode: "描述你想生成的视频..." / "Describe the video you want to create..."

6. **Aspect Ratio**
   - Same card group: 1:1, 3:4, 4:3, 9:16, 16:9

7. **Duration**
   - Section label: "时长" / "Duration"
   - Segmented control: 4s, 6s, 8s

8. **Resolution**
   - Section label: "分辨率" / "Resolution"
   - Segmented control: 720p, 1080p

9. **Generate button**
   - Same style as image page

### Right Panel — Preview

- **Empty state:** Centered icon + "准备好创作" / "Ready to Create"
- **Processing state:** Progress indicator (percentage + status text: pending/processing/completed/failed)
- **Completed state:** Video player with controls (play/pause, progress bar, volume, fullscreen)
- Multiple results: carousel with dot indicators (same as current PreviewPanel)

---

## Page 3: History (`/history`)

**Layout:** Full-width content area (max-w-6xl centered).

- **Filter bar:** Type filter (All / Image / Video), search input
- **Grid layout:** 3-4 columns of cards
- **Each card:**
  - Thumbnail (image or video first frame)
  - Type badge (Image / Video)
  - Prompt text (truncated to 2 lines)
  - Model name + timestamp
  - Click → modal with full details + parameters
- **Empty state:** "还没有生成记录" / "No generation history yet"
- **Data source:** Same API endpoints as current (`/api/conversations` lists, each conversation = one generation)

---

## Page 4: Settings (`/settings`)

Keep existing settings page, update styling to match new design:
- Card-based layout for each section
- Same functionality: API key input, auth type, test connection

---

## Styling System

**Color palette (light theme):**

| Variable | Value | Usage |
|----------|-------|-------|
| `--bg` | `#ffffff` | Main background |
| `--bg-secondary` | `#f9fafb` | Panel backgrounds, cards |
| `--bg-tertiary` | `#f3f4f6` | Hover, segmented controls |
| `--bg-hover` | `#e5e7eb` | Active hover |
| `--text` | `#111827` | Primary text |
| `--text-secondary` | `#6b7280` | Secondary text, labels |
| `--text-tertiary` | `#9ca3af` | Placeholder, hints |
| `--border` | `#e5e7eb` | Borders, dividers |
| `--border-hover` | `#d1d5db` | Focus borders |
| `--accent` | `#2563eb` | Active states, primary buttons |
| `--accent-hover` | `#1d4ed8` | Button hover |
| `--accent-text` | `#ffffff` | Text on accent bg |
| `--radius` | `12px` | Default border radius |
| `--radius-sm` | `8px` | Small elements |

**Typography:** Keep DM Sans + Chinese fallbacks. Increase base readability.

---

## Component Architecture

### New components to create:
- `components/layout/NavHeader.tsx` — New top navigation header
- `components/image/ImageGenerator.tsx` — Image generation page (replaces ChatView for image)
- `components/video/VideoGenerator.tsx` — Video generation page
- `components/video/ImageUpload.tsx` — Image upload zone for video page
- `components/history/HistoryPage.tsx` — History grid page
- `components/shared/ModelSelector.tsx` — Reusable model dropdown card
- `components/shared/ParamSection.tsx` — Reusable parameter section wrapper (label + content)
- `components/shared/SegmentedControl.tsx` — Reusable segmented control
- `components/shared/AspectRatioSelector.tsx` — Aspect ratio card group
- `components/shared/EmptyState.tsx` — Reusable empty state

### Components to remove:
- `components/layout/Sidebar.tsx`
- `components/layout/Header.tsx` (replaced by NavHeader)
- `components/chat/ChatView.tsx`
- `components/chat/ChatInput.tsx`
- `components/chat/MessageBubble.tsx`
- `components/studio/StudioView.tsx`
- `components/studio/ParamPanel.tsx`
- `components/studio/PreviewPanel.tsx`

### Components to keep (with style updates):
- `components/media/ImagePreview.tsx`
- `components/settings/SettingsPage.tsx`

### Routing changes:

```tsx
// Before
<Route path="/" element={<MainPage />} />
<Route path="/settings" element={<SettingsPage />} />

// After
<Route path="/" element={<Navigate to="/image" />} />
<Route path="/image" element={<ImageGenerator />} />
<Route path="/video" element={<VideoGenerator />} />
<Route path="/history" element={<HistoryPage />} />
<Route path="/settings" element={<SettingsPage />} />
```

All pages wrapped in a layout component with `<NavHeader />`.

### Store changes (`appStore.ts`):

Remove:
- `uiMode` / `setUIMode` (no more chat/studio toggle)
- `sidebarOpen` / `setSidebarOpen` (no sidebar)
- `currentConversationId` (no conversation concept in UI)
- `mediaTab` / `setMediaTab` (replaced by routing)

Add:
- `videoMode: 'image-to-video' | 'text-to-video'` (tab state in video page)
- `imageCount: number` (number of images to generate)

Keep:
- `locale` / `setLocale`
- `imageModel` / `videoModel` + setters
- `aspectRatio` / `duration` / `resolution` + setters
- `authType` / `geminiApiKey` + setters

---

## i18n Additions

New translation keys needed for both zh-CN and en:

```
nav.image: 图片生成 / Image
nav.video: 视频生成 / Video
nav.history: 历史记录 / History
nav.settings: 设置 / Settings

image.title: AI 图像工作室 / AI Image Studio
image.model: AI 模型 / AI Model
image.prompt: 提示词 / Prompt
image.prompt.placeholder: 详细描述你想创建的图像... / Describe the image you want to create...
image.ratio: 比例 / Aspect Ratio
image.count: 生成数量 / Count
image.generate: 生成 / Generate
image.generating: 生成中... / Generating...
image.empty.title: 准备好创作 / Ready to Create
image.empty.subtitle: 描述你想要创建的图像 / Describe the image you want to create

video.tab.i2v: 图片转视频 / Image to Video
video.tab.t2v: 文字转视频 / Text to Video
video.model: AI 模型 / AI Model
video.model.version: 模型版本 / Model Version
video.upload: 参考图片 / Reference Image
video.upload.hint: 按一下以上传影像 / Click to upload image
video.upload.formats: PNG, JPG, JPEG, WEBP
video.upload.noImage: 没有图片？使用 AI 生成图片 / No image? Generate with AI
video.prompt.placeholder: 描述你希望图片如何动画化... / Describe how you want the image to animate...
video.prompt.t2v.placeholder: 描述你想生成的视频... / Describe the video you want to create...
video.duration: 时长 / Duration
video.resolution: 分辨率 / Resolution
video.generate: 生成 / Generate

history.title: 生成历史 / Generation History
history.filter.all: 全部 / All
history.filter.image: 图片 / Image
history.filter.video: 视频 / Video
history.empty: 还没有生成记录 / No generation history yet
```

---

## Verification

1. `npm run build` passes with no errors
2. All 4 routes render correctly: `/image`, `/video`, `/history`, `/settings`
3. Image generation flow works end-to-end
4. Video generation flow works (both image-to-video and text-to-video)
5. History page displays past generations
6. Language switching works across all pages
7. Responsive: panels don't break at common screen widths
