import { useEffect, useMemo, useState } from "react";

import { CONTEXT_TAGS } from "./contextTags";
import { formatKnowledgeNoteKind, formatKnowledgeNoteTitle } from "./knowledgeNotePresentation";
import type { KnowledgeNote } from "./types";

type KnowledgeNoteListProps = {
  notes: KnowledgeNote[];
  onSelect: (note: KnowledgeNote) => void;
  onCreate: () => void;
};

function formatUpdatedAt(value: string): string {
  return new Date(value).toLocaleString();
}

export function KnowledgeNoteList({ notes, onSelect, onCreate }: KnowledgeNoteListProps) {
  const [filterText, setFilterText] = useState("");
  const [activeTag, setActiveTag] = useState<string | null>(null);

  const availableTags = useMemo(() => {
    const usedTags = new Set(notes.flatMap((note) => note.context_tags ?? []));
    const orderedKnownTags = CONTEXT_TAGS.filter((tag) => usedTags.has(tag));
    const additionalTags = [...usedTags].filter((tag) => !CONTEXT_TAGS.includes(tag));
    return [...orderedKnownTags, ...additionalTags];
  }, [notes]);

  const filteredNotes = useMemo(() => {
    const normalizedFilterText = filterText.trim().toLocaleLowerCase();

    return notes.filter((note) => {
      const matchesText =
        !normalizedFilterText ||
        formatKnowledgeNoteTitle(note.title).toLocaleLowerCase().includes(normalizedFilterText) ||
        (note.content_markdown ?? "").toLocaleLowerCase().includes(normalizedFilterText);
      const matchesTag = !activeTag || (note.context_tags ?? []).includes(activeTag);
      return matchesText && matchesTag;
    });
  }, [activeTag, filterText, notes]);

  useEffect(() => {
    setFilterText("");
    setActiveTag(null);
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
          {availableTags.length > 0 ? (
            <div className="note-chip-list tag-filter-bar">
              <button
                className={`tag-filter-chip${activeTag === null ? " active" : ""}`}
                onClick={() => setActiveTag(null)}
                type="button"
              >
                Alle
              </button>
              {availableTags.map((tag) => (
                <button
                  className={`tag-filter-chip${activeTag === tag ? " active" : ""}`}
                  key={tag}
                  onClick={() => setActiveTag((currentTag) => (currentTag === tag ? null : tag))}
                  type="button"
                >
                  {tag.replace("kontext:", "")}
                </button>
              ))}
            </div>
          ) : null}
          <input
            aria-label="Notizen durchsuchen"
            className="search-input"
            onChange={(event) => setFilterText(event.target.value)}
            placeholder="Notizen durchsuchen…"
            type="search"
            value={filterText}
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
