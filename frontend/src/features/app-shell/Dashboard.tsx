import { useCallback, useEffect, useState } from "react";

import { deleteKnowledgeNote, fetchKnowledgeNotes } from "./api";
import { Breadcrumbs } from "./Breadcrumbs";
import { CategoryManager } from "./CategoryManager";
import { CategoryTree } from "./CategoryTree";
import { CoachPanel } from "./CoachPanel";
import { ExternalSourceForm } from "./ExternalSourceForm";
import { KnowledgeNoteEditor } from "./KnowledgeNoteEditor";
import { KnowledgeNoteList } from "./KnowledgeNoteList";
import { MediaPlayerCard } from "./MediaPlayerCard";
import { MediaClassificationCard } from "./MediaClassificationCard";
import { TranscriptPanel } from "./TranscriptPanel";
import { RestrictedUserAccessCard } from "./RestrictedUserAccessCard";
import { SearchPanel } from "./SearchPanel";
import { TagManager } from "./TagManager";
import { UploadMediaForm } from "./UploadMediaForm";
import type {
  CategoryVisibilityAssignment,
  Category,
  KnowledgeNote,
  MediaItem,
  MediaItemVisibilityAssignment,
  PlaybackProgress,
  RestrictedUser,
  SearchSuggestions,
  SessionState,
  Tag,
} from "./types";

type DashboardProps = {
  session: SessionState;
  categories: Category[];
  categoryAssignments: CategoryVisibilityAssignment[];
  tags: Tag[];
  mediaAssignments: MediaItemVisibilityAssignment[];
  ownerMediaItems: MediaItem[];
  mediaItems: MediaItem[];
  playbackEntries: PlaybackProgress[];
  createError: string;
  categoryError: string;
  tagError: string;
  classificationError: string;
  restrictedUserError: string;
  visibilityError: string;
  searchQuery: string;
  searchSuggestions: SearchSuggestions | null;
  selectedMediaItem: MediaItem | null;
  selectedCategoryId: number | null;
  selectedRestrictedUserId: number | null;
  selectedTagId: number | null;
  restrictedUsers: RestrictedUser[];
  onLogout: () => Promise<void>;
  onCreateCategory: (name: string, parentId: number | null) => Promise<void>;
  onCreateRestrictedUser: (username: string, password: string, email: string) => Promise<void>;
  onCreateTag: (name: string) => Promise<void>;
  onDeleteCategory: (id: number) => Promise<void>;
  onDeleteMediaItem: (id: number) => Promise<void>;
  onDeleteRestrictedUser: (id: number) => Promise<void>;
  onDeleteTag: (id: number) => Promise<void>;
  onSelectMediaItem: (mediaItem: MediaItem) => void;
  onSelectCategory: (categoryId: number | null) => void;
  onSelectRestrictedUser: (userId: number | null) => void;
  onSelectTag: (tagId: number | null) => void;
  onChangeSearchQuery: (value: string) => void;
  onUploadMediaItem: (
    file: File,
    title: string,
    mediaType: string,
    description: string,
  ) => Promise<void>;
  onCreateExternalMediaItem: (
    provider: string,
    sourceUrl: string,
    externalId: string,
    sourceTitle: string,
    authorName: string,
    itemTitle: string,
    mediaType: string,
    description: string,
  ) => Promise<void>;
  onUpdateCategory: (id: number, data: { name: string; parent: number | null }) => Promise<void>;
  onUpdateMediaItem: (
    id: number,
    data: { title: string; description: string; media_type: string },
  ) => Promise<void>;
  onUpdateMediaItemAssignments: (
    mediaItemId: number,
    categoryIds: number[],
    tagIds: number[],
  ) => Promise<void>;
  onUpdateTag: (id: number, data: { name: string }) => Promise<void>;
  onSaveVisibility: (
    userId: number,
    categoryIds: number[],
    mediaItemIds: number[],
  ) => Promise<void>;
  onPersistProgress: (mediaItemId: number, currentTime: number, duration: number) => Promise<void>;
};

function formatSeconds(s: number): string {
  const m = Math.floor(s / 60);
  const sec = s % 60;
  return `${m}:${sec.toString().padStart(2, "0")}`;
}

function formatProgressPercent(progressPercent: string): number {
  const parsedValue = Number.parseFloat(progressPercent);
  if (Number.isNaN(parsedValue)) {
    return 0;
  }

  return Math.max(0, Math.min(100, Math.round(parsedValue)));
}

function formatPlaybackStatus(status: string): string {
  switch (status) {
    case "completed":
      return "Completed";
    case "in_progress":
      return "In progress";
    default:
      return "Not started";
  }
}

function resolveMediaTypeBadge(mediaType: string): string {
  return mediaType === "video" ? "▶" : "♪";
}

export function Dashboard({
  session,
  categories,
  categoryAssignments,
  tags,
  mediaAssignments,
  ownerMediaItems,
  mediaItems,
  playbackEntries,
  createError,
  categoryError,
  tagError,
  classificationError,
  restrictedUserError,
  visibilityError,
  searchQuery,
  searchSuggestions,
  selectedMediaItem,
  selectedCategoryId,
  selectedRestrictedUserId,
  selectedTagId,
  restrictedUsers,
  onLogout,
  onCreateCategory,
  onCreateRestrictedUser,
  onCreateTag,
  onDeleteCategory,
  onDeleteMediaItem,
  onDeleteRestrictedUser,
  onDeleteTag,
  onChangeSearchQuery,
  onSelectCategory,
  onSelectMediaItem,
  onSelectRestrictedUser,
  onSelectTag,
  onUploadMediaItem,
  onCreateExternalMediaItem,
  onUpdateCategory,
  onUpdateMediaItem,
  onUpdateMediaItemAssignments,
  onUpdateTag,
  onSaveVisibility,
  onPersistProgress,
}: DashboardProps) {
  const [filterMediaType, setFilterMediaType] = useState<"all" | "audio" | "video">("all");
  const [filterStatus, setFilterStatus] = useState<
    "all" | "not_started" | "in_progress" | "completed"
  >("all");
  const [sortBy, setSortBy] = useState<"title" | "date" | "progress">("title");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("asc");
  const [knowledgeNotes, setKnowledgeNotes] = useState<KnowledgeNote[]>([]);
  const [knowledgeNotesLoading, setKnowledgeNotesLoading] = useState(false);
  const [knowledgeNotesError, setKnowledgeNotesError] = useState("");
  const [selectedNote, setSelectedNote] = useState<KnowledgeNote | null>(null);
  const [showNoteEditor, setShowNoteEditor] = useState(false);
  const selectedProgressEntry =
    playbackEntries.find((entry) => entry.media_item === selectedMediaItem?.id) ?? null;
  const mediaTitleById = new Map(mediaItems.map((item) => [item.id, item.title]));
  const progressFor = (item: MediaItem) =>
    playbackEntries.find((entry) => entry.media_item === item.id) ?? null;
  const filteredItems = [...mediaItems]
    .filter((item) => filterMediaType === "all" || item.media_type === filterMediaType)
    .filter((item) => {
      if (filterStatus === "all") {
        return true;
      }
      const entry = progressFor(item);
      const status = entry?.status ?? "not_started";
      return status === filterStatus;
    })
    .sort((a, b) => {
      let cmp = 0;
      if (sortBy === "title") {
        cmp = a.title.localeCompare(b.title);
      } else if (sortBy === "date") {
        cmp = (a.published_at ?? a.id.toString()).localeCompare(b.published_at ?? b.id.toString());
      } else if (sortBy === "progress") {
        const pa = formatProgressPercent(progressFor(a)?.progress_percent ?? "0");
        const pb = formatProgressPercent(progressFor(b)?.progress_percent ?? "0");
        cmp = pa - pb;
      }
      return sortDir === "asc" ? cmp : -cmp;
    });

  const loadNotes = useCallback(async (): Promise<KnowledgeNote[]> => {
    if (session.role !== "owner") {
      setKnowledgeNotes([]);
      setSelectedNote(null);
      return [];
    }

    setKnowledgeNotesLoading(true);
    setKnowledgeNotesError("");

    try {
      const nextNotes = await fetchKnowledgeNotes();
      setKnowledgeNotes(nextNotes);
      setSelectedNote((currentNote) =>
        currentNote ? nextNotes.find((candidate) => candidate.id === currentNote.id) ?? null : currentNote,
      );
      return nextNotes;
    } catch (nextError) {
      const message = nextError instanceof Error ? nextError.message : "Notizen konnten nicht geladen werden.";
      setKnowledgeNotesError(message);
      setKnowledgeNotes([]);
      setSelectedNote(null);
      return [];
    } finally {
      setKnowledgeNotesLoading(false);
    }
  }, [session.role]);

  useEffect(() => {
    void loadNotes();
  }, [loadNotes]);

  async function handleNoteSaved(note: KnowledgeNote): Promise<void> {
    const nextNotes = await loadNotes();
    setSelectedNote(nextNotes.find((candidate) => candidate.id === note.id) ?? note);
    setShowNoteEditor(false);
  }

  async function handleNoteDelete(noteId: number): Promise<void> {
    await deleteKnowledgeNote(noteId);
    setSelectedNote(null);
    setShowNoteEditor(false);
    await loadNotes();
  }

  return (
    <>
      <section className="hero">
        <p className="eyebrow">Knowledge Keeper</p>
        <h1>Private media and knowledge platform</h1>
        <p className="intro">
          Logged in as <strong>{session.username}</strong> with role <strong>{session.role}</strong>.
        </p>
        <div className="hero-actions">
          <button className="secondary-button" onClick={() => void onLogout()} type="button">
            Logout
          </button>
        </div>
      </section>

      <Breadcrumbs
        categories={categories}
        onSelectCategory={onSelectCategory}
        selectedCategoryId={selectedCategoryId}
      />

      <CoachPanel mediaTitleById={mediaTitleById} />

      <section className="grid">
        <CategoryTree
          categories={categories}
          onSelectCategory={onSelectCategory}
          selectedCategoryId={selectedCategoryId}
        />

        <SearchPanel
          onChangeQuery={onChangeSearchQuery}
          onSelectCategory={(categoryId) => {
            onSelectCategory(categoryId);
          }}
          onSelectMediaItem={onSelectMediaItem}
          onSelectTag={onSelectTag}
          query={searchQuery}
          selectedTagId={selectedTagId}
          suggestions={searchSuggestions}
          tags={tags}
        />

        <article className="card">
          <h2>Media Library</h2>
          <p className="muted">Current media items available in the selected context.</p>
          <div className="library-filters">
            <select
              onChange={(event) => setFilterMediaType(event.target.value as "all" | "audio" | "video")}
              value={filterMediaType}
            >
              <option value="all">All types</option>
              <option value="audio">Audio</option>
              <option value="video">Video</option>
            </select>
            <select
              onChange={(event) =>
                setFilterStatus(
                  event.target.value as "all" | "not_started" | "in_progress" | "completed",
                )
              }
              value={filterStatus}
            >
              <option value="all">All status</option>
              <option value="not_started">Not started</option>
              <option value="in_progress">In progress</option>
              <option value="completed">Completed</option>
            </select>
            <select
              onChange={(event) => setSortBy(event.target.value as "title" | "date" | "progress")}
              value={sortBy}
            >
              <option value="title">Sort: Title</option>
              <option value="date">Sort: Date</option>
              <option value="progress">Sort: Progress</option>
            </select>
            <button
              className="secondary-button sort-dir-button"
              onClick={() => setSortDir((currentDir) => (currentDir === "asc" ? "desc" : "asc"))}
              type="button"
            >
              {sortDir === "asc" ? "↑" : "↓"}
            </button>
          </div>
          {filteredItems.length === 0 ? (
            <p className="empty-state">No media items yet.</p>
          ) : (
            <ul className="simple-list">
              {filteredItems.map((item) => {
                const playbackEntry = progressFor(item);
                const progressPercent = playbackEntry
                  ? formatProgressPercent(playbackEntry.progress_percent)
                  : 0;

                return (
                  <li
                    key={item.id}
                    className={selectedMediaItem?.id === item.id ? "selected-item" : undefined}
                  >
                    <button
                      className="list-button media-list-button"
                      onClick={() => onSelectMediaItem(item)}
                      type="button"
                    >
                      <div className="media-list-title-row">
                        <span aria-hidden="true" className="media-type-badge">
                          {resolveMediaTypeBadge(item.media_type)}
                        </span>
                        <strong>{item.title}</strong>
                      </div>
                      <span>
                        {item.media_type} · {item.player_display_mode}
                      </span>
                      {playbackEntry ? (
                        <div aria-hidden="true" className="progress-bar-track">
                          <div
                            className={`progress-bar-fill ${playbackEntry.status === "completed" ? "completed" : ""}`.trim()}
                            style={{ width: `${progressPercent}%` }}
                          />
                        </div>
                      ) : null}
                    </button>
                  </li>
                );
              })}
            </ul>
          )}
        </article>

        <MediaPlayerCard
          mediaItem={selectedMediaItem}
          onDeleteMediaItem={session.role === "owner" ? onDeleteMediaItem : undefined}
          onPersistProgress={onPersistProgress}
          onUpdateMediaItem={session.role === "owner" ? onUpdateMediaItem : undefined}
          progressEntry={selectedProgressEntry}
        />
        {session.role === "owner" && selectedMediaItem ? (
          <TranscriptPanel mediaItem={selectedMediaItem} />
        ) : null}
      </section>

      <section className="grid">
        <article className="card">
          <h2>Playback Progress</h2>
          <p className="muted">Saved continue-watching positions for the current account.</p>
          {playbackEntries.length === 0 ? (
            <p className="empty-state">No playback entries yet.</p>
          ) : (
            <ul className="simple-list">
              {playbackEntries.map((entry) => (
                <li key={entry.id}>
                  <strong>{mediaTitleById.get(entry.media_item) ?? `Media #${entry.media_item}`}</strong>
                  <span>
                    {formatPlaybackStatus(entry.status)} · {formatSeconds(entry.position_seconds)} · {formatProgressPercent(entry.progress_percent)}%
                  </span>
                </li>
              ))}
            </ul>
          )}
        </article>
      </section>

      {session.role === "owner" ? (
        <>
          <hr className="section-divider" />
          <h2 className="section-heading">Wissensnotizen</h2>
          <section className="grid knowledge-notes-grid">
            <KnowledgeNoteList
              notes={knowledgeNotes}
              onCreate={() => {
                setSelectedNote(null);
                setShowNoteEditor(true);
              }}
              onSelect={(note) => {
                setSelectedNote(note);
                setShowNoteEditor(true);
              }}
            />
            {showNoteEditor ? (
              <KnowledgeNoteEditor
                allNotes={knowledgeNotes}
                initialMediaItemId={selectedMediaItem?.id ?? null}
                note={selectedNote}
                onClose={() => setShowNoteEditor(false)}
                onDelete={handleNoteDelete}
                onSave={(note) => {
                  void handleNoteSaved(note);
                }}
              />
            ) : (
              <article className="card knowledge-note-editor">
                <h2>Notizbereich</h2>
                <p className="muted">
                  {knowledgeNotesLoading
                    ? "Wissensnotizen werden geladen…"
                    : knowledgeNotesError || "Wähle eine Notiz oder erstelle eine neue."}
                </p>
              </article>
            )}
          </section>

          <h2 className="section-heading">Library Management</h2>
          <section className="grid">
            <UploadMediaForm error={createError} onSubmit={onUploadMediaItem} />
            <ExternalSourceForm error={createError} onSubmit={onCreateExternalMediaItem} />
            <CategoryManager
              categories={categories}
              error={categoryError}
              onDelete={onDeleteCategory}
              onSubmit={onCreateCategory}
              onUpdate={onUpdateCategory}
            />
            <TagManager
              error={tagError}
              onDelete={onDeleteTag}
              onSubmit={onCreateTag}
              onUpdate={onUpdateTag}
              tags={tags}
            />
            <MediaClassificationCard
              key={selectedMediaItem?.id ?? "none"}
              categories={categories}
              error={classificationError}
              mediaItem={selectedMediaItem}
              onSubmit={onUpdateMediaItemAssignments}
              tags={tags}
            />
          </section>

          <h2 className="section-heading">Access Control</h2>
          <section className="grid">
            <RestrictedUserAccessCard
              key={selectedRestrictedUserId ?? "none"}
              categories={categories}
              categoryAssignments={categoryAssignments}
              mediaAssignments={mediaAssignments}
              mediaItems={ownerMediaItems}
              onCreateRestrictedUser={onCreateRestrictedUser}
              onDeleteRestrictedUser={onDeleteRestrictedUser}
              onSaveVisibility={onSaveVisibility}
              onSelectRestrictedUser={onSelectRestrictedUser}
              restrictedUsers={restrictedUsers}
              selectedRestrictedUserId={selectedRestrictedUserId}
              userError={restrictedUserError}
              visibilityError={visibilityError}
            />
          </section>
        </>
      ) : null}
    </>
  );
}
