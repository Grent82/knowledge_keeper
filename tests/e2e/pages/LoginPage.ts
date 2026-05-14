import type { Page } from "@playwright/test";

/**
 * Encapsulates interaction with the login screen (unauthenticated root route `/`).
 *
 * Selectors are deliberately role/label-based so they remain valid even when
 * class names or DOM structure change.
 */
export class LoginPage {
  constructor(private readonly page: Page) {}

  async goto() {
    await this.page.goto("/");
  }

  async login(username: string, password: string) {
    await this.page.getByLabel("Username").fill(username);
    await this.page.getByLabel("Password").fill(password);
    await this.page.getByRole("button", { name: "Sign in" }).click();
  }

  /** Returns the visible error text after waiting for it, or null if no error appears. */
  async errorText(timeout = 5_000): Promise<string | null> {
    const errorLocator = this.page.locator(".error-text");
    try {
      await errorLocator.waitFor({ state: "visible", timeout });
      return errorLocator.textContent();
    } catch {
      return null;
    }
  }

  /** Resolves once the page is no longer showing the login form. */
  async waitForRedirectAwayFromLogin() {
    await this.page.waitForSelector(".error-text, h2:text('Wissensnotizen')", {
      timeout: 10_000,
    });
  }
}
