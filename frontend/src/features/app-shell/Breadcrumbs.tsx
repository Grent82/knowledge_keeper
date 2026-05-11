import type { Category } from "./types";

type BreadcrumbsProps = {
  categories: Category[];
  selectedCategoryId: number | null;
  onSelectCategory: (categoryId: number | null) => void;
};

export function Breadcrumbs({
  categories,
  selectedCategoryId,
  onSelectCategory,
}: BreadcrumbsProps) {
  if (!selectedCategoryId) {
    return null;
  }

  const categoryById = new Map(categories.map((category) => [category.id, category]));
  const trail: Category[] = [];
  let current = categoryById.get(selectedCategoryId) ?? null;

  while (current) {
    trail.unshift(current);
    current = current.parent ? categoryById.get(current.parent) ?? null : null;
  }

  return (
    <nav className="breadcrumbs" aria-label="Category breadcrumb">
      <button className="breadcrumb-button" onClick={() => onSelectCategory(null)} type="button">
        All
      </button>
      {trail.map((category) => (
        <button
          key={category.id}
          className="breadcrumb-button"
          onClick={() => onSelectCategory(category.id)}
          type="button"
        >
          / {category.name}
        </button>
      ))}
    </nav>
  );
}
