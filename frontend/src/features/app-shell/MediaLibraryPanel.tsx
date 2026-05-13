import type { MediaItem, PlaybackProgress } from "./types";

type MediaLibraryPanelProps = {
  filterMediaType: "all" | "audio" | "video";
  filterStatus: "all" | "not_started" | "in_progress" | "completed";
  sortBy: "title" | "date" | "progress";
  sortDir: "asc" | "desc";
  filteredItems: MediaItem[];
  selectedMediaItem: MediaItem | null;
  progressFor: (item: MediaItem) => PlaybackProgress | null;
  onChangeFilterMediaType: (value: "all" | "audio" | "video") => void;
  onChangeFilterStatus: (value: "all" | "not_started" | "in_progress" | "completed") => void;
  onChangeSortBy: (value: "title" | "date" | "progress") => void;
  onToggleSortDir: () => void;
  onSelectMediaItem: (mediaItem: MediaItem) => void;
};

function formatProgressPercent(progressPercent: string): number {
  const parsedValue = Number.parseFloat(progressPercent);
  if (Number.isNaN(parsedValue)) {
    return 0;
  }

  return Math.max(0, Math.min(100, Math.round(parsedValue)));
}

function resolveMediaTypeBadge(mediaType: string): string {
  return mediaType === "video" ? "▶" : "♪";
}

export function MediaLibraryPanel({
  filterMediaType,
  filterStatus,
  sortBy,
  sortDir,
  filteredItems,
  selectedMediaItem,
  progressFor,
  onChangeFilterMediaType,
  onChangeFilterStatus,
  onChangeSortBy,
  onToggleSortDir,
  onSelectMediaItem,
}: MediaLibraryPanelProps) {
  return (
    <article className="card media-library-panel">
      <h2>Media Library</h2>
      <p className="muted">Current media items available in the selected context.</p>
      <div className="library-filters">
        <select
          aria-label="Filter media type"
          onChange={(event) => onChangeFilterMediaType(event.target.value as "all" | "audio" | "video")}
          value={filterMediaType}
        >
          <option value="all">All types</option>
          <option value="audio">Audio</option>
          <option value="video">Video</option>
        </select>
        <select
          aria-label="Filter playback status"
          onChange={(event) =>
            onChangeFilterStatus(
              event.target.value as "all" | "not_started" | "in_progress" | "completed",
            )
          }
          value={filterStatus}
        >
          <option value="all">All status</option>
          <option value="not_started">Not started</option>
          <option value="in_progress">In progress</option>
          <option value="completed">Completed</option>
        </select>
        <select
          aria-label="Sort media library"
          onChange={(event) => onChangeSortBy(event.target.value as "title" | "date" | "progress")}
          value={sortBy}
        >
          <option value="title">Sort: Title</option>
          <option value="date">Sort: Date</option>
          <option value="progress">Sort: Progress</option>
        </select>
        <button
          aria-label={`Sort direction ${sortDir === "asc" ? "ascending" : "descending"}`}
          className="secondary-button sort-dir-button"
          onClick={onToggleSortDir}
          type="button"
        >
          {sortDir === "asc" ? "↑" : "↓"}
        </button>
      </div>
      {filteredItems.length === 0 ? (
        <p className="empty-state">No media items yet.</p>
      ) : (
        <ul className="simple-list">
          {filteredItems.map((item) => {
            const playbackEntry = progressFor(item);
            const progressPercent = playbackEntry
              ? formatProgressPercent(playbackEntry.progress_percent)
              : 0;

            return (
              <li key={item.id} className={selectedMediaItem?.id === item.id ? "selected-item" : undefined}>
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
  );
}
