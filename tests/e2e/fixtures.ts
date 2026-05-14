import { test as baseTest, request as baseRequest } from "@playwright/test";

/**
 * E2E fixture layer for Knowledge Keeper.
 *
 * Two key fixtures:
 *   - `authenticatedPage`  — a Page that is already logged in as the owner.
 *                            Session is established once per worker via API
 *                            (no UI login overhead).
 *   - `seededNote`         — creates a KnowledgeNote via DRF before the test
 *                            and deletes it afterwards.
 *
 * Configuration (via environment variables or defaults):
 *   E2E_BASE_URL      Frontend URL  (default: http://localhost:3000)
 *   E2E_API_URL       Backend URL   (default: http://localhost:8000)
 *   E2E_USERNAME      Owner account (default: owner)
 *   E2E_PASSWORD      Owner password(default: secret)
 */

const BASE_URL = process.env.E2E_BASE_URL ?? "http://localhost:3000";
const API_URL = process.env.E2E_API_URL ?? "http://localhost:8000";
const E2E_USERNAME = process.env.E2E_USERNAME ?? "owner";
const E2E_PASSWORD = process.env.E2E_PASSWORD ?? "secret";

// ---------------------------------------------------------------------------
// Shared auth session — built once per worker, reused by all tests in a file.
// ---------------------------------------------------------------------------

type AuthState = {
  cookies: Array<{ name: string; value: string; domain: string; path: string }>;
  csrfToken: string;
};

let cachedAuthState: AuthState | null = null;

async function buildAuthState(): Promise<AuthState> {
  if (cachedAuthState) return cachedAuthState;

  const ctx = await baseRequest.newContext({ baseURL: API_URL });

  // 1. Fetch session endpoint — Django sets the csrftoken cookie on first hit.
  await ctx.get("/api/auth/session");

  // 2. Log in. LoginView bypasses CSRF enforcement (authentication_classes=[]).
  const loginResponse = await ctx.post("/api/auth/login", {
    data: { username: E2E_USERNAME, password: E2E_PASSWORD },
  });

  if (!loginResponse.ok()) {
    const body = await loginResponse.text();
    throw new Error(`Login fixture failed (${loginResponse.status()}): ${body}`);
  }

  // 3. Fetch session again — Django may refresh the csrftoken after login.
  await ctx.get("/api/auth/session");

  const rawCookies = await ctx.storageState();
  const csrfCookie = rawCookies.cookies.find((c) => c.name === "csrftoken");
  const csrfToken = csrfCookie?.value ?? "";

  // Map to a minimal cookie shape accepted by Playwright's addCookies().
  const cookies = rawCookies.cookies.map((c) => ({
    name: c.name,
    value: c.value,
    domain: c.domain,
    path: c.path,
  }));

  await ctx.dispose();

  cachedAuthState = { cookies, csrfToken };
  return cachedAuthState;
}

// ---------------------------------------------------------------------------
// Typed fixture extensions
// ---------------------------------------------------------------------------

type KnowledgeNoteFixtures = {
  /** A Page with the owner session pre-loaded — no login form is shown. */
  authenticatedPage: import("@playwright/test").Page;
  /**
   * A KnowledgeNote created via API before the test.
   * Automatically deleted via API after the test completes.
   */
  seededNote: { id: number; title: string };
};

export const test = baseTest.extend<KnowledgeNoteFixtures>({
  // ── authenticatedPage ────────────────────────────────────────────────────
  authenticatedPage: async ({ browser }, use) => {
    const authState = await buildAuthState();

    const context = await browser.newContext({ baseURL: BASE_URL });
    await context.addCookies(authState.cookies);

    const page = await context.newPage();
    await use(page);

    await context.close();
  },

  // ── seededNote ────────────────────────────────────────────────────────────
  seededNote: async ({ authenticatedPage: _ }, use) => {
    // `_` ensures authenticatedPage is set up first so auth cookies are cached.
    const authState = await buildAuthState();

    const ctx = await baseRequest.newContext({
      baseURL: API_URL,
      extraHTTPHeaders: {
        "X-CSRFToken": authState.csrfToken,
        "Content-Type": "application/json",
        Referer: BASE_URL,
      },
    });

    // Replay auth cookies into the API context.
    await ctx.storageState(); // prime internal state
    for (const cookie of authState.cookies) {
      // We set them via the Cookie header since APIRequestContext doesn't have addCookies().
    }

    // Re-login to get a fresh session in this API context (session cookies are per-context).
    await ctx.get("/api/auth/session");
    await ctx.post("/api/auth/login", {
      data: { username: E2E_USERNAME, password: E2E_PASSWORD },
    });
    await ctx.get("/api/auth/session");

    // Refresh CSRF after login in this context.
    const freshState = await ctx.storageState();
    const csrfToken =
      freshState.cookies.find((c) => c.name === "csrftoken")?.value ?? authState.csrfToken;

    const createResponse = await ctx.post("/api/knowledge-notes/", {
      headers: { "X-CSRFToken": csrfToken },
      data: {
        title: "E2E Testnotiz",
        content_markdown: "Testinhalt für E2E-Tests.",
      },
    });

    if (!createResponse.ok()) {
      const body = await createResponse.text();
      await ctx.dispose();
      throw new Error(`seededNote fixture failed (${createResponse.status()}): ${body}`);
    }

    const note = await createResponse.json() as { id: number; title: string };
    await use(note);

    // Teardown — delete the note.
    const deleteState = await ctx.storageState();
    const deleteCsrf =
      deleteState.cookies.find((c) => c.name === "csrftoken")?.value ?? csrfToken;
    await ctx.delete(`/api/knowledge-notes/${note.id}`, {
      headers: { "X-CSRFToken": deleteCsrf },
    });

    await ctx.dispose();
  },
});

export { expect } from "@playwright/test";
