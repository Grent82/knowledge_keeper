import { SubmitButton } from "./SubmitButton";
import { buildCategoryLabel } from "./categoryUtils";
import type { Category, MediaItem, Tag } from "./types";

type MediaClassificationCardProps = {
  categories: Category[];
  tags: Tag[];
  mediaItem: MediaItem | null;
  error: string;
  onSubmit: (mediaItemId: number, categoryIds: number[], tagIds: number[]) => Promise<void>;
};

export function MediaClassificationCard({
  categories,
  tags,
  mediaItem,
  error,
  onSubmit,
}: MediaClassificationCardProps) {
  if (!mediaItem) {
    return (
      <article className="card">
        <h2>Classify Media</h2>
        <p className="empty-state">Select a media item first.</p>
      </article>
    );
  }

  const sortedCategories = [...categories].sort((left, right) =>
    buildCategoryLabel(categories, left).localeCompare(buildCategoryLabel(categories, right)),
  );
  const sortedTags = [...tags].sort((left, right) => left.name.localeCompare(right.name));

  return (
    <article className="card">
      <h2>Classify Media</h2>
      <p className="muted">
        Assign categories and tags for <strong>{mediaItem.title}</strong>.
      </p>
      <form
        className="stack-form"
        action={async (formData) => {
          const categoryIds = formData
            .getAll("categories")
            .map((value) => Number(value))
            .filter((value) => !Number.isNaN(value));
          const tagIds = formData
            .getAll("tags")
            .map((value) => Number(value))
            .filter((value) => !Number.isNaN(value));

          await onSubmit(mediaItem.id, categoryIds, tagIds);
        }}
      >
        <div className="field">
          <span>Categories</span>
          {sortedCategories.length === 0 ? (
            <p className="empty-state">Create categories first.</p>
          ) : (
            <div className="checkbox-grid">
              {sortedCategories.map((category) => (
                <label key={category.id} className="checkbox-option">
                  <input
                    defaultChecked={mediaItem.categories.includes(category.id)}
                    name="categories"
                    type="checkbox"
                    value={category.id}
                  />
                  <span>{buildCategoryLabel(categories, category)}</span>
                </label>
              ))}
            </div>
          )}
        </div>

        <div className="field">
          <span>Tags</span>
          {sortedTags.length === 0 ? (
            <p className="empty-state">Create tags first.</p>
          ) : (
            <div className="checkbox-grid">
              {sortedTags.map((tag) => (
                <label key={tag.id} className="checkbox-option">
                  <input
                    defaultChecked={mediaItem.tags.includes(tag.id)}
                    name="tags"
                    type="checkbox"
                    value={tag.id}
                  />
                  <span>{tag.name}</span>
                </label>
              ))}
            </div>
          )}
        </div>

        {error ? <p className="error-text">{error}</p> : null}
        <SubmitButton>Save assignments</SubmitButton>
      </form>
    </article>
  );
}
