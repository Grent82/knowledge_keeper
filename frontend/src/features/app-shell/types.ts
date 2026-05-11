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

export type SearchSuggestions = {
  categories: Category[];
  tags: Tag[];
  media_items: MediaItem[];
};
