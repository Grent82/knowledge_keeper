import { useEffect, useMemo, useState } from "react";
import ReactMarkdown from "react-markdown";

import { createKnowledgeNote, updateKnowledgeNote } from "./api";
import { formatKnowledgeNoteTitle } from "./knowledgeNotePresentation";
import type { KnowledgeNote } from "./types";

type KnowledgeNoteEditorProps = {
  note: KnowledgeNote | null;
  allNotes: KnowledgeNote[];
  initialMediaItemId?: number | null;
  initialTranscriptId?: number | null;
  onDelete?: (noteId: number) => Promise<void>;
  onSave: (note: KnowledgeNote) => void;
  onClose: () => void;
};

export function KnowledgeNoteEditor({
  note,
  allNotes,
  initialMediaItemId = null,
  initialTranscriptId = null,
  onDelete,
  onSave,
  onClose,
}: KnowledgeNoteEditorProps) {
  const [title, setTitle] = useState(note ? formatKnowledgeNoteTitle(note.title) : "");
  const [contentMarkdown, setContentMarkdown] = useState(note?.content_markdown ?? "");
  const [previewMode, setPreviewMode] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const linkedNotes = useMemo(
    () =>
      (note?.linked_notes ?? []).map((linkedNoteId) => {
        const linkedNote = allNotes.find((candidate) => candidate.id === linkedNoteId);
        return linkedNote ? formatKnowledgeNoteTitle(linkedNote.title) : `Notiz #${linkedNoteId}`;
      }),
    [allNotes, note?.linked_notes],
  );

  useEffect(() => {
    setTitle(note ? formatKnowledgeNoteTitle(note.title) : "");
    setContentMarkdown(note?.content_markdown ?? "");
    setPreviewMode(false);
    setError("");
  }, [note]);

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
          })
        : await createKnowledgeNote({
            title: trimmedTitle,
            content_markdown: contentMarkdown,
            media_item: initialMediaItemId,
            transcript: initialTranscriptId,
            linked_notes: [],
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
        {linkedNotes.length > 0 ? (
          <div className="note-chip-list">
            {linkedNotes.map((linkedTitle) => (
              <span className="note-chip" key={linkedTitle}>
                {linkedTitle}
              </span>
            ))}
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
