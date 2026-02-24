# Reference Image Asset Picker (Modal) Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the raw reference image file input with a styled upload button and a Modal picker that can select existing image assets (default origin=generated, switchable to upload/all) and writes `reference_image_asset_id`.

**Architecture:** Add a lightweight reusable `Modal` component and a dedicated `ImageAssetPickerModal` component that pages through `/api/assets` (`media_type=image`, optional `origin`). Wire it into `GeneratePage` for `image.generate` reference images and add minimal CSS for modal + asset grid.

**Tech Stack:** React 19 + TypeScript + Vite, existing `api` client, global CSS in `web/src/index.css`.

---

### Task 1: Add a reusable Modal component

**Files:**
- Create: `web/src/app/components/Modal.tsx`

**Step 1: (Manual check) Ensure no existing modal**
- Run: `rg -n "modalOverlay|role=\\\"dialog\\\"" web/src/app`
- Expected: No existing component.

**Step 2: Implement `Modal`**
- Implement overlay + panel.
- Close behaviors: `Escape`, click on overlay, close button.
- Keep API minimal: `open`, `title`, `children`, `footer`, `onClose`.

**Step 3: Typecheck**
- Run: `pnpm -C web build`
- Expected: Exit 0.

---

### Task 2: Add ImageAssetPickerModal (origin switch + pagination + grid)

**Files:**
- Create: `web/src/app/components/ImageAssetPickerModal.tsx`
- Modify: `web/src/index.css`

**Step 1: Implement data loading**
- Use `api.listAssets({ media_type: 'image', origin, limit, offset })`.
- Default `origin='generated'`, with UI to switch `generated/upload/all`.
- Pagination: previous/next; next enabled when `assets.length === limit`.

**Step 2: Implement grid UI**
- Show thumbnail via `/api/assets/<id>/content` with `loading="lazy"`.
- Highlight selected tile.
- On click: call `onSelect(asset)` then `onClose()`.

**Step 3: Add minimal CSS**
- Add `.modalOverlay`, `.modalPanel`, `.modalHeader`, `.modalBody`, `.modalFooter`.
- Add `.assetGrid`, `.assetCard`, `.assetThumb`, `.assetMeta` and selected state.

**Step 4: Verify**
- Run: `pnpm -C web build`
- Expected: Exit 0.

---

### Task 3: Wire picker into GeneratePage reference image input

**Files:**
- Modify: `web/src/app/pages/GeneratePage.tsx`
- Modify: `web/src/index.css`

**Step 1: Replace raw file input with buttons**
- Add hidden file input + “上传参考图” button (triggers click).
- Add “从资产选择” button (opens modal).
- Ensure input value resets after upload to allow re-selecting same file.

**Step 2: Display selected reference preview + clear**
- When `referenceAssetId` exists: render thumbnail + id and a “清除” button.

**Step 3: Verify**
- Run: `pnpm -C web build`
- Expected: Exit 0.

---

### Task 4: Lint + quick manual verification

**Files:**
- No new files.

**Step 1: Lint**
- Run: `pnpm -C web lint`
- Expected: Exit 0.

**Step 2: Manual smoke**
- Run: `pnpm -C web dev`
- Check: `http://localhost:5174/generate?mode=image` → reference picker works:
  - upload sets asset id and shows preview
  - modal opens, default shows generated, toggles origin, paginates, select fills id
  - clear resets selection

