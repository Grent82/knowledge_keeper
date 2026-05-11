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
};

export type PlaybackProgress = {
  id: number;
  media_item: number;
  status: string;
  position_seconds: number;
  progress_percent: string;
};
