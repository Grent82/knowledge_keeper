import { useState } from "react";

import { SubmitButton } from "./SubmitButton";
import { buildCategoryLabel } from "./categoryUtils";
import type { Category } from "./types";

type CategoryManagerProps = {
  categories: Category[];
  error: string;
  onDelete: (id: number) => Promise<void>;
  onSubmit: (name: string, parentId: number | null) => Promise<void>;
  onUpdate: (id: number, data: { name: string; parent: number | null }) => Promise<void>;
};

export function CategoryManager({
  categories,
  error,
  onDelete,
  onSubmit,
  onUpdate,
}: CategoryManagerProps) {
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editName, setEditName] = useState("");
  const [editParent, setEditParent] = useState("");
  const [resetKey, setResetKey] = useState(0);
  const sortedCategories = [...categories].sort((left, right) =>
    buildCategoryLabel(categories, left).localeCompare(buildCategoryLabel(categories, right)),
  );

  return (
    <article className="card">
      <h2>Manage Categories</h2>
      <p className="muted">Create hierarchical categories for navigation and filtering.</p>
      <form
        key={resetKey}
        className="stack-form"
        action={async (formData) => {
          const name = String(formData.get("name") ?? "").trim();
          const parentRaw = String(formData.get("parent") ?? "");
          const parentId = parentRaw ? Number(parentRaw) : null;

          if (!name) {
            return;
          }

          await onSubmit(name, Number.isNaN(parentId) ? null : parentId);
          setResetKey((currentKey) => currentKey + 1);
        }}
      >
        <label className="field">
          <span>Name</span>
          <input name="name" required type="text" />
        </label>
        <label className="field">
          <span>Parent category</span>
          <select defaultValue="" name="parent">
            <option value="">No parent</option>
            {sortedCategories.map((category) => (
              <option key={category.id} value={category.id}>
                {buildCategoryLabel(categories, category)}
              </option>
            ))}
          </select>
        </label>
        {error ? <p className="error-text">{error}</p> : null}
        <SubmitButton pendingLabel="Creating...">Create category</SubmitButton>
      </form>

      <ul className="simple-list management-list">
        {sortedCategories.map((category) => {
          const isEditing = editingId === category.id;
          return (
            <li key={category.id}>
              {isEditing ? (
                <form
                  className="stack-form"
                  onSubmit={(event) => {
                    event.preventDefault();
                    const parentId = editParent ? Number(editParent) : null;
                    void onUpdate(category.id, {
                      name: editName.trim(),
                      parent: Number.isNaN(parentId) ? null : parentId,
                    }).then(() => {
                      setEditingId(null);
                      setEditName("");
                      setEditParent("");
                    });
                  }}
                >
                  <label className="field">
                    <span>Name</span>
                    <input
                      onChange={(event) => setEditName(event.target.value)}
                      type="text"
                      value={editName}
                    />
                  </label>
                  <label className="field">
                    <span>Parent category</span>
                    <select onChange={(event) => setEditParent(event.target.value)} value={editParent}>
                      <option value="">No parent</option>
                      {sortedCategories
                        .filter((option) => option.id !== category.id)
                        .map((option) => (
                          <option key={option.id} value={option.id}>
                            {buildCategoryLabel(categories, option)}
                          </option>
                        ))}
                    </select>
                  </label>
                  <div className="inline-actions">
                    <button type="submit">Save</button>
                    <button
                      className="secondary-button"
                      onClick={() => {
                        setEditingId(null);
                        setEditName("");
                        setEditParent("");
                      }}
                      type="button"
                    >
                      Cancel
                    </button>
                  </div>
                </form>
              ) : (
                <>
                  <strong>{buildCategoryLabel(categories, category)}</strong>
                  <div className="inline-actions">
                    <button
                      className="secondary-button"
                      onClick={() => {
                        setEditingId(category.id);
                        setEditName(category.name);
                        setEditParent(category.parent ? String(category.parent) : "");
                      }}
                      type="button"
                    >
                      Edit
                    </button>
                    <button
                      className="secondary-button"
                      onClick={() => {
                        if (window.confirm("Delete this category?")) {
                          void onDelete(category.id);
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
