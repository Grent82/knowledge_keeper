import type { Category, MediaItem, SearchSuggestions, Tag } from "./types";

type SearchPanelProps = {
  tags: Tag[];
  query: string;
  suggestions: SearchSuggestions | null;
  selectedTagId: number | null;
  onChangeQuery: (value: string) => void;
  onSelectMediaItem: (mediaItem: MediaItem) => void;
  onSelectCategory: (categoryId: number) => void;
  onSelectTag: (tagId: number | null) => void;
};

function SuggestionGroup({
  title,
  emptyLabel,
  children,
}: {
  title: string;
  emptyLabel: string;
  children: React.ReactNode;
}) {
  return (
    <div className="suggestion-group">
      <h3>{title}</h3>
      {children || <p className="empty-state">{emptyLabel}</p>}
    </div>
  );
}

export function SearchPanel({
  tags,
  query,
  suggestions,
  selectedTagId,
  onChangeQuery,
  onSelectMediaItem,
  onSelectCategory,
  onSelectTag,
}: SearchPanelProps) {
  const categories = suggestions?.categories ?? [];
  const suggestionTags = suggestions?.tags ?? [];
  const mediaItems = suggestions?.media_items ?? [];
  const selectedTag = tags.find((tag) => tag.id === selectedTagId) ?? null;

  return (
    <article className="card search-card">
      <h2>Search</h2>
      <p className="muted">Start typing to get matching categories, tags and media items.</p>
      <input
        aria-label="Search media library"
        className="search-input"
        onChange={(event) => onChangeQuery(event.target.value)}
        placeholder="Search categories, tags, media..."
        type="search"
        value={query}
      />
      {selectedTag ? (
        <div className="inline-actions">
          <p className="muted">Tag filter: {selectedTag.name}</p>
          <button className="secondary-button" onClick={() => onSelectTag(null)} type="button">
            Clear tag filter
          </button>
        </div>
      ) : null}

      {query ? (
        <div className="suggestion-layout">
          <SuggestionGroup emptyLabel="No category matches." title="Categories">
            {categories.length > 0 ? (
              <ul className="simple-list compact-list">
                {categories.map((category: Category) => (
                  <li key={category.id}>
                    <button
                      className="list-button"
                      onClick={() => onSelectCategory(category.id)}
                      type="button"
                    >
                      {category.name}
                    </button>
                  </li>
                ))}
              </ul>
            ) : null}
          </SuggestionGroup>

          <SuggestionGroup emptyLabel="No tag matches." title="Tags">
            {suggestionTags.length > 0 ? (
              <ul className="simple-list compact-list">
                {suggestionTags.map((tag: Tag) => (
                  <li key={tag.id}>
                    <button className="list-button" onClick={() => onSelectTag(tag.id)} type="button">
                      {tag.name}
                    </button>
                  </li>
                ))}
              </ul>
            ) : null}
          </SuggestionGroup>

          <SuggestionGroup emptyLabel="No media matches." title="Media">
            {mediaItems.length > 0 ? (
              <ul className="simple-list compact-list">
                {mediaItems.map((item: MediaItem) => (
                  <li key={item.id}>
                    <button className="list-button" onClick={() => onSelectMediaItem(item)} type="button">
                      {item.title}
                    </button>
                  </li>
                ))}
              </ul>
            ) : null}
          </SuggestionGroup>
        </div>
      ) : null}
    </article>
  );
}
