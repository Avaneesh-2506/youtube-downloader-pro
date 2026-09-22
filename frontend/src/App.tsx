import React, { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { UrlInput } from './components/UrlInput';
import { VideoPreview } from './components/VideoPreview';
import { QualitySelector } from './components/QualitySelector';
import { ProgressModal } from './components/ProgressModal';
import { HistoryList } from './components/HistoryList';
import { ErrorAlert } from './components/ErrorAlert';
import { VideoInfo, DownloadProgress, HistoryItem } from './types';
import { api } from './services/api';
import { Sparkles, CheckCircle2, Shield, Zap } from 'lucide-react';

export const App: React.FC = () => {
  const [videoInfo, setVideoInfo] = useState<VideoInfo | null>(null);
  const [isLoadingInfo, setIsLoadingInfo] = useState(false);
  const [isStartingDownload, setIsStartingDownload] = useState(false);
  const [downloadProgress, setDownloadProgress] = useState<DownloadProgress | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [history, setHistory] = useState<HistoryItem[]>(() => {
    try {
      const saved = localStorage.getItem('ytdl_history');
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });

  useEffect(() => {
    try {
      localStorage.setItem('ytdl_history', JSON.stringify(history));
    } catch (e) {
      console.warn('Failed to persist history:', e);
    }
  }, [history]);

  const handleFetchInfo = async (url: string) => {
    setIsLoadingInfo(true);
    setErrorMessage(null);
    setVideoInfo(null);
    try {
      const info = await api.fetchVideoInfo(url);
      setVideoInfo(info);
    } catch (err: any) {
      const msg =
        err.response?.data?.detail ||
        err.message ||
        'Could not fetch video information. Please ensure the link is public and valid.';
      setErrorMessage(msg);
    } finally {
      setIsLoadingInfo(false);
    }
  };

  const handleStartDownload = async (formatType: 'video' | 'audio', quality: string) => {
    if (!videoInfo) return;
    setIsStartingDownload(true);
    setErrorMessage(null);

    try {
      const { task_id } = await api.startDownload(videoInfo.url, formatType, quality);

      // Save to local history
      const newHistoryItem: HistoryItem = {
        id: task_id,
        videoId: videoInfo.id,
        title: videoInfo.title,
        thumbnail: videoInfo.thumbnail,
        author: videoInfo.author,
        format: formatType.toUpperCase(),
        quality: formatType === 'video' ? `${quality}p` : `${quality}`,
        timestamp: Date.now(),
      };
      setHistory((prev) => [newHistoryItem, ...prev.filter((i) => i.videoId !== videoInfo.id)].slice(0, 15));

      // Subscribe to real-time progress via Server-Sent Events (SSE)
      setDownloadProgress({
        task_id,
        stage: 'queued',
        progress: 0,
        message: 'Initializing stream pipeline...',
      });

      api.subscribeToProgress(
        task_id,
        (progressUpdate) => {
          setDownloadProgress((prev) => ({
            ...(prev || { task_id }),
            ...progressUpdate,
          }));
        },
        (errorStr) => {
          setDownloadProgress((prev) => (prev ? { ...prev, stage: 'failed', error: errorStr } : null));
        }
      );
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message || 'Failed to initialize download task.';
      setErrorMessage(msg);
    } finally {
      setIsStartingDownload(false);
    }
  };

  const handleClearHistory = () => {
    setHistory([]);
    try {
      localStorage.removeItem('ytdl_history');
    } catch {}
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#030712] text-slate-100">
      <Header />

      <main className="flex-1 max-w-5xl w-full mx-auto px-4 py-8 sm:py-12 flex flex-col gap-6">
        {/* Hero Title */}
        <div className="text-center max-w-2xl mx-auto mb-2 sm:mb-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs font-semibold mb-4">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Support for 1080p, 720p, 480p, 360p, 240p & Audio MP3</span>
          </div>
          <h1 className="text-3xl sm:text-5xl font-black tracking-tight text-white leading-tight">
            Download YouTube Media <br />
            <span className="bg-gradient-to-r from-rose-500 via-pink-500 to-amber-400 bg-clip-text text-transparent">
              Without Compromise
            </span>
          </h1>
          <p className="mt-3 text-slate-400 text-xs sm:text-sm leading-relaxed">
            High-speed lossless DASH audio/video stream muxing powered by modern FFmpeg and yt-dlp.
          </p>
        </div>

        {/* URL Input */}
        <UrlInput onSearch={handleFetchInfo} isLoading={isLoadingInfo} />

        {/* Error Notification */}
        {errorMessage && (
          <ErrorAlert message={errorMessage} onDismiss={() => setErrorMessage(null)} />
        )}

        {/* Video Card & Quality Selection */}
        {videoInfo && (
          <div className="animate-in fade-in slide-in-from-bottom-4 duration-300">
            <VideoPreview info={videoInfo} />
            <QualitySelector
              info={videoInfo}
              onDownload={handleStartDownload}
              isStarting={isStartingDownload}
            />
          </div>
        )}

        {/* Live Progress Modal */}
        <ProgressModal
          progress={downloadProgress}
          onClose={() => setDownloadProgress(null)}
        />

        {/* Recent History */}
        <HistoryList
          items={history}
          onSelect={handleFetchInfo}
          onClear={handleClearHistory}
        />

        {/* Key Architectural Highlights Banner */}
        <div className="mt-12 grid grid-cols-1 sm:grid-cols-3 gap-4 text-left pt-8 border-t border-slate-900">
          <div className="p-4 rounded-xl glass-panel border border-slate-800/60">
            <div className="w-8 h-8 rounded-lg bg-rose-500/10 text-rose-400 flex items-center justify-center mb-2.5">
              <Zap className="w-4 h-4" />
            </div>
            <h4 className="font-bold text-white text-sm">Adaptive DASH Muxing</h4>
            <p className="text-xs text-slate-400 mt-1 leading-relaxed">
              Merges separate video & audio streams with native FFmpeg for full 1080p with zero quality degradation.
            </p>
          </div>

          <div className="p-4 rounded-xl glass-panel border border-slate-800/60">
            <div className="w-8 h-8 rounded-lg bg-emerald-500/10 text-emerald-400 flex items-center justify-center mb-2.5">
              <CheckCircle2 className="w-4 h-4" />
            </div>
            <h4 className="font-bold text-white text-sm">Real-time SSE Progress</h4>
            <p className="text-xs text-slate-400 mt-1 leading-relaxed">
              Watch live download speeds and multi-stage rendering with precision status updates.
            </p>
          </div>

          <div className="p-4 rounded-xl glass-panel border border-slate-800/60">
            <div className="w-8 h-8 rounded-lg bg-indigo-500/10 text-indigo-400 flex items-center justify-center mb-2.5">
              <Shield className="w-4 h-4" />
            </div>
            <h4 className="font-bold text-white text-sm">Ephemeral Transient Storage</h4>
            <p className="text-xs text-slate-400 mt-1 leading-relaxed">
              Files are immediately unlinked post-stream; periodic janitors purge inactive temporary caches.
            </p>
          </div>
        </div>
      </main>

      <footer className="w-full border-t border-slate-900 py-6 text-center text-xs text-slate-400">
        <p>Built for personal and offline study use. Comply with all local copyright terms and conditions.</p>
      </footer>
    </div>
  );
};

export default App;
