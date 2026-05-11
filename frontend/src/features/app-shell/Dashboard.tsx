import { Breadcrumbs } from "./Breadcrumbs";
import { CategoryManager } from "./CategoryManager";
import { CategoryTree } from "./CategoryTree";
import { MediaPlayerCard } from "./MediaPlayerCard";
import { MediaClassificationCard } from "./MediaClassificationCard";
import { RestrictedUserAccessCard } from "./RestrictedUserAccessCard";
import { SearchPanel } from "./SearchPanel";
import { TagManager } from "./TagManager";
import { UploadMediaForm } from "./UploadMediaForm";
import type {
  CategoryVisibilityAssignment,
  Category,
  MediaItem,
  MediaItemVisibilityAssignment,
  PlaybackProgress,
  RestrictedUser,
  SearchSuggestions,
  SessionState,
  Tag,
} from "./types";

type DashboardProps = {
  session: SessionState;
  categories: Category[];
  categoryAssignments: CategoryVisibilityAssignment[];
  tags: Tag[];
  mediaAssignments: MediaItemVisibilityAssignment[];
  ownerMediaItems: MediaItem[];
  mediaItems: MediaItem[];
  playbackEntries: PlaybackProgress[];
  createError: string;
  categoryError: string;
  tagError: string;
  classificationError: string;
  restrictedUserError: string;
  visibilityError: string;
  searchQuery: string;
  searchSuggestions: SearchSuggestions | null;
  selectedMediaItem: MediaItem | null;
  selectedCategoryId: number | null;
  selectedRestrictedUserId: number | null;
  selectedTagId: number | null;
  restrictedUsers: RestrictedUser[];
  onLogout: () => Promise<void>;
  onCreateCategory: (name: string, parentId: number | null) => Promise<void>;
  onCreateRestrictedUser: (username: string, password: string, email: string) => Promise<void>;
  onCreateTag: (name: string) => Promise<void>;
  onSelectMediaItem: (mediaItem: MediaItem) => void;
  onSelectCategory: (categoryId: number | null) => void;
  onSelectRestrictedUser: (userId: number | null) => void;
  onSelectTag: (tagId: number | null) => void;
  onChangeSearchQuery: (value: string) => void;
  onUploadMediaItem: (
    file: File,
    title: string,
    mediaType: string,
    description: string,
  ) => Promise<void>;
  onUpdateMediaItemAssignments: (
    mediaItemId: number,
    categoryIds: number[],
    tagIds: number[],
  ) => Promise<void>;
  onSaveVisibility: (
    userId: number,
    categoryIds: number[],
    mediaItemIds: number[],
  ) => Promise<void>;
  onPersistProgress: (mediaItemId: number, currentTime: number, duration: number) => Promise<void>;
};

function formatSeconds(s: number): string {
  const m = Math.floor(s / 60);
  const sec = s % 60;
  return `${m}:${sec.toString().padStart(2, "0")}`;
}

function formatProgressPercent(progressPercent: string): number {
  const parsedValue = Number.parseFloat(progressPercent);
  if (Number.isNaN(parsedValue)) {
    return 0;
  }

  return Math.max(0, Math.min(100, Math.round(parsedValue)));
}

function formatPlaybackStatus(status: string): string {
  switch (status) {
    case "completed":
      return "Completed";
    case "in_progress":
      return "In progress";
    default:
      return "Not started";
  }
}

function resolveMediaTypeBadge(mediaType: string): string {
  return mediaType === "video" ? "▶" : "♪";
}

export function Dashboard({
  session,
  categories,
  categoryAssignments,
  tags,
  mediaAssignments,
  ownerMediaItems,
  mediaItems,
  playbackEntries,
  createError,
  categoryError,
  tagError,
  classificationError,
  restrictedUserError,
  visibilityError,
  searchQuery,
  searchSuggestions,
  selectedMediaItem,
  selectedCategoryId,
  selectedRestrictedUserId,
  selectedTagId,
  restrictedUsers,
  onLogout,
  onCreateCategory,
  onCreateRestrictedUser,
  onCreateTag,
  onChangeSearchQuery,
  onSelectCategory,
  onSelectMediaItem,
  onSelectRestrictedUser,
  onSelectTag,
  onUploadMediaItem,
  onUpdateMediaItemAssignments,
  onSaveVisibility,
  onPersistProgress,
}: DashboardProps) {
  const selectedProgressEntry =
    playbackEntries.find((entry) => entry.media_item === selectedMediaItem?.id) ?? null;
  const mediaTitleById = new Map(ownerMediaItems.map((item) => [item.id, item.title]));
  const progressFor = (item: MediaItem) =>
    playbackEntries.find((entry) => entry.media_item === item.id) ?? null;

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
          selectedTagId={selectedTagId}
          suggestions={searchSuggestions}
          tags={tags}
        />

        <article className="card">
          <h2>Media Library</h2>
          <p className="muted">Current media items available in the selected context.</p>
          {mediaItems.length === 0 ? (
            <p className="empty-state">No media items yet.</p>
          ) : (
            <ul className="simple-list">
              {mediaItems.map((item) => {
                const playbackEntry = progressFor(item);
                const progressPercent = playbackEntry
                  ? formatProgressPercent(playbackEntry.progress_percent)
                  : 0;

                return (
                  <li
                    key={item.id}
                    className={selectedMediaItem?.id === item.id ? "selected-item" : undefined}
                  >
                    <button
                      className="list-button media-list-button"
                      onClick={() => onSelectMediaItem(item)}
                      type="button"
                    >
                      <div className="media-list-title-row">
                        <span aria-hidden="true" className="media-type-badge">
                          {resolveMediaTypeBadge(item.media_type)}
                        </span>
                        <strong>{item.title}</strong>
                      </div>
                      <span>
                        {item.media_type} · {item.player_display_mode}
                      </span>
                      {playbackEntry ? (
                        <div aria-hidden="true" className="progress-bar-track">
                          <div
                            className={`progress-bar-fill ${playbackEntry.status === "completed" ? "completed" : ""}`.trim()}
                            style={{ width: `${progressPercent}%` }}
                          />
                        </div>
                      ) : null}
                    </button>
                  </li>
                );
              })}
            </ul>
          )}
        </article>

        <MediaPlayerCard
          mediaItem={selectedMediaItem}
          onPersistProgress={onPersistProgress}
          progressEntry={selectedProgressEntry}
        />
      </section>

      <section className="grid">
        <article className="card">
          <h2>Playback Progress</h2>
          <p className="muted">Saved continue-watching positions for the current account.</p>
          {playbackEntries.length === 0 ? (
            <p className="empty-state">No playback entries yet.</p>
          ) : (
            <ul className="simple-list">
              {playbackEntries.map((entry) => (
                <li key={entry.id}>
                  <strong>{mediaTitleById.get(entry.media_item) ?? `Media #${entry.media_item}`}</strong>
                  <span>
                    {formatPlaybackStatus(entry.status)} · {formatSeconds(entry.position_seconds)} · {formatProgressPercent(entry.progress_percent)}%
                  </span>
                </li>
              ))}
            </ul>
          )}
        </article>
      </section>

      {session.role === "owner" ? (
        <>
          <hr className="section-divider" />
          <h2 className="section-heading">Library Management</h2>
          <section className="grid">
            <UploadMediaForm error={createError} onSubmit={onUploadMediaItem} />
            <CategoryManager
              categories={categories}
              error={categoryError}
              onSubmit={onCreateCategory}
            />
            <TagManager error={tagError} onSubmit={onCreateTag} />
            <MediaClassificationCard
              key={selectedMediaItem?.id ?? "none"}
              categories={categories}
              error={classificationError}
              mediaItem={selectedMediaItem}
              onSubmit={onUpdateMediaItemAssignments}
              tags={tags}
            />
          </section>

          <h2 className="section-heading">Access Control</h2>
          <section className="grid">
            <RestrictedUserAccessCard
              key={selectedRestrictedUserId ?? "none"}
              categories={categories}
              categoryAssignments={categoryAssignments}
              mediaAssignments={mediaAssignments}
              mediaItems={ownerMediaItems}
              onCreateRestrictedUser={onCreateRestrictedUser}
              onSaveVisibility={onSaveVisibility}
              onSelectRestrictedUser={onSelectRestrictedUser}
              restrictedUsers={restrictedUsers}
              selectedRestrictedUserId={selectedRestrictedUserId}
              userError={restrictedUserError}
              visibilityError={visibilityError}
            />
          </section>
        </>
      ) : null}
    </>
  );
}
