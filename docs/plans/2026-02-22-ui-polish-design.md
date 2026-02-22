# UI 精修设计 — 侧栏 / Header / 输入区

**Date:** 2026-02-22
**Status:** Approved

## Problem

Three UI areas look rough: sidebar, header (mode/language switchers), and bottom input area. Issues include poor visual hierarchy, inconsistent spacing, and lack of refinement.

## Solution: Targeted Polish (Plan A)

Minimal changes to CSS classes only. No structural or behavioral changes.

### 1. Sidebar (`Sidebar.tsx`)

| Element | Before | After |
|---------|--------|-------|
| "新建对话" button | `border border-[var(--border)] bg-[var(--bg)]` | `bg-[var(--bg-tertiary)]` (no border) |
| Conversation item padding | `py-2` | `py-2.5` |
| Active item indicator | `bg-[var(--bg-hover)]` only | Add `border-l-2 border-[var(--accent)]` |
| "历史" label | `text-[12px]` | `text-[11px] uppercase tracking-wider` |

### 2. Header (`Header.tsx`)

| Element | Before | After |
|---------|--------|-------|
| Language switcher container | Segmented control (`bg-[var(--bg-secondary)] rounded-lg p-0.5`) | Plain text buttons separated by `/` |
| Selected language | `bg-[var(--bg)] shadow-sm` | `font-semibold text-[var(--text)]` |
| Unselected language | `text-[var(--text-tertiary)]` | `text-[var(--text-tertiary)]` (same) |
| Mode switcher | No change | No change |

### 3. ChatInput (`ChatInput.tsx`)

| Element | Before | After |
|---------|--------|-------|
| Toolbar separator | `border-t border-[var(--border)]` | No border, use `bg-[var(--bg-secondary)] rounded-b-xl` |
| Dropdown font size | `text-[12px]` | `text-[13px]` |
| Media toggle padding | `px-2.5 py-0.5` | `px-3 py-1` |
| Toolbar padding | `px-3 py-1.5` | `px-3 py-2` |

## Non-goals

- No color palette changes
- No new components
- No structural/layout changes
- No dark mode
