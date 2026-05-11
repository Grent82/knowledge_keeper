import { useEffect, useState } from "react";

import {
  createMediaItemFromAsset,
  createPlaybackProgress,
  createMediaItem,
  fetchMediaItems,
  fetchPlaybackProgress,
  fetchSession,
  login,
  logout,
  updatePlaybackProgress,
  uploadMediaAsset,
} from "./api";
import { Dashboard } from "./Dashboard";
import { LoginForm } from "./LoginForm";
import type { MediaItem, PlaybackProgress, SessionState } from "./types";

const anonymousSession: SessionState = {
  is_authenticated: false,
  username: "",
  role: "",
};

export function AppScreen() {
  const [session, setSession] = useState<SessionState>(anonymousSession);
  const [mediaItems, setMediaItems] = useState<MediaItem[]>([]);
  const [playbackEntries, setPlaybackEntries] = useState<PlaybackProgress[]>([]);
  const [selectedMediaItem, setSelectedMediaItem] = useState<MediaItem | null>(null);
  const [loginError, setLoginError] = useState("");
  const [createError, setCreateError] = useState("");

  useEffect(() => {
    void refreshSession();
  }, []);

  async function refreshSession() {
    const nextSession = await fetchSession();
    setSession(nextSession);

    if (nextSession.is_authenticated) {
      await refreshData();
    }
  }

  async function refreshData() {
    const [items, progress] = await Promise.all([fetchMediaItems(), fetchPlaybackProgress()]);
    setMediaItems(items);
    setPlaybackEntries(progress);
    setSelectedMediaItem((currentSelected) => {
      if (!currentSelected) {
        return items[0] ?? null;
      }
      return items.find((item) => item.id === currentSelected.id) ?? items[0] ?? null;
    });
  }

  async function handleLogin(username: string, password: string) {
    try {
      setLoginError("");
      const nextSession = await login(username, password);
      setSession(nextSession);
      await refreshData();
    } catch (error) {
      setLoginError(error instanceof Error ? error.message : "Login failed.");
    }
  }

  async function handleLogout() {
    await logout();
    setSession(anonymousSession);
    setMediaItems([]);
    setPlaybackEntries([]);
    setSelectedMediaItem(null);
  }

  async function handleCreateMediaItem(title: string, mediaType: string, description: string) {
    try {
      setCreateError("");
      const item = await createMediaItem(title, mediaType, description);
      await refreshData();
      setSelectedMediaItem(item);
    } catch (error) {
      setCreateError(error instanceof Error ? error.message : "Media creation failed.");
    }
  }

  async function handleUploadMediaItem(
    file: File,
    title: string,
    mediaType: string,
    description: string,
  ) {
    try {
      setCreateError("");
      const asset = await uploadMediaAsset(file);
      const item = await createMediaItemFromAsset(title, mediaType, description, asset.id);
      await refreshData();
      setSelectedMediaItem(item);
    } catch (error) {
      setCreateError(error instanceof Error ? error.message : "Upload failed.");
    }
  }

  async function handlePersistProgress(mediaItemId: number, currentTime: number, duration: number) {
    const progressPercent = duration > 0 ? (currentTime / duration) * 100 : 0;
    const existingEntry = playbackEntries.find((entry) => entry.media_item === mediaItemId);
    const nextEntry = existingEntry
      ? await updatePlaybackProgress(existingEntry.id, mediaItemId, currentTime, progressPercent)
      : await createPlaybackProgress(mediaItemId, currentTime, progressPercent);

    setPlaybackEntries((currentEntries) => {
      const withoutCurrent = currentEntries.filter((entry) => entry.media_item !== mediaItemId);
      return [...withoutCurrent, nextEntry].sort((left, right) => left.media_item - right.media_item);
    });
  }

  if (!session.is_authenticated) {
    return (
      <>
        <section className="hero">
          <p className="eyebrow">Knowledge Keeper</p>
          <h1>Private media and knowledge platform</h1>
          <p className="intro">
            Sign in to browse media, resume playback and manage your personal knowledge library.
          </p>
        </section>
        <LoginForm error={loginError} onSubmit={handleLogin} />
      </>
    );
  }

  return (
    <Dashboard
      createError={createError}
      mediaItems={mediaItems}
      onCreateMediaItem={handleCreateMediaItem}
      onLogout={handleLogout}
      onPersistProgress={handlePersistProgress}
      onSelectMediaItem={setSelectedMediaItem}
      onUploadMediaItem={handleUploadMediaItem}
      playbackEntries={playbackEntries}
      selectedMediaItem={selectedMediaItem}
      session={session}
    />
  );
}
