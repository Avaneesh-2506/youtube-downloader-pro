import axios from 'axios';
import { VideoInfo, DownloadProgress } from '../types';

const API_BASE = '/api/v1';

export const api = {
  async fetchVideoInfo(url: string): Promise<VideoInfo> {
    const response = await axios.post<VideoInfo>(`${API_BASE}/info`, { url });
    return response.data;
  },

  async startDownload(url: string, format_type: 'video' | 'audio', quality: string): Promise<{ task_id: string }> {
    const response = await axios.post<{ task_id: string }>(`${API_BASE}/download/start`, {
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
    const eventSource = new EventSource(`${API_BASE}/download/progress/${taskId}`);

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
    return `${API_BASE}/download/file/${taskId}`;
  }
};
