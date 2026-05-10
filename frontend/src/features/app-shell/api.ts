import type { MediaItem, PlaybackProgress, SessionState } from "./types";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    ...init,
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `${response.status} ${response.statusText}`);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export function fetchSession() {
  return request<SessionState>("/api/auth/session");
}

export function login(username: string, password: string) {
  return request<SessionState>("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
}

export function logout() {
  return request<void>("/api/auth/logout", { method: "POST" });
}

export function fetchMediaItems() {
  return request<MediaItem[]>("/api/media/items");
}

export function fetchPlaybackProgress() {
  return request<PlaybackProgress[]>("/api/playback/progress");
}

export function createMediaItem(title: string, mediaType: string, description: string) {
  return request<MediaItem>("/api/media/items", {
    method: "POST",
    body: JSON.stringify({
      title,
      media_type: mediaType,
      description,
      categories: [],
      tags: [],
    }),
  });
}
