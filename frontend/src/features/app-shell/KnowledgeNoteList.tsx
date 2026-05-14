import { useEffect, useMemo, useState } from "react";

import type { KnowledgeNote } from "./types";
import { formatKnowledgeNoteKind, formatKnowledgeNoteTitle } from "./knowledgeNotePresentation";

type KnowledgeNoteListProps = {
  notes: KnowledgeNote[];
  onSelect: (note: KnowledgeNote) => void;
  onCreate: () => void;
};

function formatUpdatedAt(value: string): string {
  return new Date(value).toLocaleString();
}

export function KnowledgeNoteList({ notes, onSelect, onCreate }: KnowledgeNoteListProps) {
  const [query, setQuery] = useState("");
  const filteredNotes = useMemo(() => {
    const normalizedQuery = query.trim().toLocaleLowerCase();
    if (!normalizedQuery) {
      return notes;
    }

    return notes.filter((note) => {
      const title = formatKnowledgeNoteTitle(note.title).toLocaleLowerCase();
      const content = note.content_markdown.toLocaleLowerCase();
      return title.includes(normalizedQuery) || content.includes(normalizedQuery);
    });
  }, [notes, query]);

  useEffect(() => {
    setQuery("");
  }, [notes]);

  return (
    <article className="card">
      <div className="card-header">
        <div>
          <h2>Wissensnotizen</h2>
          <p className="muted">Markdown-Notizen des Owners mit Verlinkungen und Kontextbezug.</p>
        </div>
        <button onClick={onCreate} type="button">
          Neue Notiz
        </button>
      </div>
      {notes.length === 0 ? (
        <p className="empty-state">Noch keine Wissensnotizen vorhanden.</p>
      ) : (
        <>
          <input
            aria-label="Notizen durchsuchen"
            className="search-input"
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Notizen durchsuchen…"
            type="search"
            value={query}
          />
          {filteredNotes.length === 0 ? (
            <p className="empty-state">Keine Notizen gefunden.</p>
          ) : (
            <ul className="simple-list compact-list">
              {filteredNotes.map((note) => (
                <li key={note.id}>
                  <button className="list-button media-list-button" onClick={() => onSelect(note)} type="button">
                    <span className="knowledge-note-title-row">
                      <strong>{formatKnowledgeNoteTitle(note.title)}</strong>
                      <span className="tag">{formatKnowledgeNoteKind(note.kind)}</span>
                    </span>
                    {note.core_insight ? (
                      <span className="note-subtitle muted">
                        {note.core_insight.length > 80
                          ? `${note.core_insight.slice(0, 80)}…`
                          : note.core_insight}
                      </span>
                    ) : null}
                    {note.first_step ? (
                      <span className="note-action-badge">▶ Schritt vorhanden</span>
                    ) : null}
                    {note.context_tags && note.context_tags.length > 0 ? (
                      <span className="note-chip-list compact">
                        {note.context_tags.slice(0, 3).map((tag) => (
                          <span className="note-chip tag small" key={tag}>
                            {tag.replace("kontext:", "")}
                          </span>
                        ))}
                        {note.context_tags.length > 3 ? (
                          <span className="note-chip tag small muted">+{note.context_tags.length - 3}</span>
                        ) : null}
                      </span>
                    ) : null}
                    <span className="muted">Aktualisiert: {formatUpdatedAt(note.updated_at)}</span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </>
      )}
    </article>
  );
}
