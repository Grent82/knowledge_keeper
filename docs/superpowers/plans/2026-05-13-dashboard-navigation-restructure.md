# Dashboard Navigation Restructure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move search into a top-level discovery bar, shift categories into a dedicated left navigation column, keep the media library as the main workspace, and contain transcript overflow in a bounded scroll area.

**Architecture:** Keep the existing data and selection model intact. Refactor only the dashboard composition, extract the inline media-library card into its own component, and add a transcript scroll container so the page hierarchy is clearer without introducing a new navigation state model.

**Tech Stack:** React 19, TypeScript, Vite, Vitest, CSS

---

### Task 1: Lock the new structure with failing tests

**Files:**
- Create: `frontend/src/features/app-shell/dashboardLayout.test.tsx`
- Test: `frontend/src/features/app-shell/dashboardLayout.test.tsx`

- [ ] **Step 1: Write the failing tests**

```tsx
expect(markup).toContain("dashboard-search-row");
expect(markup).toContain("dashboard-workspace");
expect(markup).toContain("dashboard-sidebar");
expect(markup).toContain("dashboard-main");
expect(markup).toContain("transcript-scroll-area");
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pnpm --filter @knowledge-keeper/frontend test -- src/features/app-shell/dashboardLayout.test.tsx`
Expected: FAIL because the current dashboard and transcript markup do not include the new structure classes.

- [ ] **Step 3: Write minimal implementation**

Add the new dashboard regions in `Dashboard.tsx`, extract the media-library card to its own component, and wrap transcript content in a dedicated scroll area in `TranscriptPanel.tsx`.

- [ ] **Step 4: Run test to verify it passes**

Run: `pnpm --filter @knowledge-keeper/frontend test -- src/features/app-shell/dashboardLayout.test.tsx`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/features/app-shell/dashboardLayout.test.tsx frontend/src/features/app-shell/Dashboard.tsx frontend/src/features/app-shell/MediaLibraryPanel.tsx frontend/src/features/app-shell/TranscriptPanel.tsx frontend/src/styles.css
git commit -m "feat: restructure dashboard workspace"
```

### Task 2: Apply layout styling and verify the app-level checks

**Files:**
- Modify: `frontend/src/styles.css`
- Test: `frontend/src/features/app-shell/dashboardLayout.test.tsx`

- [ ] **Step 1: Add the layout styles**

```css
.dashboard-search-row { ... }
.dashboard-workspace { ... }
.dashboard-sidebar { ... }
.dashboard-main { ... }
.transcript-scroll-area { ... }
```

- [ ] **Step 2: Run targeted frontend validation**

Run: `pnpm --filter @knowledge-keeper/frontend test -- src/features/app-shell/dashboardLayout.test.tsx`
Expected: PASS

- [ ] **Step 3: Run full frontend validation**

Run: `pnpm --filter @knowledge-keeper/frontend lint && pnpm --filter @knowledge-keeper/frontend typecheck && pnpm --filter @knowledge-keeper/frontend build`
Expected: all commands succeed

- [ ] **Step 4: Run repo quality gates**

Run: `make quality`
Expected: PASS
