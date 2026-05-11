import { useEffect, useState } from "react";

import {
  createCategoryVisibilityAssignment,
  createCategory,
  createMediaItemFromAsset,
  createMediaVisibilityAssignment,
  createPlaybackProgress,
  createMediaItem,
  createRestrictedUser,
  createTag,
  deleteCategoryVisibilityAssignment,
  deleteMediaVisibilityAssignment,
  fetchCategoryVisibilityAssignments,
  fetchCategories,
  fetchMediaVisibilityAssignments,
  fetchMediaItems,
  fetchPlaybackProgress,
  fetchRestrictedUsers,
  fetchSearchSuggestions,
  fetchSession,
  fetchTags,
  login,
  logout,
  updateMediaItemAssignments,
  updatePlaybackProgress,
  uploadMediaAsset,
} from "./api";
import { Dashboard } from "./Dashboard";
import { LoginForm } from "./LoginForm";
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
  const [tags, setTags] = useState<Tag[]>([]);
  const [mediaItems, setMediaItems] = useState<MediaItem[]>([]);
  const [restrictedUsers, setRestrictedUsers] = useState<RestrictedUser[]>([]);
  const [categoryAssignments, setCategoryAssignments] = useState<CategoryVisibilityAssignment[]>([]);
  const [mediaAssignments, setMediaAssignments] = useState<MediaItemVisibilityAssignment[]>([]);
  const [playbackEntries, setPlaybackEntries] = useState<PlaybackProgress[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchSuggestions, setSearchSuggestions] = useState<SearchSuggestions | null>(null);
  const [selectedCategoryId, setSelectedCategoryId] = useState<number | null>(null);
  const [selectedTagId, setSelectedTagId] = useState<number | null>(null);
  const [selectedRestrictedUserId, setSelectedRestrictedUserId] = useState<number | null>(null);
  const [selectedMediaItem, setSelectedMediaItem] = useState<MediaItem | null>(null);
  const [loginError, setLoginError] = useState("");
  const [createError, setCreateError] = useState("");
  const [categoryError, setCategoryError] = useState("");
  const [tagError, setTagError] = useState("");
  const [classificationError, setClassificationError] = useState("");
  const [restrictedUserError, setRestrictedUserError] = useState("");
  const [visibilityError, setVisibilityError] = useState("");

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

  useEffect(() => {
    if (session.role !== "owner") {
      setSelectedRestrictedUserId(null);
      return;
    }

    if (restrictedUsers.length === 0) {
      setSelectedRestrictedUserId(null);
      return;
    }

    setSelectedRestrictedUserId((currentSelected) => {
      if (currentSelected && restrictedUsers.some((user) => user.id === currentSelected)) {
        return currentSelected;
      }
      return restrictedUsers[0]?.id ?? null;
    });
  }, [restrictedUsers, session.role]);

  async function refreshSession() {
    const nextSession = await fetchSession();
    setSession(nextSession);

    if (nextSession.is_authenticated) {
      await refreshData(nextSession);
    }
  }

  async function refreshData(currentSession: SessionState = session) {
    const [items, progress, nextCategories, nextTags] = await Promise.all([
      fetchMediaItems(),
      fetchPlaybackProgress(),
      fetchCategories(),
      fetchTags(),
    ]);
    setMediaItems(items);
    setPlaybackEntries(progress);
    setCategories(nextCategories);
    setTags(nextTags);
    setSelectedMediaItem((currentSelected) => {
      if (!currentSelected) {
        return items[0] ?? null;
      }
      return items.find((item) => item.id === currentSelected.id) ?? items[0] ?? null;
    });

    if (currentSession.role === "owner") {
      const [nextRestrictedUsers, nextCategoryAssignments, nextMediaAssignments] = await Promise.all([
        fetchRestrictedUsers(),
        fetchCategoryVisibilityAssignments(),
        fetchMediaVisibilityAssignments(),
      ]);
      setRestrictedUsers(nextRestrictedUsers);
      setCategoryAssignments(nextCategoryAssignments);
      setMediaAssignments(nextMediaAssignments);
      return;
    }

    setRestrictedUsers([]);
    setCategoryAssignments([]);
    setMediaAssignments([]);
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
      await refreshData(nextSession);
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
    setTags([]);
    setRestrictedUsers([]);
    setCategoryAssignments([]);
    setMediaAssignments([]);
    setSearchQuery("");
    setSearchSuggestions(null);
    setSelectedCategoryId(null);
    setSelectedTagId(null);
    setSelectedRestrictedUserId(null);
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

  async function handleCreateCategory(name: string, parentId: number | null) {
    try {
      setCategoryError("");
      await createCategory(name, parentId);
      await refreshData();
    } catch (error) {
      setCategoryError(error instanceof Error ? error.message : "Category creation failed.");
    }
  }

  async function handleCreateTag(name: string) {
    try {
      setTagError("");
      await createTag(name);
      await refreshData();
    } catch (error) {
      setTagError(error instanceof Error ? error.message : "Tag creation failed.");
    }
  }

  async function handleUpdateMediaItemAssignments(
    mediaItemId: number,
    categoryIds: number[],
    tagIds: number[],
  ) {
    try {
      setClassificationError("");
      const updatedMediaItem = await updateMediaItemAssignments(mediaItemId, categoryIds, tagIds);
      await refreshData();
      setSelectedMediaItem(updatedMediaItem);
    } catch (error) {
      setClassificationError(
        error instanceof Error ? error.message : "Media classification update failed.",
      );
    }
  }

  async function handleCreateRestrictedUser(username: string, password: string, email: string) {
    try {
      setRestrictedUserError("");
      const restrictedUser = await createRestrictedUser(username, password, email);
      await refreshData();
      setSelectedRestrictedUserId(restrictedUser.id);
    } catch (error) {
      setRestrictedUserError(
        error instanceof Error ? error.message : "Restricted user creation failed.",
      );
    }
  }

  async function handleSaveVisibility(
    userId: number,
    nextCategoryIds: number[],
    nextMediaItemIds: number[],
  ) {
    try {
      setVisibilityError("");

      const currentCategoryAssignments = categoryAssignments.filter(
        (assignment) => assignment.user === userId,
      );
      const currentMediaAssignments = mediaAssignments.filter((assignment) => assignment.user === userId);
      const currentCategoryIds = new Set(currentCategoryAssignments.map((assignment) => assignment.category));
      const currentMediaIds = new Set(currentMediaAssignments.map((assignment) => assignment.media_item));
      const desiredCategoryIds = new Set(nextCategoryIds);
      const desiredMediaIds = new Set(nextMediaItemIds);

      await Promise.all([
        ...currentCategoryAssignments
          .filter((assignment) => !desiredCategoryIds.has(assignment.category))
          .map((assignment) => deleteCategoryVisibilityAssignment(assignment.id)),
        ...currentMediaAssignments
          .filter((assignment) => !desiredMediaIds.has(assignment.media_item))
          .map((assignment) => deleteMediaVisibilityAssignment(assignment.id)),
      ]);

      await Promise.all([
        ...nextCategoryIds
          .filter((categoryId) => !currentCategoryIds.has(categoryId))
          .map((categoryId) => createCategoryVisibilityAssignment(userId, categoryId)),
        ...nextMediaItemIds
          .filter((mediaItemId) => !currentMediaIds.has(mediaItemId))
          .map((mediaItemId) => createMediaVisibilityAssignment(userId, mediaItemId)),
      ]);

      await refreshData();
    } catch (error) {
      setVisibilityError(error instanceof Error ? error.message : "Visibility update failed.");
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
      categoryError={categoryError}
      categoryAssignments={categoryAssignments}
      classificationError={classificationError}
      categories={categories}
      mediaAssignments={mediaAssignments}
      ownerMediaItems={mediaItems}
      mediaItems={visibleMediaItems}
      onCreateMediaItem={handleCreateMediaItem}
      onCreateCategory={handleCreateCategory}
      onCreateRestrictedUser={handleCreateRestrictedUser}
      onCreateTag={handleCreateTag}
      onChangeSearchQuery={setSearchQuery}
      onLogout={handleLogout}
      onPersistProgress={handlePersistProgress}
      onSaveVisibility={handleSaveVisibility}
      onSelectCategory={(categoryId) => {
        setSelectedCategoryId(categoryId);
      }}
      onSelectMediaItem={setSelectedMediaItem}
      onSelectRestrictedUser={setSelectedRestrictedUserId}
      onSelectTag={setSelectedTagId}
      onUpdateMediaItemAssignments={handleUpdateMediaItemAssignments}
      onUploadMediaItem={handleUploadMediaItem}
      playbackEntries={playbackEntries}
      restrictedUserError={restrictedUserError}
      restrictedUsers={restrictedUsers}
      searchQuery={searchQuery}
      searchSuggestions={searchSuggestions}
      selectedCategoryId={selectedCategoryId}
      selectedRestrictedUserId={selectedRestrictedUserId}
      selectedTagId={selectedTagId}
      selectedMediaItem={selectedMediaItem}
      session={session}
      tagError={tagError}
      tags={tags}
      visibilityError={visibilityError}
    />
  );
}
