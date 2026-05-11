import { useCallback, useEffect, useState } from "react";

import {
  fetchCategories,
  fetchCategoryVisibilityAssignments,
  fetchMediaItems,
  fetchMediaVisibilityAssignments,
  fetchPlaybackProgress,
  fetchRestrictedUsers,
  fetchTags,
} from "./api";
import type {
  CategoryVisibilityAssignment,
  Category,
  MediaItem,
  MediaItemVisibilityAssignment,
  PlaybackProgress,
  RestrictedUser,
  SessionState,
  Tag,
} from "./types";

export function useMediaLibraryData(session: SessionState) {
  const [mediaItems, setMediaItems] = useState<MediaItem[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [tags, setTags] = useState<Tag[]>([]);
  const [playbackEntries, setPlaybackEntries] = useState<PlaybackProgress[]>([]);
  const [restrictedUsers, setRestrictedUsers] = useState<RestrictedUser[]>([]);
  const [categoryAssignments, setCategoryAssignments] = useState<CategoryVisibilityAssignment[]>([]);
  const [mediaAssignments, setMediaAssignments] = useState<MediaItemVisibilityAssignment[]>([]);

  const refresh = useCallback(
    async (currentSession: SessionState = session) => {
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
    },
    [session],
  );

  useEffect(() => {
    if (!session.is_authenticated) {
      setMediaItems([]);
      setCategories([]);
      setTags([]);
      setPlaybackEntries([]);
      setRestrictedUsers([]);
      setCategoryAssignments([]);
      setMediaAssignments([]);
      return;
    }

    void refresh(session);
  }, [refresh, session]);

  return {
    mediaItems,
    categories,
    tags,
    playbackEntries,
    restrictedUsers,
    categoryAssignments,
    mediaAssignments,
    refresh,
  };
}
