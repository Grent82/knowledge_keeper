import type { Locator, Page } from "@playwright/test";

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
    return this.page.locator("article.card").filter({
      has: this.page.getByRole("heading", { name: "Wissensnotizen" }),
    });
  }

  filterInput() {
    return this.page.getByLabel("Notizen durchsuchen");
  }

  emptyStateMessage() {
    // Scoped to the knowledge notes card to avoid matching other empty-state paragraphs.
    return this.noteList().locator(".empty-state");
  }

  noteItems() {
    return this.noteList().locator(".simple-list .list-button");
  }

  kindBadge(noteButton: Locator) {
    return noteButton.locator(".tag").first();
  }

  async openNoteByTitle(title: string) {
    await this.noteItems().filter({ hasText: title }).first().click();
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

  kindSelect() {
    return this.page.getByLabel("Typ");
  }

  linkSection() {
    return this.page.locator(".field").filter({
      has: this.page.getByText("Verlinkte Notizen", { exact: true }),
    });
  }

  linkPicker() {
    return this.page.getByLabel("Notiz zum Verlinken auswählen");
  }

  addLinkButton() {
    return this.page.getByRole("button", { name: "Verlinkung hinzufügen" });
  }

  linkedChips() {
    return this.page.locator(".note-chip");
  }

  async waitForEditorOpen() {
    await this.editorHeading().waitFor({ timeout: 8_000 });
  }
}
