import type { Category } from "./types";

export function buildCategoryLabel(categories: Category[], category: Category): string {
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
