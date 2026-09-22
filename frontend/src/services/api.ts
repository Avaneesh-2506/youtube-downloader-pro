import axios from 'axios';
import { VideoInfo, DownloadProgress } from '../types';

export const getBackendHost = (): string => {
  const saved = localStorage.getItem('ytdl_backend_url');
  if (saved) return saved.trim().replace(/\/$/, '');
  return (import.meta.env.VITE_API_BASE_URL || '').trim().replace(/\/$/, '');
};

export const setBackendHost = (url: string) => {
  if (url.trim()) {
    localStorage.setItem('ytdl_backend_url', url.trim().replace(/\/$/, ''));
  } else {
    localStorage.removeItem('ytdl_backend_url');
  }
};

export const getApiBase = (): string => {
  const host = getBackendHost();
  return host ? `${host}/api/v1` : '/api/v1';
};

export const api = {
  async fetchVideoInfo(url: string): Promise<VideoInfo> {
    const response = await axios.post<VideoInfo>(`${getApiBase()}/info`, { url });
    return response.data;
  },

  async startDownload(url: string, format_type: 'video' | 'audio', quality: string): Promise<{ task_id: string }> {
    const response = await axios.post<{ task_id: string }>(`${getApiBase()}/download/start`, {
      url,
      format_type,
      quality,
      ext: format_type === 'audio' ? 'mp3' : 'mp4'
    });
    return response.data;
  },

  subscribeToProgress(
    taskId: string,
    onProgress: (data: DownloadProgress) => void,
    onError: (error: string) => void
  ): () => void {
    const eventSource = new EventSource(`${getApiBase()}/download/progress/${taskId}`);

    eventSource.onmessage = (event) => {
      try {
        const data: DownloadProgress = JSON.parse(event.data);
        onProgress(data);
        if (data.stage === 'completed' || data.stage === 'failed') {
          eventSource.close();
        }
      } catch (err) {
        console.error('Failed to parse SSE payload:', err);
      }
    };

    eventSource.addEventListener('progress', (event: any) => {
      try {
        const data: DownloadProgress = JSON.parse(event.data);
        onProgress(data);
      } catch (err) {
        console.error('Failed to parse SSE progress event:', err);
      }
    });

    eventSource.addEventListener('complete', (event: any) => {
      try {
        const data: DownloadProgress = JSON.parse(event.data);
        onProgress(data);
        eventSource.close();
      } catch (err) {
        console.error('Failed to parse SSE complete event:', err);
      }
    });

    eventSource.onerror = () => {
      onError('Lost connection to download progress stream.');
      eventSource.close();
    };

    return () => {
      eventSource.close();
    };
  },

  getFileUrl(taskId: string): string {
    return `${getApiBase()}/download/file/${taskId}`;
  }
};
