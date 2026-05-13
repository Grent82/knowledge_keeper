import { describe, expect, it } from "vitest";

import { formatKnowledgeNoteTitle } from "./knowledgeNotePresentation";

describe("formatKnowledgeNoteTitle", () => {
  it("removes visible stub prefixes from generated note titles", () => {
    expect(formatKnowledgeNoteTitle("[Stub] Reflexionsfrage")).toBe("Reflexionsfrage");
  });

  it("keeps regular note titles unchanged", () => {
    expect(formatKnowledgeNoteTitle("Eigene Beobachtung")).toBe("Eigene Beobachtung");
  });
});
