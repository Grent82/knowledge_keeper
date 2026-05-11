import type { MediaItem, PlaybackProgress, SessionState } from "./types";

function readCookie(name: string): string {
  const cookies = document.cookie.split(";").map((value) => value.trim());
  const cookie = cookies.find((value) => value.startsWith(`${name}=`));
  return cookie ? decodeURIComponent(cookie.slice(name.length + 1)) : "";
}

function isUnsafeMethod(method: string): boolean {
  return !["GET", "HEAD", "OPTIONS", "TRACE"].includes(method.toUpperCase());
}

async function ensureCsrfCookie(): Promise<string> {
  let token = readCookie("csrftoken");
  if (token) {
    return token;
  }

  await fetch("/api/auth/session", {
    credentials: "include",
  });

  token = readCookie("csrftoken");
  return token;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const method = init?.method ?? "GET";
  const headers = new Headers(init?.headers ?? {});

  if (!headers.has("Content-Type") && init?.body) {
    headers.set("Content-Type", "application/json");
  }

  if (isUnsafeMethod(method)) {
    const csrfToken = await ensureCsrfCookie();
    if (csrfToken) {
      headers.set("X-CSRFToken", csrfToken);
    }
  }

  const response = await fetch(path, {
    credentials: "include",
    headers,
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
