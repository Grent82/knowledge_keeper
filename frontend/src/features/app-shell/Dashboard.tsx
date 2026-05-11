import { Breadcrumbs } from "./Breadcrumbs";
import { CategoryTree } from "./CategoryTree";
import { MediaPlayerCard } from "./MediaPlayerCard";
import { SearchPanel } from "./SearchPanel";
import { UploadMediaForm } from "./UploadMediaForm";
import type {
  Category,
  MediaItem,
  PlaybackProgress,
  SearchSuggestions,
  SessionState,
} from "./types";

type DashboardProps = {
  session: SessionState;
  categories: Category[];
  mediaItems: MediaItem[];
  playbackEntries: PlaybackProgress[];
  createError: string;
  searchQuery: string;
  searchSuggestions: SearchSuggestions | null;
  selectedMediaItem: MediaItem | null;
  selectedCategoryId: number | null;
  onLogout: () => Promise<void>;
  onCreateMediaItem: (title: string, mediaType: string, description: string) => Promise<void>;
  onSelectMediaItem: (mediaItem: MediaItem) => void;
  onSelectCategory: (categoryId: number | null) => void;
  onSelectTag: (tagId: number) => void;
  onChangeSearchQuery: (value: string) => void;
  onUploadMediaItem: (
    file: File,
    title: string,
    mediaType: string,
    description: string,
  ) => Promise<void>;
  onPersistProgress: (mediaItemId: number, currentTime: number, duration: number) => Promise<void>;
};

export function Dashboard({
  session,
  categories,
  mediaItems,
  playbackEntries,
  createError,
  searchQuery,
  searchSuggestions,
  selectedMediaItem,
  selectedCategoryId,
  onLogout,
  onCreateMediaItem,
  onChangeSearchQuery,
  onSelectCategory,
  onSelectMediaItem,
  onSelectTag,
  onUploadMediaItem,
  onPersistProgress,
}: DashboardProps) {
  const selectedProgressEntry =
    playbackEntries.find((entry) => entry.media_item === selectedMediaItem?.id) ?? null;

  return (
    <>
      <section className="hero">
        <p className="eyebrow">Knowledge Keeper</p>
        <h1>Private media and knowledge platform</h1>
        <p className="intro">
          Logged in as <strong>{session.username}</strong> with role <strong>{session.role}</strong>.
        </p>
        <div className="hero-actions">
          <button className="secondary-button" onClick={() => void onLogout()} type="button">
            Logout
          </button>
        </div>
      </section>

      <Breadcrumbs
        categories={categories}
        onSelectCategory={onSelectCategory}
        selectedCategoryId={selectedCategoryId}
      />

      <section className="grid">
        <CategoryTree
          categories={categories}
          onSelectCategory={onSelectCategory}
          selectedCategoryId={selectedCategoryId}
        />

        <SearchPanel
          onChangeQuery={onChangeSearchQuery}
          onSelectCategory={(categoryId) => {
            onSelectCategory(categoryId);
          }}
          onSelectMediaItem={onSelectMediaItem}
          onSelectTag={onSelectTag}
          query={searchQuery}
          suggestions={searchSuggestions}
        />

        <article className="card">
          <h2>Media Library</h2>
          <p className="muted">Current media items available in the selected context.</p>
          {mediaItems.length === 0 ? (
            <p className="empty-state">No media items yet.</p>
          ) : (
            <ul className="simple-list">
              {mediaItems.map((item) => (
                <li key={item.id}>
                  <button
                    className="list-button"
                    onClick={() => onSelectMediaItem(item)}
                    type="button"
                  >
                    <strong>{item.title}</strong>
                  </button>
                  <span>
                    {item.media_type} · {item.player_display_mode}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </article>

        <article className="card">
          <h2>Playback Progress</h2>
          <p className="muted">Saved continue-watching positions for the current account.</p>
          {playbackEntries.length === 0 ? (
            <p className="empty-state">No playback entries yet.</p>
          ) : (
            <ul className="simple-list">
              {playbackEntries.map((entry) => (
                <li key={entry.id}>
                  <strong>Media #{entry.media_item}</strong>
                  <span>
                    {entry.status} · {entry.position_seconds}s · {entry.progress_percent}%
                  </span>
                </li>
              ))}
            </ul>
          )}
        </article>

        <MediaPlayerCard
          mediaItem={selectedMediaItem}
          onPersistProgress={onPersistProgress}
          progressEntry={selectedProgressEntry}
        />

        {session.role === "owner" ? (
          <>
            <UploadMediaForm error={createError} onSubmit={onUploadMediaItem} />
            <article className="card">
              <h2>Create Basic Media Item</h2>
              <p className="muted">Fallback owner-only entry without file upload.</p>
              <form
                className="stack-form"
                action={async (formData) => {
                  const title = String(formData.get("title") ?? "");
                  const mediaType = String(formData.get("mediaType") ?? "audio");
                  const description = String(formData.get("description") ?? "");
                  await onCreateMediaItem(title, mediaType, description);
                }}
              >
                <label className="field">
                  <span>Title</span>
                  <input name="title" required type="text" />
                </label>
                <label className="field">
                  <span>Type</span>
                  <select defaultValue="audio" name="mediaType">
                    <option value="audio">Audio</option>
                    <option value="video">Video</option>
                  </select>
                </label>
                <label className="field">
                  <span>Description</span>
                  <textarea name="description" rows={3} />
                </label>
                {createError ? <p className="error-text">{createError}</p> : null}
                <button type="submit">Create media item</button>
              </form>
            </article>
          </>
        ) : null}
      </section>
    </>
  );
}
