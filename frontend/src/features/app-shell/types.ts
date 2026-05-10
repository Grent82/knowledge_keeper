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
};

export type PlaybackProgress = {
  id: number;
  media_item: number;
  status: string;
  position_seconds: number;
  progress_percent: string;
};
