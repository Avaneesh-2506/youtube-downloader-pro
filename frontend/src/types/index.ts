export interface VideoResolution {
  height: number;
  format_note: string;
  fps?: number;
  ext: string;
  filesize_est?: number;
  filesize_est_formatted?: string;
  has_audio: boolean;
  requires_mux: boolean;
}

export interface AudioFormat {
  quality: string;
  ext: string;
  filesize_est?: number;
  filesize_est_formatted?: string;
}

export interface VideoInfo {
  id: string;
  url: string;
  title: string;
  author: string;
  thumbnail: string;
  duration_seconds: number;
  duration_formatted: string;
  views?: number;
  views_formatted?: string;
  available_resolutions: VideoResolution[];
  audio_formats: AudioFormat[];
}

export interface DownloadProgress {
  task_id: string;
  stage: 'queued' | 'analyzing' | 'downloading_video' | 'downloading_audio' | 'muxing' | 'converting' | 'completed' | 'failed';
  progress: number;
  speed?: string;
  eta?: string;
  downloaded_bytes?: number;
  total_bytes?: number;
  message?: string;
  file_url?: string;
  filename?: string;
  error?: string;
}

export interface HistoryItem {
  id: string;
  videoId: string;
  title: string;
  thumbnail: string;
  author: string;
  format: string;
  quality: string;
  timestamp: number;
}
