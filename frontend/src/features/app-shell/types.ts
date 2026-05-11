export type MediaAsset = {
  id: number;
  asset_url: string;
  filename: string;
  mime_type: string;
  storage_path: string;
  duration_seconds: number | null;
  width: number | null;
  height: number | null;
};

export type Category = {
  id: number;
  name: string;
  parent: number | null;
};

export type Tag = {
  id: number;
  name: string;
};

export type RestrictedUser = {
  id: number;
  username: string;
  email: string;
  is_active: boolean;
  role: string;
};

export type ExternalSource = {
  id: number;
  provider: string;
  source_url: string;
  external_id: string;
  title: string;
  author_name: string;
};

export type CategoryVisibilityAssignment = {
  id: number;
  user: number;
  category: number;
};

export type MediaItemVisibilityAssignment = {
  id: number;
  user: number;
  media_item: number;
};

export type SessionState = {
  is_authenticated: boolean;
  username: string;
  role: string;
};

export type MediaItem = {
  id: number;
  title: string;
  description: string;
  media_type: string;
  player_display_mode: string;
  owner: number;
  asset: number | null;
  asset_detail: MediaAsset | null;
  external_source: number | null;
  external_source_detail: ExternalSource | null;
  published_at: string | null;
  categories: number[];
  tags: number[];
};

export type PlaybackProgress = {
  id: number;
  media_item: number;
  status: string;
  position_seconds: number;
  progress_percent: string;
};

export type Transcript = {
  id: number;
  media_item: number;
  status: string;
  provider: string;
  language_code: string;
  content: string;
  markdown_content: string;
  error_message: string;
  generated_at: string | null;
};

export type TranscriptSegment = {
  id: number;
  transcript: number;
  sequence_number: number;
  start_seconds: string | null;
  end_seconds: string | null;
  content: string;
};

export type Summary = {
  id: number;
  media_item: number;
  transcript: number | null;
  status: string;
  kind: string;
  provider: string;
  content: string;
  markdown_content: string;
  error_message: string;
  generated_at: string | null;
};

export type SearchSuggestions = {
  categories: Category[];
  tags: Tag[];
  media_items: MediaItem[];
};
