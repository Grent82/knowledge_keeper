import type { Category } from "./types";

type CategoryManagerProps = {
  categories: Category[];
  error: string;
  onSubmit: (name: string, parentId: number | null) => Promise<void>;
};

function buildCategoryLabel(categories: Category[], category: Category): string {
  const categoryById = new Map(categories.map((entry) => [entry.id, entry]));
  const path: string[] = [category.name];
  let currentParentId = category.parent;

  while (currentParentId !== null) {
    const parent = categoryById.get(currentParentId);
    if (!parent) {
      break;
    }
    path.unshift(parent.name);
    currentParentId = parent.parent;
  }

  return path.join(" / ");
}

export function CategoryManager({
  categories,
  error,
  onSubmit,
}: CategoryManagerProps) {
  const sortedCategories = [...categories].sort((left, right) =>
    buildCategoryLabel(categories, left).localeCompare(buildCategoryLabel(categories, right)),
  );

  return (
    <article className="card">
      <h2>Manage Categories</h2>
      <p className="muted">Create hierarchical categories for navigation and filtering.</p>
      <form
        className="stack-form"
        action={async (formData) => {
          const name = String(formData.get("name") ?? "").trim();
          const parentRaw = String(formData.get("parent") ?? "");
          const parentId = parentRaw ? Number(parentRaw) : null;

          if (!name) {
            return;
          }

          await onSubmit(name, Number.isNaN(parentId) ? null : parentId);
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
        <button type="submit">Create category</button>
      </form>
    </article>
  );
}
