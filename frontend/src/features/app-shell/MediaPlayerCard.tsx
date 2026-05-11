import type { SyntheticEvent } from "react";
import { useEffect, useMemo, useRef } from "react";

import type { MediaItem, PlaybackProgress } from "./types";

type MediaPlayerCardProps = {
  mediaItem: MediaItem | null;
  progressEntry: PlaybackProgress | null;
  onPersistProgress: (mediaItemId: number, currentTime: number, duration: number) => Promise<void>;
};

export function MediaPlayerCard({
  mediaItem,
  progressEntry,
  onPersistProgress,
}: MediaPlayerCardProps) {
  const mediaRef = useRef<HTMLMediaElement | null>(null);
  const lastSavedSecondRef = useRef<number>(-1);

  const assetUrl = mediaItem?.asset_detail?.asset_url ?? "";
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

  if (!mediaItem) {
    return (
      <article className="card detail-card">
        <h2>Media Detail</h2>
        <p className="empty-state">Select a media item to inspect and play it.</p>
      </article>
    );
  }

  const commonProps = {
    controls: true,
    src: assetUrl,
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
    <article className="card detail-card">
      <h2>{mediaItem.title}</h2>
      <p className="muted">{mediaItem.description || "No description provided."}</p>
      <p className="muted">
        {mediaItem.media_type} · {mediaItem.player_display_mode}
      </p>
      <p className="muted">{playbackLabel}</p>
      {assetUrl ? (
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
      ) : (
        <p className="empty-state">No playable file attached yet.</p>
      )}
    </article>
  );
}
