import { describe, expect, it, vi } from "vitest";

import { postCoachQuestion } from "./api";

describe("postCoachQuestion", () => {
  it("posts the question and history and returns the coach response", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({
          answer: "Arbeite in klaren Fokusbloecken.",
          response_mode: "grounded_answer",
          source_semantics: "related_sources",
          cited_segments: [
            {
              segment_id: 1,
              media_item_id: 2,
              snippet: "Fokus braucht Wiederholung.",
              start_seconds: "12.500",
            },
          ],
        }),
      });

    vi.stubGlobal("fetch", fetchMock);
    vi.stubGlobal("document", {} as Document);
    Object.defineProperty(globalThis.document, "cookie", {
      value: "csrftoken=test-token",
      configurable: true,
    });

    const result = await postCoachQuestion("Wie lerne ich fokussierter?", [
      { role: "user", content: "Ich schweife oft ab." },
    ]);

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/coach/chat/",
      expect.objectContaining({
        method: "POST",
        credentials: "include",
      }),
    );
    expect(result.answer).toContain("Fokus");
    expect(result.response_mode).toBe("grounded_answer");
    expect(result.source_semantics).toBe("related_sources");
    expect(result.cited_segments).toHaveLength(1);
  });
});
