import { describe, expect, it } from "vitest";

import { formatKnowledgeNoteKind, formatKnowledgeNoteTitle } from "./knowledgeNotePresentation";

describe("formatKnowledgeNoteTitle", () => {
  it("removes visible stub prefixes from generated note titles", () => {
    expect(formatKnowledgeNoteTitle("[Stub] Reflexionsfrage")).toBe("Reflexionsfrage");
  });

  it("keeps regular note titles unchanged", () => {
    expect(formatKnowledgeNoteTitle("Eigene Beobachtung")).toBe("Eigene Beobachtung");
  });
});

describe("formatKnowledgeNoteKind", () => {
  it("translates note kinds for the UI", () => {
    expect(formatKnowledgeNoteKind("insight")).toBe("Erkenntnis");
  });

  it("falls back to Allgemein for unknown kinds", () => {
    expect(formatKnowledgeNoteKind("unknown")).toBe("Allgemein");
  });
});
