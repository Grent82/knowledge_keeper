import { MediaPlayerCard } from "./MediaPlayerCard";
import { UploadMediaForm } from "./UploadMediaForm";
import type { MediaItem, PlaybackProgress, SessionState } from "./types";

type DashboardProps = {
  session: SessionState;
  mediaItems: MediaItem[];
  playbackEntries: PlaybackProgress[];
  createError: string;
  selectedMediaItem: MediaItem | null;
  onLogout: () => Promise<void>;
  onCreateMediaItem: (title: string, mediaType: string, description: string) => Promise<void>;
  onSelectMediaItem: (mediaItem: MediaItem) => void;
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
  mediaItems,
  playbackEntries,
  createError,
  selectedMediaItem,
  onLogout,
  onCreateMediaItem,
  onSelectMediaItem,
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

      <section className="grid">
        <article className="card">
          <h2>Media Library</h2>
          <p className="muted">Current media items available to this account.</p>
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
