import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";

import {
  createKnowledgeNote,
  fetchRelatedNotes,
  type RelatedNote,
  updateKnowledgeNote,
} from "./api";
import { formatKnowledgeNoteTitle, KIND_LABELS } from "./knowledgeNotePresentation";
import type { KnowledgeNote } from "./types";

type KnowledgeNoteEditorProps = {
  note: KnowledgeNote | null;
  allNotes: KnowledgeNote[];
  initialMediaItemId?: number | null;
  initialTranscriptId?: number | null;
  onDelete?: (noteId: number) => Promise<void>;
  onSave: (note: KnowledgeNote) => void;
  onClose: () => void;
  onNavigateToNote?: (note: KnowledgeNote) => void;
};

export function KnowledgeNoteEditor({
  note,
  allNotes,
  initialMediaItemId = null,
  initialTranscriptId = null,
  onDelete,
  onSave,
  onClose,
  onNavigateToNote,
}: KnowledgeNoteEditorProps) {
  const [title, setTitle] = useState(note ? formatKnowledgeNoteTitle(note.title) : "");
  const [contentMarkdown, setContentMarkdown] = useState(note?.content_markdown ?? "");
  const [kind, setKind] = useState(note?.kind ?? "general");
  const [linkedNoteIds, setLinkedNoteIds] = useState<number[]>(note?.linked_notes ?? []);
  const [linkPickerValue, setLinkPickerValue] = useState("");
  const [previewMode, setPreviewMode] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [relatedNotes, setRelatedNotes] = useState<RelatedNote[]>([]);

  const linkableNotes = allNotes.filter(
    (n) => n.id !== note?.id && !linkedNoteIds.includes(n.id),
  );
  const hasTransformationFields = Boolean(
    note?.problem ||
      note?.core_insight ||
      note?.application ||
      note?.first_step ||
      note?.deeper_principle ||
      (note?.context_tags && note.context_tags.length > 0),
  );

  useEffect(() => {
    setTitle(note ? formatKnowledgeNoteTitle(note.title) : "");
    setContentMarkdown(note?.content_markdown ?? "");
    setKind(note?.kind ?? "general");
    setLinkedNoteIds(note?.linked_notes ?? []);
    setLinkPickerValue("");
    setPreviewMode(false);
    setError("");
  }, [note]);

  useEffect(() => {
    let cancelled = false;

    if (note?.id && note.deeper_principle) {
      fetchRelatedNotes(note.id)
        .then((nextRelatedNotes) => {
          if (!cancelled) {
            setRelatedNotes(nextRelatedNotes);
          }
        })
        .catch(() => {
          if (!cancelled) {
            setRelatedNotes([]);
          }
        });
    } else {
      setRelatedNotes([]);
    }

    return () => {
      cancelled = true;
    };
  }, [note]);

  function handleAddLink(): void {
    const id = parseInt(linkPickerValue, 10);
    if (!id || linkedNoteIds.includes(id)) return;
    setLinkedNoteIds((prev) => [...prev, id]);
    setLinkPickerValue("");
  }

  function handleRemoveLink(id: number): void {
    setLinkedNoteIds((prev) => prev.filter((n) => n !== id));
  }

  async function handleSave(): Promise<void> {
    const trimmedTitle = title.trim();
    if (!trimmedTitle) {
      setError("Bitte einen Titel eingeben.");
      return;
    }

    setSaving(true);
    setError("");

    try {
      const savedNote = note
        ? await updateKnowledgeNote(note.id, {
            title: trimmedTitle,
            content_markdown: contentMarkdown,
            kind,
            linked_notes: linkedNoteIds,
          })
        : await createKnowledgeNote({
            title: trimmedTitle,
            content_markdown: contentMarkdown,
            kind,
            media_item: initialMediaItemId,
            transcript: initialTranscriptId,
            linked_notes: linkedNoteIds,
          });
      onSave(savedNote);
    } catch (nextError) {
      setError(nextError instanceof Error ? nextError.message : "Notiz konnte nicht gespeichert werden.");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(): Promise<void> {
    if (!note || !onDelete) {
      return;
    }

    setSaving(true);
    setError("");

    try {
      await onDelete(note.id);
    } catch (nextError) {
      setError(nextError instanceof Error ? nextError.message : "Notiz konnte nicht gelöscht werden.");
      setSaving(false);
    }
  }

  return (
    <article className="card knowledge-note-editor">
      <div className="card-header">
        <div>
          <h2>{note ? "Wissensnotiz bearbeiten" : "Neue Wissensnotiz"}</h2>
          <p className="muted">
            Markdown-first Notizen mit optionalem Medienbezug und Vorschau.
          </p>
        </div>
        <button className="secondary-button" onClick={onClose} type="button">
          Schließen
        </button>
      </div>

      <div className="tab-row">
        <button
          className={previewMode ? "secondary-button" : "tab-button tab-button-active"}
          onClick={() => setPreviewMode(false)}
          type="button"
        >
          Bearbeiten
        </button>
        <button
          className={previewMode ? "tab-button tab-button-active" : "secondary-button"}
          onClick={() => setPreviewMode(true)}
          type="button"
        >
          Vorschau
        </button>
      </div>

      <div className="stack-form">
        <label className="field">
          <span>Titel</span>
          <input onChange={(event) => setTitle(event.target.value)} type="text" value={title} />
        </label>
        <label className="field">
          <span>Typ</span>
          <select onChange={(event) => setKind(event.target.value as KnowledgeNote["kind"])} value={kind}>
            {Object.entries(KIND_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </label>
        {previewMode ? (
          <div className="markdown-preview">
            {contentMarkdown.trim() ? (
              <ReactMarkdown>{contentMarkdown}</ReactMarkdown>
            ) : (
              <p className="empty-state">Noch kein Markdown-Inhalt vorhanden.</p>
            )}
          </div>
        ) : (
          <label className="field">
            <span>Markdown</span>
            <textarea
              onChange={(event) => setContentMarkdown(event.target.value)}
              rows={14}
              value={contentMarkdown}
            />
          </label>
        )}
        {hasTransformationFields ? (
          <div className="transformation-section">
            <h3>Transformations-Struktur</h3>

            {note?.problem ? (
              <div className="transformation-field">
                <span className="transformation-label">⚡ Spannung / Problem</span>
                <p>{note.problem}</p>
              </div>
            ) : null}

            {note?.core_insight ? (
              <div className="transformation-field">
                <span className="transformation-label">💡 Kern-Erkenntnis</span>
                <p className="core-insight-text">{note.core_insight}</p>
              </div>
            ) : null}

            {note?.application ? (
              <div className="transformation-field">
                <span className="transformation-label">🎯 Anwendung</span>
                <p>{note.application}</p>
              </div>
            ) : null}

            {note?.first_step ? (
              <div className="transformation-field first-step-field">
                <span className="transformation-label">▶ Erster Schritt</span>
                <p className="first-step-text">{note.first_step}</p>
              </div>
            ) : null}

            {note?.deeper_principle ? (
              <div className="transformation-field">
                <span className="transformation-label">🌐 Tieferes Prinzip</span>
                <p className="deeper-principle-text">{note.deeper_principle}</p>
              </div>
            ) : null}

            {note?.context_tags && note.context_tags.length > 0 ? (
              <div className="transformation-field">
                <span className="transformation-label">🏷 Kontext</span>
                <div className="note-chip-list">
                  {note.context_tags.map((tag) => (
                    <span className="note-chip tag" key={tag}>
                      {tag.replace("kontext:", "")}
                    </span>
                  ))}
                </div>
              </div>
            ) : null}
          </div>
        ) : null}
        {relatedNotes.length > 0 ? (
          <div className="related-notes-section">
            <span className="transformation-label">🔗 Verwandte Erkenntnisse (KI-Vorschlag)</span>
            <ul className="simple-list compact-list">
              {relatedNotes.map((related) => (
                <li key={related.id}>
                  <div className="related-note-row">
                    <div className="related-note-info">
                      <strong>{formatKnowledgeNoteTitle(related.title)}</strong>
                      {related.core_insight ? (
                        <span className="muted" style={{ fontSize: "0.8rem" }}>
                          {related.core_insight.slice(0, 80)}
                          {related.core_insight.length > 80 ? "…" : ""}
                        </span>
                      ) : null}
                    </div>
                    {onNavigateToNote ? (
                      <button
                        className="secondary-button"
                        onClick={() => {
                          const target = allNotes.find((n) => n.id === related.id);
                          if (target) onNavigateToNote(target);
                        }}
                        style={{ fontSize: "0.75rem", padding: "0.2rem 0.5rem" }}
                        type="button"
                      >
                        Öffnen
                      </button>
                    ) : null}
                  </div>
                </li>
              ))}
            </ul>
          </div>
        ) : null}
        {linkedNoteIds.length > 0 || allNotes.length > 1 ? (
          <div className="field">
            <span>Verlinkte Notizen</span>
            <div className="note-chip-list">
              {linkedNoteIds.map((id) => {
                const linked = allNotes.find((n) => n.id === id);
                const label = linked ? formatKnowledgeNoteTitle(linked.title) : `Notiz #${id}`;
                return (
                  <span className="note-chip" key={id}>
                    {onNavigateToNote && linked ? (
                      <button
                        className="chip-link"
                        onClick={() => onNavigateToNote(linked)}
                        type="button"
                      >
                        {label}
                      </button>
                    ) : (
                      label
                    )}
                    <button
                      aria-label={`Verlinkung mit ${label} entfernen`}
                      className="chip-remove"
                      onClick={() => handleRemoveLink(id)}
                      type="button"
                    >
                      ✕
                    </button>
                  </span>
                );
              })}
            </div>
            {linkableNotes.length > 0 ? (
              <div className="inline-actions">
                <select
                  aria-label="Notiz zum Verlinken auswählen"
                  onChange={(e) => setLinkPickerValue(e.target.value)}
                  value={linkPickerValue}
                >
                  <option value="">Notiz auswählen…</option>
                  {linkableNotes.map((n) => (
                    <option key={n.id} value={n.id}>
                      {formatKnowledgeNoteTitle(n.title)}
                    </option>
                  ))}
                </select>
                <button
                  disabled={!linkPickerValue}
                  onClick={handleAddLink}
                  type="button"
                >
                  Verlinkung hinzufügen
                </button>
              </div>
            ) : null}
          </div>
        ) : null}
        {error ? <p className="error-text">{error}</p> : null}
        <div className="inline-actions note-editor-actions">
          <button disabled={saving} onClick={() => void handleSave()} type="button">
            {saving ? "Speichern…" : note ? "Notiz speichern" : "Notiz erstellen"}
          </button>
          {note ? (
            <button
              className="secondary-button"
              disabled={saving}
              onClick={() => void handleDelete()}
              type="button"
            >
              Löschen
            </button>
          ) : null}
        </div>
      </div>
    </article>
  );
}
