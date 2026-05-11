import { useEffect, useState } from "react";

import {
  createMediaItemFromAsset,
  createPlaybackProgress,
  createMediaItem,
  fetchCategories,
  fetchMediaItems,
  fetchPlaybackProgress,
  fetchSearchSuggestions,
  fetchSession,
  login,
  logout,
  updatePlaybackProgress,
  uploadMediaAsset,
} from "./api";
import { Dashboard } from "./Dashboard";
import { LoginForm } from "./LoginForm";
import type {
  Category,
  MediaItem,
  PlaybackProgress,
  SearchSuggestions,
  SessionState,
} from "./types";

const anonymousSession: SessionState = {
  is_authenticated: false,
  username: "",
  role: "",
};

function collectVisibleCategoryIds(
  categories: Category[],
  selectedCategoryId: number | null,
): Set<number> | null {
  if (selectedCategoryId === null) {
    return null;
  }

  const childrenByParent = new Map<number, number[]>();

  for (const category of categories) {
    if (category.parent === null) {
      continue;
    }

    const currentChildren = childrenByParent.get(category.parent) ?? [];
    currentChildren.push(category.id);
    childrenByParent.set(category.parent, currentChildren);
  }

  const collectedIds = new Set<number>();
  const pendingIds = [selectedCategoryId];

  while (pendingIds.length > 0) {
    const nextId = pendingIds.pop();
    if (nextId === undefined || collectedIds.has(nextId)) {
      continue;
    }

    collectedIds.add(nextId);

    for (const childId of childrenByParent.get(nextId) ?? []) {
      pendingIds.push(childId);
    }
  }

  return collectedIds;
}

export function AppScreen() {
  const [session, setSession] = useState<SessionState>(anonymousSession);
  const [categories, setCategories] = useState<Category[]>([]);
  const [mediaItems, setMediaItems] = useState<MediaItem[]>([]);
  const [playbackEntries, setPlaybackEntries] = useState<PlaybackProgress[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchSuggestions, setSearchSuggestions] = useState<SearchSuggestions | null>(null);
  const [selectedCategoryId, setSelectedCategoryId] = useState<number | null>(null);
  const [selectedTagId, setSelectedTagId] = useState<number | null>(null);
  const [selectedMediaItem, setSelectedMediaItem] = useState<MediaItem | null>(null);
  const [loginError, setLoginError] = useState("");
  const [createError, setCreateError] = useState("");

  useEffect(() => {
    void refreshSession();
  }, []);

  useEffect(() => {
    if (!session.is_authenticated) {
      return;
    }

    if (!searchQuery.trim()) {
      setSearchSuggestions(null);
      return;
    }

    const timeoutId = window.setTimeout(() => {
      void fetchSearchSuggestions(searchQuery).then(setSearchSuggestions);
    }, 180);

    return () => window.clearTimeout(timeoutId);
  }, [searchQuery, session.is_authenticated]);

  async function refreshSession() {
    const nextSession = await fetchSession();
    setSession(nextSession);

    if (nextSession.is_authenticated) {
      await refreshData();
    }
  }

  async function refreshData() {
    const [items, progress, nextCategories] = await Promise.all([
      fetchMediaItems(),
      fetchPlaybackProgress(),
      fetchCategories(),
    ]);
    setMediaItems(items);
    setPlaybackEntries(progress);
    setCategories(nextCategories);
    setSelectedMediaItem((currentSelected) => {
      if (!currentSelected) {
        return items[0] ?? null;
      }
      return items.find((item) => item.id === currentSelected.id) ?? items[0] ?? null;
    });
  }

  const visibleCategoryIds = collectVisibleCategoryIds(categories, selectedCategoryId);
  const visibleMediaItems = mediaItems.filter((item) => {
    const categoryMatch =
      visibleCategoryIds === null ||
      item.categories.some((categoryId) => visibleCategoryIds.has(categoryId));
    const tagMatch = selectedTagId === null || item.tags.includes(selectedTagId);
    return categoryMatch && tagMatch;
  });

  useEffect(() => {
    if (visibleMediaItems.length === 0) {
      setSelectedMediaItem(null);
      return;
    }

    if (!selectedMediaItem) {
      setSelectedMediaItem(visibleMediaItems[0] ?? null);
      return;
    }

    if (!visibleMediaItems.some((item) => item.id === selectedMediaItem.id)) {
      setSelectedMediaItem(visibleMediaItems[0] ?? null);
    }
  }, [selectedMediaItem, visibleMediaItems]);

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
    setCategories([]);
    setSearchQuery("");
    setSearchSuggestions(null);
    setSelectedCategoryId(null);
    setSelectedTagId(null);
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
      categories={categories}
      mediaItems={visibleMediaItems}
      onCreateMediaItem={handleCreateMediaItem}
      onChangeSearchQuery={setSearchQuery}
      onLogout={handleLogout}
      onPersistProgress={handlePersistProgress}
      onSelectCategory={(categoryId) => {
        setSelectedCategoryId(categoryId);
      }}
      onSelectMediaItem={setSelectedMediaItem}
      onSelectTag={setSelectedTagId}
      onUploadMediaItem={handleUploadMediaItem}
      playbackEntries={playbackEntries}
      searchQuery={searchQuery}
      searchSuggestions={searchSuggestions}
      selectedCategoryId={selectedCategoryId}
      selectedMediaItem={selectedMediaItem}
      session={session}
    />
  );
}
