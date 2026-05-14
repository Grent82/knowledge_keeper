import { useState } from "react";
import ReactMarkdown from "react-markdown";

import { ApiError, postCoachQuestion } from "./api";
import { CONTEXT_TAGS } from "./contextTags";
import type { CoachCitedSegment, CoachHistoryEntry } from "./types";

type CoachMessage = {
  role: "user" | "assistant";
  content: string;
  responseMode?: "grounded_answer" | "sources_only";
  sourceSemantics?: "related_sources";
  citedSegments?: CoachCitedSegment[];
};

type CoachPanelProps = {
  mediaTitleById: Map<number, string>;
};

function formatTimestamp(value: string | null): string | null {
  if (!value) {
    return null;
  }

  const totalSeconds = Number.parseFloat(value);
  if (Number.isNaN(totalSeconds)) {
    return null;
  }

  const minutes = Math.floor(totalSeconds / 60);
  const seconds = Math.floor(totalSeconds % 60);
  return `${minutes}:${seconds.toString().padStart(2, "0")}`;
}

export function CoachPanel({ mediaTitleById }: CoachPanelProps) {
  const [draft, setDraft] = useState("");
  const [contextTag, setContextTag] = useState("");
  const [messages, setMessages] = useState<CoachMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const question = draft.trim();
    if (!question || isLoading) {
      return;
    }

    const history: CoachHistoryEntry[] = messages
      .slice(-5)
      .map((message) => ({ role: message.role, content: message.content }));

    setIsLoading(true);
    setError("");

    try {
      const response = await postCoachQuestion(question, history, contextTag);
      setMessages((currentMessages) => [
        ...currentMessages,
        { role: "user", content: question },
        {
          role: "assistant",
          content: response.answer,
          responseMode: response.response_mode,
          sourceSemantics: response.source_semantics,
          citedSegments: response.cited_segments,
        },
      ]);
      setDraft("");
    } catch (nextError) {
      setError(
        nextError instanceof ApiError
          ? nextError.message
          : "Coach-Antwort konnte nicht geladen werden.",
      );
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <section className="card coach-card">
      <div className="coach-header">
        <div>
          <p className="eyebrow">Coach</p>
          <h2>Frage auf Basis deiner Quellen</h2>
        </div>
        {isLoading ? <span className="coach-status">Antwort wird vorbereitet…</span> : null}
      </div>
      <p className="muted coach-intro">
        Stelle eine konkrete Frage. Der Coach gibt dir eine vorsichtige, quellenbasierte
        Orientierung oder zeigt dir passende Quellen aus deiner Sammlung.
      </p>

      <form className="stack-form" onSubmit={(event) => void handleSubmit(event)}>
        <label className="field" style={{ marginBottom: "0.5rem" }}>
          <span className="muted" style={{ fontSize: "0.8rem" }}>
            Meine aktuelle Situation (optional)
          </span>
          <select value={contextTag} onChange={(event) => setContextTag(event.target.value)}>
            <option value="">Kein Kontext gewählt</option>
            {CONTEXT_TAGS.map((tag) => (
              <option key={tag} value={tag}>
                {tag.replace("kontext:", "")}
              </option>
            ))}
          </select>
        </label>
        <label className="field">
          <span>Frage</span>
          <textarea
            name="question"
            placeholder="Zum Beispiel: Wie kann ich fokussierter lernen?"
            rows={3}
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
          />
        </label>
        <div className="coach-actions">
          <button disabled={isLoading || draft.trim().length === 0} type="submit">
            {isLoading ? "Antwortet…" : "Coach fragen"}
          </button>
        </div>
        {error ? <p className="error-text">{error}</p> : null}
      </form>

      <div aria-live="polite" className="coach-thread">
        {messages.length === 0 ? (
          <p className="empty-state">Noch keine Frage gestellt.</p>
        ) : (
          messages.map((message, index) => (
            <article
              className={`coach-message coach-message-${message.role}`}
              key={`${message.role}-${index}`}
            >
              <p className="coach-role">{message.role === "user" ? "Du" : "Coach"}</p>
              {message.role === "assistant" ? (
                <div className="coach-markdown">
                  {message.responseMode === "sources_only" ? (
                    <p className="coach-mode-note">
                      Begrenzter Modus: aktuell werden passende Quellen gezeigt statt einer voll
                      ausformulierten Coach-Antwort.
                    </p>
                  ) : null}
                  <ReactMarkdown>{message.content}</ReactMarkdown>
                </div>
              ) : (
                <p>{message.content}</p>
              )}
              {message.role === "assistant" && message.citedSegments ? (
                <div className="coach-citations">
                  <p className="coach-citations-label">
                    {message.sourceSemantics === "related_sources"
                      ? "Passende Quellen"
                      : "Quellen"}
                  </p>
                  {message.citedSegments.length === 0 ? (
                    <p className="muted">Keine passenden Quellen verfuegbar.</p>
                  ) : (
                    message.citedSegments.map((segment) => {
                      const mediaTitle =
                        mediaTitleById.get(segment.media_item_id) ??
                        `Media Item #${segment.media_item_id}`;
                      const timestamp = formatTimestamp(segment.start_seconds);

                      return (
                        <div className="coach-citation-card" key={segment.segment_id}>
                          <div className="coach-citation-meta">
                            <strong>{mediaTitle}</strong>
                            {timestamp ? <span>{timestamp}</span> : null}
                          </div>
                          <p>{segment.snippet}</p>
                        </div>
                      );
                    })
                  )}
                </div>
              ) : null}
            </article>
          ))
        )}
      </div>
    </section>
  );
}
