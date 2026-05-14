import type { Page } from "@playwright/test";

/**
 * Represents the authenticated dashboard shell.
 *
 * The dashboard is a single-page layout; sub-sections are accessed by
 * navigating to the relevant panel, not by full-page navigation.
 */
export class DashboardPage {
  constructor(private readonly page: Page) {}

  /** Wait until the dashboard has rendered (knowledge notes heading is a reliable anchor). */
  async waitForReady() {
    await this.page.waitForSelector("h2:text('Wissensnotizen')", { timeout: 15_000 });
  }

  /** Heading that identifies the logged-in user or the session status. */
  logoutButton() {
    return this.page.getByRole("button", { name: /abmelden|logout|sign out/i });
  }

  knowledgeNotesHeading() {
    return this.page.getByRole("heading", { name: "Wissensnotizen" }).first();
  }

  newNoteButton() {
    return this.page.getByRole("button", { name: "Neue Notiz" });
  }
}
