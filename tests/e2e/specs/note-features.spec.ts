/**
 * Acceptance tests: New knowledge note features
 */

import type { Page } from "@playwright/test";

import { test, expect } from "../fixtures";
import { DashboardPage } from "../pages/DashboardPage";
import { KnowledgeNotesPage } from "../pages/KnowledgeNotesPage";

async function openDashboard(page: Page) {
  await page.goto("/");
  const dashboard = new DashboardPage(page);
  await dashboard.waitForReady();

  return {
    dashboard,
    notes: new KnowledgeNotesPage(page),
  };
}

test.describe("Knowledge note feature coverage", () => {
  test("note list can be filtered via the search input", async ({
    authenticatedPage: page,
    seededNote,
  }) => {
    const { notes } = await openDashboard(page);
    const noteButton = notes.noteItems().filter({ hasText: seededNote.title }).first();

    await notes.filterInput().fill(seededNote.title);
    await expect(noteButton).toBeVisible();

    await notes.filterInput().clear();
    await expect(noteButton).toBeVisible();
  });

  test("note list items show a non-empty kind badge", async ({
    authenticatedPage: page,
    seededNote,
  }) => {
    const { notes } = await openDashboard(page);
    const noteButton = notes.noteItems().filter({ hasText: seededNote.title }).first();
    const badge = notes.kindBadge(noteButton);

    await expect(noteButton).toBeVisible();
    await expect(badge).toBeVisible();
    await expect(badge).toHaveText(/\S+/);
  });

  test("note editor persists the selected note kind", async ({
    authenticatedPage: page,
    seededNote,
  }) => {
    const { dashboard, notes } = await openDashboard(page);

    await notes.openNoteByTitle(seededNote.title);
    await notes.waitForEditorOpen();
    await expect(notes.kindSelect()).toBeVisible();

    await notes.kindSelect().selectOption("question");

    await Promise.all([
      page.waitForResponse(
        (response) =>
          response.url().includes(`/api/knowledge-notes/${seededNote.id}`) &&
          response.request().method() === "PATCH" &&
          response.ok(),
      ),
      page.getByRole("button", { name: "Notiz speichern" }).click(),
    ]);

    await page.reload();
    await dashboard.waitForReady();
    await notes.openNoteByTitle(seededNote.title);
    await notes.waitForEditorOpen();

    await expect(notes.kindSelect()).toHaveValue("question");
    await expect(notes.kindSelect().locator("option:checked")).toHaveText("Frage");
  });

  test("dashboard shows the knowledge graph when notes exist", async ({
    authenticatedPage: page,
    seededNote: _,
  }) => {
    const { dashboard } = await openDashboard(page);

    await expect(dashboard.graphPanel()).toBeVisible();
    await expect(
      dashboard.graphPanel().getByRole("heading", { name: "Wissensgraph" }),
    ).toBeVisible();
    await expect(dashboard.graphNodes().first()).toBeVisible({ timeout: 10_000 });
  });

  // TODO(kk-dws): Add stable E2E coverage for note linking with a dedicated two-note API helper.
});
