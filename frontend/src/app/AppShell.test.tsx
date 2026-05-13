import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { AppShell } from "./AppShell";

describe("AppShell", () => {
  it("renders the wide dashboard shell class", () => {
    const markup = renderToStaticMarkup(
      <AppShell>
        <div>content</div>
      </AppShell>,
    );

    expect(markup).toContain('class="app-shell app-shell-wide"');
  });
});
