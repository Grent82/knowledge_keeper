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
        <ul className="simple-list compact-list">
          {notes.map((note) => (
            <li key={note.id}>
              <button className="list-button media-list-button" onClick={() => onSelect(note)} type="button">
                <strong>{note.title}</strong>
                <span className="muted">Aktualisiert: {formatUpdatedAt(note.updated_at)}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </article>
  );
}
