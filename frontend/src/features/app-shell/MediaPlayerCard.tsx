import type { SyntheticEvent } from "react";
import { useEffect, useMemo, useRef, useState } from "react";

import type { MediaItem, PlaybackProgress } from "./types";

type MediaPlayerCardProps = {
  mediaItem: MediaItem | null;
  progressEntry: PlaybackProgress | null;
  onDeleteMediaItem?: (id: number) => Promise<void>;
  onPersistProgress: (mediaItemId: number, currentTime: number, duration: number) => Promise<void>;
  onUpdateMediaItem?: (
    id: number,
    data: { title: string; description: string; media_type: string },
  ) => Promise<void>;
};

export function MediaPlayerCard({
  mediaItem,
  progressEntry,
  onDeleteMediaItem,
  onPersistProgress,
  onUpdateMediaItem,
}: MediaPlayerCardProps) {
  const mediaRef = useRef<HTMLMediaElement | null>(null);
  const lastSavedSecondRef = useRef<number>(-1);
  const [isEditing, setIsEditing] = useState(false);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [mediaType, setMediaType] = useState("audio");

  const assetUrl = mediaItem?.asset_detail?.asset_url ?? "";
  const externalSource = mediaItem?.external_source_detail ?? null;
  const externalPlayableUrl =
    externalSource && ["direct_link", "podcast"].includes(externalSource.provider)
      ? externalSource.source_url
      : "";
  const isYouTubeEmbed = externalSource?.provider === "youtube" && Boolean(externalSource.external_id);
  const playbackLabel = useMemo(() => {
    if (!progressEntry) {
      return "No saved playback position yet.";
    }
    return `${progressEntry.status} · ${progressEntry.position_seconds}s · ${progressEntry.progress_percent}%`;
  }, [progressEntry]);

  useEffect(() => {
    const mediaElement = mediaRef.current;
    if (!mediaElement || !progressEntry) {
      return;
    }

    mediaElement.currentTime = progressEntry.position_seconds;
    lastSavedSecondRef.current = progressEntry.position_seconds;
  }, [mediaItem?.id, progressEntry]);

  useEffect(() => {
    if (!mediaItem) {
      return;
    }

    setIsEditing(false);
    setTitle(mediaItem.title);
    setDescription(mediaItem.description);
    setMediaType(mediaItem.media_type);
  }, [mediaItem]);

  if (!mediaItem) {
    return (
      <article className="card detail-card player-card">
        <h2>Media Detail</h2>
        <p className="empty-state">Select a media item to inspect and play it.</p>
      </article>
    );
  }

  const commonProps = {
    controls: true,
    src: assetUrl || externalPlayableUrl,
    onTimeUpdate: async (event: SyntheticEvent<HTMLMediaElement>) => {
      const element = event.currentTarget;
      const currentSecond = Math.floor(element.currentTime);
      if (!element.duration || currentSecond === lastSavedSecondRef.current) {
        return;
      }

      if (currentSecond === 0 || currentSecond - lastSavedSecondRef.current >= 5) {
        lastSavedSecondRef.current = currentSecond;
        await onPersistProgress(mediaItem.id, element.currentTime, element.duration);
      }
    },
    onPause: async (event: SyntheticEvent<HTMLMediaElement>) => {
      const element = event.currentTarget;
      if (element.duration) {
        await onPersistProgress(mediaItem.id, element.currentTime, element.duration);
      }
    },
    onEnded: async (event: SyntheticEvent<HTMLMediaElement>) => {
      const element = event.currentTarget;
      if (element.duration) {
        await onPersistProgress(mediaItem.id, element.duration, element.duration);
      }
    },
  };

  return (
    <article className="card detail-card player-card">
      <h2>{mediaItem.title}</h2>
      <p className="muted">{mediaItem.description || "No description provided."}</p>
      <p className="muted">
        {mediaItem.media_type} · {mediaItem.player_display_mode}
      </p>
      {onUpdateMediaItem && onDeleteMediaItem ? (
        <div className="inline-actions media-item-actions">
          <button
            className="secondary-button"
            onClick={() => {
              setIsEditing((currentValue) => !currentValue);
              setTitle(mediaItem.title);
              setDescription(mediaItem.description);
              setMediaType(mediaItem.media_type);
            }}
            type="button"
          >
            {isEditing ? "Close" : "Edit"}
          </button>
          <button
            className="secondary-button"
            onClick={() => {
              if (window.confirm("Delete this media item?")) {
                void onDeleteMediaItem(mediaItem.id);
              }
            }}
            type="button"
          >
            Delete
          </button>
        </div>
      ) : null}
      {isEditing && onUpdateMediaItem ? (
        <form
          className="stack-form media-item-edit-form"
          onSubmit={(event) => {
            event.preventDefault();
            void onUpdateMediaItem(mediaItem.id, {
              title: title.trim(),
              description: description.trim(),
              media_type: mediaType,
            }).then(() => setIsEditing(false));
          }}
        >
          <label className="field">
            <span>Title</span>
            <input onChange={(event) => setTitle(event.target.value)} type="text" value={title} />
          </label>
          <label className="field">
            <span>Description</span>
            <textarea
              onChange={(event) => setDescription(event.target.value)}
              rows={3}
              value={description}
            />
          </label>
          <label className="field">
            <span>Type</span>
            <select onChange={(event) => setMediaType(event.target.value)} value={mediaType}>
              <option value="audio">Audio</option>
              <option value="video">Video</option>
            </select>
          </label>
          <div className="inline-actions">
            <button type="submit">Save</button>
            <button
              className="secondary-button"
              onClick={() => {
                setIsEditing(false);
                setTitle(mediaItem.title);
                setDescription(mediaItem.description);
                setMediaType(mediaItem.media_type);
              }}
              type="button"
            >
              Cancel
            </button>
          </div>
        </form>
      ) : null}
      <p className="muted">{playbackLabel}</p>
      {assetUrl || externalPlayableUrl ? (
        mediaItem.media_type === "video" ? (
          <video
            className="media-player"
            ref={(node) => {
              mediaRef.current = node;
            }}
            {...commonProps}
          />
        ) : (
          <audio
            className="media-player"
            ref={(node) => {
              mediaRef.current = node;
            }}
            {...commonProps}
          />
        )
      ) : isYouTubeEmbed ? (
        <iframe
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
          allowFullScreen
          className="media-embed"
          src={`https://www.youtube.com/embed/${externalSource?.external_id}`}
          title={mediaItem.title}
        />
      ) : externalSource?.provider === "other" ? (
        <p className="muted">
          External source available: <a href={externalSource.source_url}>{externalSource.source_url}</a>
        </p>
      ) : (
        <p className="empty-state">No playable file attached yet.</p>
      )}
    </article>
  );
}
