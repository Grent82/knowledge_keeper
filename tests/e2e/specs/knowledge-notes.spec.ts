/**
 * Acceptance tests: Knowledge notes section
 *
 * User stories:
 *   1. After login the notes section is visible without raw placeholder text.
 *   2. Clicking a note opens the editor with the correct heading.
 *   3. When no notes exist, a friendly empty-state message is shown.
 */

import { test, expect } from "../fixtures";
import { DashboardPage } from "../pages/DashboardPage";
import { KnowledgeNotesPage } from "../pages/KnowledgeNotesPage";

test.describe("Knowledge notes section", () => {
  // ── 1. Section renders after login ────────────────────────────────────────
  test("knowledge notes section is visible and contains no stub placeholder", async ({
    authenticatedPage: page,
  }) => {
    await page.goto("/");
    const dashboard = new DashboardPage(page);
    await dashboard.waitForReady();

    const notes = new KnowledgeNotesPage(page);
    await expect(notes.noteList()).toBeVisible();

    // No raw stub text should leak into the UI.
    const pageText = await page.locator("body").innerText();
    expect(pageText).not.toContain("[Stub]");
    expect(pageText).not.toContain("TODO");
  });

  // ── 2. Empty state ────────────────────────────────────────────────────────
  test("empty state message is shown when no notes exist", async ({
    authenticatedPage: page,
  }) => {
    await page.goto("/");
    const dashboard = new DashboardPage(page);
    await dashboard.waitForReady();

    const notes = new KnowledgeNotesPage(page);
    const noteCount = await notes.noteItems().count();

    if (noteCount === 0) {
      await expect(notes.emptyStateMessage()).toBeVisible();
      const text = await notes.emptyStateMessage().textContent();
      expect(text).toBeTruthy();
      expect(text!.toLowerCase()).not.toBe("");
    } else {
      // Notes exist — empty state must NOT be rendered.
      await expect(notes.emptyStateMessage()).not.toBeVisible();
    }
  });

  // ── 3. Open editor via seeded note ────────────────────────────────────────
  test("clicking a note opens the editor with correct heading", async ({
    authenticatedPage: page,
    seededNote,
  }) => {
    await page.goto("/");
    const dashboard = new DashboardPage(page);
    await dashboard.waitForReady();

    const notes = new KnowledgeNotesPage(page);

    // The seeded note title may be formatted by `formatKnowledgeNoteTitle` which
    // strips the leading slash if present. Match a button that contains the title text.
    await page
      .getByRole("button", { name: new RegExp(seededNote.title, "i") })
      .first()
      .click();

    await notes.waitForEditorOpen();

    // Heading must say "Wissensnotiz bearbeiten" — NOT "Notizeditor" or any stub variant.
    await expect(page.getByRole("heading", { name: "Wissensnotiz bearbeiten" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Notizeditor" })).not.toBeVisible();
  });

  // ── 4. New note editor heading ─────────────────────────────────────────────
  test("clicking Neue Notiz opens the editor with new-note heading", async ({
    authenticatedPage: page,
  }) => {
    await page.goto("/");
    const dashboard = new DashboardPage(page);
    await dashboard.waitForReady();

    const notes = new KnowledgeNotesPage(page);
    await notes.clickNewNote();
    await notes.waitForEditorOpen();

    await expect(page.getByRole("heading", { name: "Neue Wissensnotiz" })).toBeVisible();
  });
});
