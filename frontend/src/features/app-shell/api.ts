import type {
  CategoryVisibilityAssignment,
  Category,
  CoachChatResponse,
  CoachHistoryEntry,
  ExternalSource,
  KnowledgeNote,
  MediaItem,
  MediaItemVisibilityAssignment,
  PlaybackProgress,
  RestrictedUser,
  SearchSuggestions,
  SessionState,
  Summary,
  Tag,
  Transcript,
  TranscriptSegment,
} from "./types";

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

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const method = init?.method ?? "GET";
  const headers = new Headers(init?.headers ?? {});
  const isFormData = init?.body instanceof FormData;

  if (!headers.has("Content-Type") && init?.body && !isFormData) {
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
    let parsedMessage = message || `${response.status} ${response.statusText}`;

    try {
      const payload = JSON.parse(message) as { detail?: string };
      parsedMessage = payload.detail ?? parsedMessage;
    } catch {
      // Ignore non-JSON error payloads.
    }

    throw new ApiError(response.status, parsedMessage);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export function fetchSession() {
  return request<SessionState>("/api/auth/session");
}

export function postCoachQuestion(
  question: string,
  history: CoachHistoryEntry[],
  contextTag = "",
) {
  return request<CoachChatResponse>("/api/coach/chat/", {
    method: "POST",
    body: JSON.stringify({ question, history, context_tag: contextTag }),
  });
}

export function fetchRestrictedUsers() {
  return request<RestrictedUser[]>("/api/auth/restricted-users");
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

export function fetchCategories() {
  return request<Category[]>("/api/media/categories");
}

export function fetchTags() {
  return request<Tag[]>("/api/media/tags");
}

export function fetchSearchSuggestions(query: string) {
  return request<SearchSuggestions>(`/api/media/search?q=${encodeURIComponent(query)}`);
}

export function createRestrictedUser(username: string, password: string, email: string) {
  return request<RestrictedUser>("/api/auth/restricted-users", {
    method: "POST",
    body: JSON.stringify({ username, password, email }),
  });
}

export function createCategory(name: string, parent: number | null) {
  return request<Category>("/api/media/categories", {
    method: "POST",
    body: JSON.stringify({
      name,
      parent,
    }),
  });
}

export function createTag(name: string) {
  return request<Tag>("/api/media/tags", {
    method: "POST",
    body: JSON.stringify({ name }),
  });
}

export function fetchPlaybackProgress() {
  return request<PlaybackProgress[]>("/api/playback/progress");
}

export function fetchTranscripts(mediaItemId: number) {
  return request<Transcript[]>(`/api/playback/transcripts?media_item=${mediaItemId}`);
}

export function fetchTranscriptSegments(transcriptId: number) {
  return request<TranscriptSegment[]>(`/api/playback/segments?transcript=${transcriptId}`);
}

export function fetchSummaries(mediaItemId: number) {
  return request<Summary[]>(`/api/playback/summaries?media_item=${mediaItemId}`);
}

export async function triggerTranscription(
  mediaItemId: number,
): Promise<{ status: string; media_item_id: number }> {
  return request(`/api/playback/trigger/${mediaItemId}/`, { method: "POST" });
}

export async function triggerSummary(
  mediaItemId: number,
  kind: "short" | "detailed" | "bullet",
): Promise<{ status: string; media_item_id?: number; summary_id?: number; kind: string }> {
  return request(`/api/playback/trigger/${mediaItemId}/summary/`, {
    method: "POST",
    body: JSON.stringify({ kind }),
  });
}

export type CreateKnowledgeNotePayload = Pick<
  KnowledgeNote,
  "title" | "content_markdown" | "kind" | "media_item" | "transcript" | "linked_notes"
>;

export type UpdateKnowledgeNotePayload = Partial<CreateKnowledgeNotePayload>;

export interface RelatedNote {
  id: number;
  title: string;
  core_insight: string;
  similarity_score: number;
}

export async function fetchKnowledgeNotes(mediaItemId?: number): Promise<KnowledgeNote[]> {
  const params = mediaItemId ? `?media_item=${mediaItemId}` : "";
  return request(`/api/knowledge-notes/${params}`);
}

export async function createKnowledgeNote(data: CreateKnowledgeNotePayload): Promise<KnowledgeNote> {
  return request("/api/knowledge-notes/", { method: "POST", body: JSON.stringify(data) });
}

export async function updateKnowledgeNote(
  id: number,
  data: UpdateKnowledgeNotePayload,
): Promise<KnowledgeNote> {
  return request(`/api/knowledge-notes/${id}`, { method: "PATCH", body: JSON.stringify(data) });
}

export async function deleteKnowledgeNote(id: number): Promise<void> {
  return request(`/api/knowledge-notes/${id}`, { method: "DELETE" });
}

export async function fetchRelatedNotes(noteId: number): Promise<RelatedNote[]> {
  return request(`/api/knowledge-notes/${noteId}/related/`);
}

export async function triggerKnowledgeNoteGeneration(
  transcriptId: number,
  force = false,
): Promise<{ status: string; transcript_id: number }> {
  return request(`/api/knowledge-notes/generate/${transcriptId}/`, {
    method: "POST",
    body: JSON.stringify({ force }),
  });
}

export function fetchCategoryVisibilityAssignments() {
  return request<CategoryVisibilityAssignment[]>("/api/access/category-assignments");
}

export function fetchMediaVisibilityAssignments() {
  return request<MediaItemVisibilityAssignment[]>("/api/access/media-assignments");
}

export function createCategoryVisibilityAssignment(userId: number, categoryId: number) {
  return request<CategoryVisibilityAssignment>("/api/access/category-assignments", {
    method: "POST",
    body: JSON.stringify({ user: userId, category: categoryId }),
  });
}

export function createMediaVisibilityAssignment(userId: number, mediaItemId: number) {
  return request<MediaItemVisibilityAssignment>("/api/access/media-assignments", {
    method: "POST",
    body: JSON.stringify({ user: userId, media_item: mediaItemId }),
  });
}

export function deleteCategoryVisibilityAssignment(assignmentId: number) {
  return request<void>(`/api/access/category-assignments/${assignmentId}`, {
    method: "DELETE",
  });
}

export function deleteMediaVisibilityAssignment(assignmentId: number) {
  return request<void>(`/api/access/media-assignments/${assignmentId}`, {
    method: "DELETE",
  });
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

export function uploadMediaAsset(file: File) {
  const body = new FormData();
  body.set("origin", "local_upload");
  body.set("uploaded_file", file);
  body.set("storage_path", file.name);
  body.set("mime_type", file.type);

  return request<{ id: number }>("/api/media/assets", {
    method: "POST",
    body,
  });
}

export function createMediaItemFromAsset(
  title: string,
  mediaType: string,
  description: string,
  assetId: number,
) {
  return request<MediaItem>("/api/media/items", {
    method: "POST",
    body: JSON.stringify({
      title,
      media_type: mediaType,
      description,
      asset: assetId,
      categories: [],
      tags: [],
    }),
  });
}

export function createExternalSource(
  provider: string,
  sourceUrl: string,
  externalId: string,
  title: string,
  authorName: string,
) {
  return request<ExternalSource>("/api/media/sources", {
    method: "POST",
    body: JSON.stringify({
      provider,
      source_url: sourceUrl,
      external_id: externalId,
      title,
      author_name: authorName,
    }),
  });
}

export function createMediaItemFromExternalSource(
  title: string,
  mediaType: string,
  description: string,
  sourceId: number,
) {
  return request<MediaItem>("/api/media/items", {
    method: "POST",
    body: JSON.stringify({
      title,
      media_type: mediaType,
      description,
      external_source: sourceId,
      categories: [],
      tags: [],
    }),
  });
}

export function updateMediaItemAssignments(
  mediaItemId: number,
  categories: number[],
  tags: number[],
) {
  return request<MediaItem>(`/api/media/items/${mediaItemId}`, {
    method: "PATCH",
    body: JSON.stringify({
      categories,
      tags,
    }),
  });
}

export function updateMediaItem(
  id: number,
  data: { title: string; description: string; media_type: string },
) {
  return request<MediaItem>(`/api/media/items/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export function deleteMediaItem(id: number) {
  return request<void>(`/api/media/items/${id}`, { method: "DELETE" });
}

export function updateCategory(id: number, data: { name: string; parent: number | null }) {
  return request<Category>(`/api/media/categories/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export function deleteCategory(id: number) {
  return request<void>(`/api/media/categories/${id}`, { method: "DELETE" });
}

export function updateTag(id: number, data: { name: string }) {
  return request<Tag>(`/api/media/tags/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export function deleteTag(id: number) {
  return request<void>(`/api/media/tags/${id}`, { method: "DELETE" });
}

export function deleteRestrictedUser(id: number) {
  return request<void>(`/api/auth/restricted-users/${id}`, { method: "DELETE" });
}

export function createPlaybackProgress(mediaItemId: number, positionSeconds: number, progressPercent: number) {
  return request<PlaybackProgress>("/api/playback/progress", {
    method: "POST",
    body: JSON.stringify({
      media_item: mediaItemId,
      status: progressPercent >= 99 ? "completed" : "in_progress",
      position_seconds: Math.floor(positionSeconds),
      progress_percent: progressPercent.toFixed(2),
    }),
  });
}

export function updatePlaybackProgress(
  id: number,
  mediaItemId: number,
  positionSeconds: number,
  progressPercent: number,
) {
  return request<PlaybackProgress>(`/api/playback/progress/${id}`, {
    method: "PATCH",
    body: JSON.stringify({
      media_item: mediaItemId,
      status: progressPercent >= 99 ? "completed" : "in_progress",
      position_seconds: Math.floor(positionSeconds),
      progress_percent: progressPercent.toFixed(2),
    }),
  });
}
