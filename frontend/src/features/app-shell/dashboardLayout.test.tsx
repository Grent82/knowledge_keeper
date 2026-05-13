import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { Dashboard } from "./Dashboard";
import { TranscriptPanel } from "./TranscriptPanel";
import type { MediaItem, SessionState } from "./types";

function buildSession(): SessionState {
  return {
    is_authenticated: true,
    username: "owner",
    role: "owner",
  };
}

function buildMediaItem(): MediaItem {
  return {
    id: 1,
    title: "Sample media",
    description: "desc",
    media_type: "audio",
    player_display_mode: "native",
    owner: 1,
    asset: null,
    asset_detail: null,
    external_source: null,
    external_source_detail: null,
    categories: [],
    tags: [],
    published_at: null,
  };
}

function buildDashboardProps(): React.ComponentProps<typeof Dashboard> {
  const session = buildSession();
  const mediaItem = buildMediaItem();

  return {
    session,
    categories: [],
    categoryAssignments: [],
    tags: [],
    mediaAssignments: [],
    ownerMediaItems: [mediaItem],
    mediaItems: [mediaItem],
    playbackEntries: [],
    createError: "",
    categoryError: "",
    tagError: "",
    classificationError: "",
    restrictedUserError: "",
    visibilityError: "",
    searchQuery: "",
    searchSuggestions: null,
    selectedMediaItem: mediaItem,
    selectedCategoryId: null,
    selectedRestrictedUserId: null,
    selectedTagId: null,
    restrictedUsers: [],
    onLogout: async () => {},
    onCreateCategory: async () => {},
    onCreateRestrictedUser: async () => {},
    onCreateTag: async () => {},
    onDeleteCategory: async () => {},
    onDeleteMediaItem: async () => {},
    onDeleteRestrictedUser: async () => {},
    onDeleteTag: async () => {},
    onSelectMediaItem: () => {},
    onSelectCategory: () => {},
    onSelectRestrictedUser: () => {},
    onSelectTag: () => {},
    onChangeSearchQuery: () => {},
    onUploadMediaItem: async () => {},
    onCreateExternalMediaItem: async () => {},
    onUpdateCategory: async () => {},
    onUpdateMediaItem: async () => {},
    onUpdateMediaItemAssignments: async () => {},
    onUpdateTag: async () => {},
    onSaveVisibility: async () => {},
    onPersistProgress: async () => {},
  };
}

describe("Dashboard layout", () => {
  it("renders search above a sidebar/main workspace layout", () => {
    const markup = renderToStaticMarkup(<Dashboard {...buildDashboardProps()} />);

    expect(markup).toContain("dashboard-search-row");
    expect(markup).toContain("dashboard-workspace");
    expect(markup).toContain("dashboard-sidebar");
    expect(markup).toContain("dashboard-main");
  });
});

describe("Transcript panel", () => {
  it("renders a dedicated transcript scroll area", () => {
    const markup = renderToStaticMarkup(<TranscriptPanel mediaItem={buildMediaItem()} />);

    expect(markup).toContain("transcript-scroll-area");
  });
});
