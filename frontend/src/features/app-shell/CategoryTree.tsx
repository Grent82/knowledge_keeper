import type { Category } from "./types";

type CategoryTreeProps = {
  categories: Category[];
  selectedCategoryId: number | null;
  onSelectCategory: (categoryId: number | null) => void;
  variant?: "card" | "sidebar";
};

type CategoryNode = Category & {
  children: CategoryNode[];
};

function buildTree(categories: Category[]): CategoryNode[] {
  const lookup = new Map<number, CategoryNode>();
  const roots: CategoryNode[] = [];

  for (const category of categories) {
    lookup.set(category.id, { ...category, children: [] });
  }

  for (const category of lookup.values()) {
    if (category.parent && lookup.has(category.parent)) {
      lookup.get(category.parent)?.children.push(category);
    } else {
      roots.push(category);
    }
  }

  return roots.sort((left, right) => left.name.localeCompare(right.name));
}

function TreeNode({
  node,
  selectedCategoryId,
  onSelectCategory,
}: {
  node: CategoryNode;
  selectedCategoryId: number | null;
  onSelectCategory: (categoryId: number | null) => void;
}) {
  return (
    <li>
      <button
        className={selectedCategoryId === node.id ? "tree-button active-tree-button" : "tree-button"}
        onClick={() => onSelectCategory(node.id)}
        type="button"
      >
        {node.name}
      </button>
      {node.children.length > 0 ? (
        <ul className="tree-list">
          {node.children
            .sort((left, right) => left.name.localeCompare(right.name))
            .map((child) => (
              <TreeNode
                key={child.id}
                node={child}
                onSelectCategory={onSelectCategory}
                selectedCategoryId={selectedCategoryId}
              />
            ))}
        </ul>
      ) : null}
    </li>
  );
}

export function CategoryTree({
  categories,
  selectedCategoryId,
  onSelectCategory,
  variant = "card",
}: CategoryTreeProps) {
  const roots = buildTree(categories);
  const classes = variant === "sidebar" ? "tree-card tree-card-sidebar" : "card tree-card";

  return (
    <section className={classes}>
      <div className="tree-header">
        <h2>Categories</h2>
        <button className="secondary-button" onClick={() => onSelectCategory(null)} type="button">
          All
        </button>
      </div>
      {roots.length === 0 ? (
        <p className="empty-state">No categories yet.</p>
      ) : (
        <ul className="tree-list">
          {roots.map((root) => (
            <TreeNode
              key={root.id}
              node={root}
              onSelectCategory={onSelectCategory}
              selectedCategoryId={selectedCategoryId}
            />
          ))}
        </ul>
      )}
    </section>
  );
}
