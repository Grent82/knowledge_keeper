import { useEffect, useState } from "react";

import {
  createMediaItem,
  fetchMediaItems,
  fetchPlaybackProgress,
  fetchSession,
  login,
  logout,
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
  }

  async function handleCreateMediaItem(title: string, mediaType: string, description: string) {
    try {
      setCreateError("");
      await createMediaItem(title, mediaType, description);
      await refreshData();
    } catch (error) {
      setCreateError(error instanceof Error ? error.message : "Media creation failed.");
    }
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
      playbackEntries={playbackEntries}
      session={session}
    />
  );
}
