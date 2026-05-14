import { defineConfig, devices } from "@playwright/test";

/**
 * Base URL of the running frontend dev server.
 * Override with E2E_BASE_URL when the default port 3000 is taken.
 * Backend is accessed via the Vite proxy on the same origin — no extra config needed.
 */
const baseURL = process.env.E2E_BASE_URL ?? "http://localhost:3000";

export default defineConfig({
  testDir: "./tests/e2e",
  testMatch: "**/*.spec.ts",

  /* Run tests in parallel within each file — adjust if tests share DB state */
  fullyParallel: false,
  workers: 1,

  /* Fail the CI run if tests are accidentally left in .only() */
  forbidOnly: !!process.env.CI,

  /* Retry flaky tests once in CI, never locally */
  retries: process.env.CI ? 1 : 0,

  /* Reporters: list for terminal, HTML for local debugging */
  reporter: [["list"], ["html", { outputFolder: "playwright-report", open: "never" }]],

  use: {
    baseURL,
    /* Collect trace on first retry so we can debug CI failures */
    trace: "on-first-retry",
    /* Screenshots on failure */
    screenshot: "only-on-failure",
    /* Short action timeout — don't wait forever for UI actions */
    actionTimeout: 10_000,
  },

  /* Only Chromium initially — add webkit/firefox later when foundation is stable */
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],

  /*
   * E2E tests require pre-started servers.
   * Run both before executing the suite:
   *
   *   Backend:  .venv/bin/python backend/manage.py runserver
   *   Frontend: pnpm --filter @knowledge-keeper/frontend dev
   *
   * See: make e2e
   */
});
