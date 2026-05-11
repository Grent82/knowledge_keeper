import { useState } from "react";

import { SubmitButton } from "./SubmitButton";
import type { Tag } from "./types";

type TagManagerProps = {
  error: string;
  onDelete: (id: number) => Promise<void>;
  onSubmit: (name: string) => Promise<void>;
  onUpdate: (id: number, data: { name: string }) => Promise<void>;
  tags: Tag[];
};

export function TagManager({ error, onDelete, onSubmit, onUpdate, tags }: TagManagerProps) {
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editName, setEditName] = useState("");
  const [resetKey, setResetKey] = useState(0);

  return (
    <article className="card">
      <h2>Manage Tags</h2>
      <p className="muted">Create reusable labels that cut across categories and topics.</p>
      <form
        key={resetKey}
        className="stack-form"
        action={async (formData) => {
          const name = String(formData.get("name") ?? "").trim();
          if (!name) {
            return;
          }

          await onSubmit(name);
          setResetKey((currentKey) => currentKey + 1);
        }}
      >
        <label className="field">
          <span>Name</span>
          <input name="name" required type="text" />
        </label>
        {error ? <p className="error-text">{error}</p> : null}
        <SubmitButton pendingLabel="Creating...">Create tag</SubmitButton>
      </form>

      <ul className="simple-list management-list">
        {[...tags].sort((left, right) => left.name.localeCompare(right.name)).map((tag) => {
          const isEditing = editingId === tag.id;
          return (
            <li key={tag.id}>
              {isEditing ? (
                <form
                  className="inline-edit-form"
                  onSubmit={(event) => {
                    event.preventDefault();
                    void onUpdate(tag.id, { name: editName.trim() }).then(() => {
                      setEditingId(null);
                      setEditName("");
                    });
                  }}
                >
                  <input onChange={(event) => setEditName(event.target.value)} type="text" value={editName} />
                  <div className="inline-actions">
                    <button type="submit">Save</button>
                    <button
                      className="secondary-button"
                      onClick={() => {
                        setEditingId(null);
                        setEditName("");
                      }}
                      type="button"
                    >
                      Cancel
                    </button>
                  </div>
                </form>
              ) : (
                <>
                  <strong>{tag.name}</strong>
                  <div className="inline-actions">
                    <button
                      className="secondary-button"
                      onClick={() => {
                        setEditingId(tag.id);
                        setEditName(tag.name);
                      }}
                      type="button"
                    >
                      Edit
                    </button>
                    <button
                      className="secondary-button"
                      onClick={() => {
                        if (window.confirm("Delete this tag?")) {
                          void onDelete(tag.id);
                        }
                      }}
                      type="button"
                    >
                      Delete
                    </button>
                  </div>
                </>
              )}
            </li>
          );
        })}
      </ul>
    </article>
  );
}
