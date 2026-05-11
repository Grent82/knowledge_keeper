import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import {
  createCategoryVisibilityAssignment,
  createCategory,
  createExternalSource,
  createMediaItemFromAsset,
  createMediaItemFromExternalSource,
  createMediaVisibilityAssignment,
  createPlaybackProgress,
  createRestrictedUser,
  createTag,
  deleteCategory,
  deleteCategoryVisibilityAssignment,
  deleteMediaItem,
  deleteMediaVisibilityAssignment,
  deleteRestrictedUser,
  deleteTag,
  fetchSearchSuggestions,
  fetchSession,
  login,
  logout,
  updateCategory,
  updateMediaItem,
  updateMediaItemAssignments,
  updatePlaybackProgress,
  updateTag,
  uploadMediaAsset,
} from "./api";
import { Dashboard } from "./Dashboard";
import { LoginForm } from "./LoginForm";
import type { Category, MediaItem, SearchSuggestions, SessionState } from "./types";
import { useMediaLibraryData } from "./useMediaLibraryData";

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
  const navigate = useNavigate();
  const { categoryId, mediaItemId } = useParams();
  const [session, setSession] = useState<SessionState>(anonymousSession);
  const {
    categories,
    mediaAssignments,
    mediaItems,
    playbackEntries,
    restrictedUsers,
    categoryAssignments,
    tags,
    refresh,
  } = useMediaLibraryData(session);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchSuggestions, setSearchSuggestions] = useState<SearchSuggestions | null>(null);
  const [selectedTagId, setSelectedTagId] = useState<number | null>(null);
  const [selectedRestrictedUserId, setSelectedRestrictedUserId] = useState<number | null>(null);
  const [loginError, setLoginError] = useState("");
  const [createError, setCreateError] = useState("");
  const [categoryError, setCategoryError] = useState("");
  const [tagError, setTagError] = useState("");
  const [classificationError, setClassificationError] = useState("");
  const [restrictedUserError, setRestrictedUserError] = useState("");
  const [visibilityError, setVisibilityError] = useState("");

  const parsedCategoryId = categoryId ? Number(categoryId) : null;
  const selectedCategoryId =
    parsedCategoryId !== null && !Number.isNaN(parsedCategoryId) ? parsedCategoryId : null;
  const parsedMediaItemId = mediaItemId ? Number(mediaItemId) : null;
  const selectedMediaItem =
    parsedMediaItemId !== null && !Number.isNaN(parsedMediaItemId)
      ? mediaItems.find((item) => item.id === parsedMediaItemId) ?? null
      : null;

  useEffect(() => {
    void fetchSession().then(setSession);
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

  function navigateToMediaItem(itemId: number, categorySelection: number | null = selectedCategoryId) {
    if (categorySelection !== null) {
      navigate(`/c/${categorySelection}/m/${itemId}`);
      return;
    }

    navigate(`/m/${itemId}`);
  }

  function handleSelectCategory(categorySelection: number | null) {
    if (categorySelection === null) {
      navigate("/");
      return;
    }

    navigate(`/c/${categorySelection}`);
  }

  function handleSelectMediaItem(item: MediaItem) {
    navigateToMediaItem(item.id);
  }

  const visibleCategoryIds = collectVisibleCategoryIds(categories, selectedCategoryId);
  const visibleMediaItems = mediaItems.filter((item) => {
    const categoryMatch =
      visibleCategoryIds === null ||
      item.categories.some((categorySelection) => visibleCategoryIds.has(categorySelection));
    const tagMatch = selectedTagId === null || item.tags.includes(selectedTagId);
    return categoryMatch && tagMatch;
  });

  async function handleLogin(username: string, password: string) {
    try {
      setLoginError("");
      const nextSession = await login(username, password);
      setSession(nextSession);
    } catch (error) {
      setLoginError(error instanceof Error ? error.message : "Login failed.");
    }
  }

  async function handleLogout() {
    await logout();
    navigate("/");
    setSession(anonymousSession);
    setSearchQuery("");
    setSearchSuggestions(null);
    setSelectedTagId(null);
    setSelectedRestrictedUserId(null);
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
      await refresh();
      navigateToMediaItem(item.id);
    } catch (error) {
      setCreateError(error instanceof Error ? error.message : "Upload failed.");
    }
  }

  async function handleCreateExternalMediaItem(
    provider: string,
    sourceUrl: string,
    externalId: string,
    sourceTitle: string,
    authorName: string,
    itemTitle: string,
    mediaType: string,
    description: string,
  ) {
    try {
      setCreateError("");
      const source = await createExternalSource(
        provider,
        sourceUrl,
        externalId,
        sourceTitle,
        authorName,
      );
      const item = await createMediaItemFromExternalSource(
        itemTitle,
        mediaType,
        description,
        source.id,
      );
      await refresh();
      navigateToMediaItem(item.id);
    } catch (error) {
      setCreateError(error instanceof Error ? error.message : "External source creation failed.");
    }
  }

  async function handlePersistProgress(mediaItemId: number, currentTime: number, duration: number) {
    const progressPercent = duration > 0 ? (currentTime / duration) * 100 : 0;
    const existingEntry = playbackEntries.find((entry) => entry.media_item === mediaItemId);

    if (existingEntry) {
      await updatePlaybackProgress(existingEntry.id, mediaItemId, currentTime, progressPercent);
    } else {
      await createPlaybackProgress(mediaItemId, currentTime, progressPercent);
    }

    await refresh();
  }

  async function handleCreateCategory(name: string, parentId: number | null) {
    try {
      setCategoryError("");
      await createCategory(name, parentId);
      await refresh();
    } catch (error) {
      setCategoryError(error instanceof Error ? error.message : "Category creation failed.");
    }
  }

  async function handleCreateTag(name: string) {
    try {
      setTagError("");
      await createTag(name);
      await refresh();
    } catch (error) {
      setTagError(error instanceof Error ? error.message : "Tag creation failed.");
    }
  }

  async function handleUpdateMediaItem(
    id: number,
    data: { title: string; description: string; media_type: string },
  ) {
    try {
      setCreateError("");
      const updatedMediaItem = await updateMediaItem(id, data);
      await refresh();
      navigateToMediaItem(updatedMediaItem.id);
    } catch (error) {
      setCreateError(error instanceof Error ? error.message : "Media item update failed.");
    }
  }

  async function handleDeleteMediaItem(id: number) {
    try {
      setCreateError("");
      await deleteMediaItem(id);
      navigate("/");
      await refresh();
    } catch (error) {
      setCreateError(error instanceof Error ? error.message : "Media item deletion failed.");
    }
  }

  async function handleUpdateCategory(id: number, data: { name: string; parent: number | null }) {
    try {
      setCategoryError("");
      await updateCategory(id, data);
      await refresh();
    } catch (error) {
      setCategoryError(error instanceof Error ? error.message : "Category update failed.");
    }
  }

  async function handleDeleteCategory(id: number) {
    try {
      setCategoryError("");
      await deleteCategory(id);
      await refresh();
    } catch (error) {
      setCategoryError(error instanceof Error ? error.message : "Category deletion failed.");
    }
  }

  async function handleUpdateTag(id: number, data: { name: string }) {
    try {
      setTagError("");
      await updateTag(id, data);
      await refresh();
    } catch (error) {
      setTagError(error instanceof Error ? error.message : "Tag update failed.");
    }
  }

  async function handleDeleteTag(id: number) {
    try {
      setTagError("");
      await deleteTag(id);
      await refresh();
    } catch (error) {
      setTagError(error instanceof Error ? error.message : "Tag deletion failed.");
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
      await refresh();
      navigateToMediaItem(updatedMediaItem.id);
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
      await refresh();
      setSelectedRestrictedUserId(restrictedUser.id);
    } catch (error) {
      setRestrictedUserError(
        error instanceof Error ? error.message : "Restricted user creation failed.",
      );
    }
  }

  async function handleDeleteRestrictedUser(id: number) {
    try {
      setRestrictedUserError("");
      await deleteRestrictedUser(id);
      await refresh();
    } catch (error) {
      setRestrictedUserError(
        error instanceof Error ? error.message : "Restricted user deletion failed.",
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
          .filter((categorySelection) => !currentCategoryIds.has(categorySelection))
          .map((categorySelection) => createCategoryVisibilityAssignment(userId, categorySelection)),
        ...nextMediaItemIds
          .filter((itemId) => !currentMediaIds.has(itemId))
          .map((itemId) => createMediaVisibilityAssignment(userId, itemId)),
      ]);

      await refresh();
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
      categoryAssignments={categoryAssignments}
      categoryError={categoryError}
      categories={categories}
      classificationError={classificationError}
      createError={createError}
      mediaAssignments={mediaAssignments}
      mediaItems={visibleMediaItems}
      onChangeSearchQuery={setSearchQuery}
      onCreateCategory={handleCreateCategory}
      onCreateExternalMediaItem={handleCreateExternalMediaItem}
      onCreateRestrictedUser={handleCreateRestrictedUser}
      onCreateTag={handleCreateTag}
      onDeleteCategory={handleDeleteCategory}
      onDeleteMediaItem={handleDeleteMediaItem}
      onDeleteRestrictedUser={handleDeleteRestrictedUser}
      onDeleteTag={handleDeleteTag}
      onLogout={handleLogout}
      onPersistProgress={handlePersistProgress}
      onSaveVisibility={handleSaveVisibility}
      onSelectCategory={handleSelectCategory}
      onSelectMediaItem={handleSelectMediaItem}
      onSelectRestrictedUser={setSelectedRestrictedUserId}
      onSelectTag={setSelectedTagId}
      onUpdateCategory={handleUpdateCategory}
      onUpdateMediaItem={handleUpdateMediaItem}
      onUpdateMediaItemAssignments={handleUpdateMediaItemAssignments}
      onUpdateTag={handleUpdateTag}
      onUploadMediaItem={handleUploadMediaItem}
      ownerMediaItems={mediaItems}
      playbackEntries={playbackEntries}
      restrictedUserError={restrictedUserError}
      restrictedUsers={restrictedUsers}
      searchQuery={searchQuery}
      searchSuggestions={searchSuggestions}
      selectedCategoryId={selectedCategoryId}
      selectedMediaItem={selectedMediaItem}
      selectedRestrictedUserId={selectedRestrictedUserId}
      selectedTagId={selectedTagId}
      session={session}
      tagError={tagError}
      tags={tags}
      visibilityError={visibilityError}
    />
  );
}
