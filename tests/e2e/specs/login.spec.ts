/**
 * Acceptance tests: Login flow
 *
 * User story:
 *   As a user, I can sign in with valid credentials and see the dashboard.
 *   If credentials are wrong, I see an error message and stay on the login screen.
 */

import { test, expect } from "@playwright/test";
import { LoginPage } from "../pages/LoginPage";
import { DashboardPage } from "../pages/DashboardPage";

const VALID_USER = process.env.E2E_USERNAME ?? "owner";
const VALID_PASS = process.env.E2E_PASSWORD ?? "secret";

test.describe("Login flow", () => {
  test("valid credentials → dashboard renders", async ({ page }) => {
    const loginPage = new LoginPage(page);
    const dashboard = new DashboardPage(page);

    await loginPage.goto();

    // The login form must be visible before we interact.
    await expect(page.getByRole("button", { name: "Sign in" })).toBeVisible();

    await loginPage.login(VALID_USER, VALID_PASS);
    await dashboard.waitForReady();

    // Dashboard is present — knowledge notes section heading is the anchor.
    await expect(dashboard.knowledgeNotesHeading()).toBeVisible();
  });

  test("invalid credentials → error shown, stays on login", async ({ page }) => {
    const loginPage = new LoginPage(page);

    await loginPage.goto();
    await loginPage.login(VALID_USER, "wrong-password");

    // Error text must appear.
    const error = await loginPage.errorText();
    expect(error).not.toBeNull();
    expect(error!.length).toBeGreaterThan(0);

    // The login button must still be there — we have not left the login screen.
    await expect(page.getByRole("button", { name: "Sign in" })).toBeVisible();
  });

  test("login form elements are labelled for accessibility", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByLabel("Username")).toBeVisible();
    await expect(page.getByLabel("Password")).toBeVisible();
    await expect(page.getByRole("button", { name: "Sign in" })).toBeVisible();
  });
});
