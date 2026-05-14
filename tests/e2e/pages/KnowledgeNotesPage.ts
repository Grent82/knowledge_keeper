import type { Page } from "@playwright/test";

/**
 * Encapsulates the KnowledgeNoteList + KnowledgeNoteEditor panel pair.
 *
 * The list is always visible on the dashboard; the editor slides in when
 * a note is selected or "Neue Notiz" is clicked.
 */
export class KnowledgeNotesPage {
  constructor(private readonly page: Page) {}

  // ── List ──────────────────────────────────────────────────────────────────

  noteList() {
    return this.page.locator("article.card").filter({ has: this.page.getByRole("heading", { name: "Wissensnotizen" }) });
  }

  emptyStateMessage() {
    // Scoped to the knowledge notes card to avoid matching other empty-state paragraphs.
    return this.noteList().locator(".empty-state");
  }

  noteItems() {
    return this.noteList().locator(".simple-list .list-button");
  }

  async openNoteByTitle(title: string) {
    await this.page.getByRole("button", { name: title }).click();
  }

  async clickNewNote() {
    await this.page.getByRole("button", { name: "Neue Notiz" }).click();
  }

  // ── Editor ────────────────────────────────────────────────────────────────

  editorHeading() {
    return this.page.getByRole("heading", { name: /Wissensnotiz bearbeiten|Neue Wissensnotiz/ });
  }

  editorTitleInput() {
    return this.page.getByLabel(/Titel/i);
  }

  async waitForEditorOpen() {
    await this.editorHeading().waitFor({ timeout: 8_000 });
  }
}
