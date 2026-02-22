# CreativeAI Studio UI 改版与双语支持（简中/英文）设计

**日期：** 2026-02-22  
**范围：** `CreativeAI-Studio/frontend`（React + Vite + Tailwind）

## 背景 / 问题

- 当前主区域布局高度链路不完整，导致内容“挤在顶部、下方大面积空白”，聊天输入框无法稳定贴底。
- 多处文案硬编码英文（Header/Sidebar/Chat/Studio/Settings/空状态/提示文本等），缺少简体中文支持。
- 视觉层级偏弱：分栏比例、内边距、字体回退（中文字体）与若干细节一致性不足。

## 目标

- 修复布局：主区域占满可用高度；Chat 的消息区滚动、输入框贴底；Studio 左右分栏稳定且可滚动。
- 视觉提升（不使用渐变）：更一致的留白、边框、背景层级与字体回退，整体更“干净、克制、像工具”。
- 多语系：支持 **简体中文 / English** 两种语言；在 Header 右上角提供语言切换；使用 `localStorage` 记住选择。

## 非目标

- 不引入大型 UI 组件库或完整 i18n 框架（保持依赖与复杂度最小）。
- 不做深色模式、不做主题系统重构（可留后续扩展点）。
- 不改变后端接口与数据结构（仅前端展示层改进）。

## 现状梳理（关键发现）

- `src/App.tsx` 的 `<main>` 不是 flex 容器且缺少 `min-h-0` 约束，子组件里的 `flex-1` 高度无法按预期生效。
- 文案分散在多个组件内：`Header.tsx`、`Sidebar.tsx`、`ChatView.tsx`、`ChatInput.tsx`、`ParamPanel.tsx`、`PreviewPanel.tsx`、`SettingsPage.tsx`、`App.tsx`（生成状态文案）。
- Sidebar 的相对时间目前为英文拼接，不会随语言变化。

## 方案概览（方案 A）

### 1) 布局修复（最小改动）

- 调整 `src/App.tsx`：让 `<main>` 成为垂直 flex 容器，并补齐高度链路（`flex flex-col min-h-0`）。
- `ChatView`：外层容器使用 `h-full min-h-0`，消息列表区 `flex-1 overflow-y-auto`，输入框 `shrink-0`，确保稳定贴底。
- `StudioView`：保持左右分栏 `h-full min-h-0`；参数面板 `overflow-y-auto`；预览区居中且滚动行为稳定。

### 2) 视觉（不使用渐变）

- 继续沿用 CSS 变量体系：`--bg / --bg-secondary / --border / --radius / --accent-*`。
- 增强中文字体回退：在 `index.css` 的 `--font-sans` 增加常见中文系统字体（不改变现有英文字体）。
- 统一细节：分栏宽度、Header/按钮高度、空状态的卡片边框与留白；减少不一致的阴影/对比。

### 3) i18n（简中/英文）

- 在 `zustand` store 增加 `locale: 'zh-CN' | 'en'` 与 `setLocale()`；启动时从 `localStorage` 读取，变更时写回。
- 新增轻量翻译模块 `src/lib/i18n.ts`：
  - 内置字典对象：`en`/`zh-CN`
  - `t(key)`：基于当前 `locale` 返回字符串（可支持简单插值）
- Header 增加语言切换控件（中文/EN），与现有模式切换风格一致。
- Sidebar 的相对时间改为 `Intl.RelativeTimeFormat(locale)` 输出，确保“刚刚 / 3 分钟前”与“just now / 3m ago”一致。
- 页面 `<html lang>` 同步更新（便于可访问性/输入法/浏览器优化）。

## 验收标准

- Chat 页：空状态垂直居中；消息区滚动；输入框始终贴底；窗口缩放/侧边栏开关不破版。
- Studio 页：左侧参数区可滚动；右侧预览区居中；无结果时空状态居中展示。
- Settings 页：中英文文案完整覆盖；切换语言后立即生效且刷新后保持。
- 全站：无渐变背景/按钮；视觉层级更清晰（背景/面板/边框/间距一致）。

## 风险与回滚

- 风险：少量文案漏翻译导致混用语言；通过全量 `t()` 替换与 `rg` 检查降低风险。
- 回滚：所有改动集中在前端 UI 与文案，回滚可通过还原相关文件完成，不涉及后端数据。

