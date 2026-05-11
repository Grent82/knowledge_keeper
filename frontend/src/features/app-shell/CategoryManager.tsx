import { useState } from "react";

import { SubmitButton } from "./SubmitButton";
import { buildCategoryLabel } from "./categoryUtils";
import type { Category } from "./types";

type CategoryManagerProps = {
  categories: Category[];
  error: string;
  onSubmit: (name: string, parentId: number | null) => Promise<void>;
};

export function CategoryManager({
  categories,
  error,
  onSubmit,
}: CategoryManagerProps) {
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
    </article>
  );
}
