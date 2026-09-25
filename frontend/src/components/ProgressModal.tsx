import React, { useState, useEffect } from 'react';
import { DownloadProgress } from '../types';
import { 
  Loader2, 
  CheckCircle2, 
  AlertCircle, 
  Download, 
  X, 
  Layers, 
  Cpu, 
  FolderDown, 
  FolderOpen, 
  Play 
} from 'lucide-react';
import confetti from 'canvas-confetti';

interface ProgressModalProps {
  progress: DownloadProgress | null;
  onClose: () => void;
}

const cleanText = (str?: string): string => {
  if (!str) return '';
  return str.replace(/\u001b\[[0-9;]*[a-zA-Z]/g, '').trim();
};

export const ProgressModal: React.FC<ProgressModalProps> = ({ progress, onClose }) => {
  const [savedPath, setSavedPath] = useState<string | null>(null);
  const [, setSavedFilename] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  if (!progress) return null;

  const isCompleted = progress.stage === 'completed';
  const isFailed = progress.stage === 'failed';

  useEffect(() => {
    // Reset state for new task
    setSavedPath(null);
    setSavedFilename(null);
    setIsSaving(false);
    setSaveError(null);
  }, [progress?.task_id]);

  useEffect(() => {
    if (isCompleted) {
      // Trigger festive celebration confetti
      confetti({
        particleCount: 80,
        spread: 70,
        origin: { y: 0.6 }
      });
    }
  }, [isCompleted]);

  const handleSaveToDownloads = async () => {
    if (!progress.task_id) return;
    setIsSaving(true);
    setSaveError(null);

    try {
      // 1. Check if running inside desktop app with pywebview API
      const pywebview = (window as any).pywebview;
      if (pywebview?.api?.save_to_downloads) {
        const res = await pywebview.api.save_to_downloads(progress.task_id);
        if (res?.success) {
          setSavedPath(res.path);
          setSavedFilename(res.filename);
          setIsSaving(false);
          return;
        } else if (res?.error) {
          setSaveError(res.error);
          setIsSaving(false);
          return;
        }
      }

      // 2. Call backend API endpoint
      const resp = await fetch('/api/v1/download/save-to-downloads', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task_id: progress.task_id }),
      });

      const data = await resp.json();
      if (data?.success) {
        setSavedPath(data.path);
        setSavedFilename(data.filename);
      } else {
        // Fallback for standalone browser: trigger standard browser download
        if (progress.file_url) {
          const link = document.createElement('a');
          link.href = progress.file_url;
          link.download = progress.filename || 'video.mp4';
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
        } else {
          setSaveError(data?.detail || data?.error || 'Failed to save file.');
        }
      }
    } catch (err: any) {
      // Browser fallback on network error
      if (progress.file_url) {
        window.open(progress.file_url, '_blank');
      } else {
        setSaveError(err.message || 'Error saving file.');
      }
    } finally {
      setIsSaving(false);
    }
  };

  const handleSaveAs = async () => {
    if (!progress.task_id) return;
    setIsSaving(true);
    setSaveError(null);

    try {
      // 1. Check if running inside desktop app with pywebview API
      const pywebview = (window as any).pywebview;
      if (pywebview?.api?.save_file_as) {
        const res = await pywebview.api.save_file_as(progress.task_id);
        if (res?.success) {
          setSavedPath(res.path);
          setSavedFilename(res.filename);
        } else if (res?.error) {
          setSaveError(res.error);
        }
        // If cancelled, do nothing
        return;
      }

      // 2. In browser fallback: trigger standard browser download
      if (progress.file_url) {
        const link = document.createElement('a');
        link.href = progress.file_url;
        link.download = progress.filename || 'video.mp4';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      }
    } catch (err: any) {
      setSaveError(err.message || 'Error selecting save location.');
    } finally {
      setIsSaving(false);
    }
  };

  const handleOpenFolder = async () => {
    if (!savedPath) return;
    try {
      const pywebview = (window as any).pywebview;
      if (pywebview?.api?.open_folder) {
        await pywebview.api.open_folder(savedPath);
        return;
      }

      await fetch('/api/v1/download/open-folder', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: savedPath }),
      });
    } catch (err) {
      console.error('Failed to open folder:', err);
    }
  };

  const handleOpenFile = async () => {
    if (!savedPath) return;
    try {
      const pywebview = (window as any).pywebview;
      if (pywebview?.api?.open_file) {
        await pywebview.api.open_file(savedPath);
        return;
      }

      await fetch('/api/v1/download/open-file', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: savedPath }),
      });
    } catch (err) {
      console.error('Failed to open file:', err);
    }
  };

  const getStageLabel = () => {
    switch (progress.stage) {
      case 'queued':
        return 'Queued in processing pipeline...';
      case 'analyzing':
        return 'Analyzing stream manifest & resolving cipher...';
      case 'downloading_video':
        return 'Downloading HD video stream...';
      case 'downloading_audio':
        return 'Downloading high-bitrate audio stream...';
      case 'muxing':
        return 'Lossless FFmpeg stream muxing...';
      case 'converting':
        return 'Extracting and encoding MP3 audio...';
      case 'completed':
        return progress.filename || 'Download Complete!';
      case 'failed':
        return 'Process Failed';
      default:
        return 'Processing...';
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-in fade-in duration-200">
      <div className="relative w-full max-w-lg glass-panel rounded-2xl p-6 sm:p-8 shadow-2xl border border-slate-700/60 overflow-hidden">
        {/* Glow Header Accent */}
        <div className="absolute top-0 left-0 right-0 h-1.5 bg-gradient-to-r from-rose-500 via-pink-500 to-amber-500" />

        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-2.5 min-w-0">
            {isCompleted ? (
              <div className="w-9 h-9 shrink-0 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center">
                <CheckCircle2 className="w-5 h-5" />
              </div>
            ) : isFailed ? (
              <div className="w-9 h-9 shrink-0 rounded-full bg-rose-500/20 text-rose-400 flex items-center justify-center">
                <AlertCircle className="w-5 h-5" />
              </div>
            ) : (
              <div className="w-9 h-9 shrink-0 rounded-full bg-rose-500/20 text-rose-400 flex items-center justify-center">
                <Loader2 className="w-5 h-5 animate-spin" />
              </div>
            )}

            <div className="min-w-0">
              <h3 className="font-bold text-white text-base sm:text-lg">
                {isCompleted ? 'File Ready!' : isFailed ? 'Download Failed' : 'Processing Media'}
              </h3>
              <p className="text-xs text-slate-400 truncate max-w-[260px] sm:max-w-[340px]">
                {getStageLabel()}
              </p>
            </div>
          </div>

          {(isCompleted || isFailed) && (
            <button
              onClick={onClose}
              className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition cursor-pointer"
            >
              <X className="w-5 h-5" />
            </button>
          )}
        </div>

        {/* Progress Bar Section */}
        {!isFailed && (
          <div className="mt-4 mb-6">
            <div className="flex items-center justify-between text-xs text-slate-300 font-medium mb-2">
              <span className="flex items-center gap-1.5">
                {progress.stage === 'muxing' ? (
                  <Cpu className="w-3.5 h-3.5 text-amber-400 animate-pulse" />
                ) : (
                  <Layers className="w-3.5 h-3.5 text-rose-400" />
                )}
                <span>{progress.message || (isCompleted ? 'Processing complete' : getStageLabel())}</span>
              </span>
              <span className="font-bold text-white font-mono">{progress.progress}%</span>
            </div>

            <div className="w-full h-3 bg-slate-900 rounded-full overflow-hidden p-0.5 border border-slate-800">
              <div
                className="h-full bg-gradient-to-r from-rose-600 via-pink-600 to-amber-500 rounded-full transition-all duration-300 ease-out"
                style={{ width: `${Math.max(5, progress.progress)}%` }}
              />
            </div>

            {/* Metrics (Speed & ETA) */}
            {(progress.speed || progress.eta) && !isCompleted && (
              <div className="flex items-center justify-between mt-2.5 text-[11px] text-slate-400">
                <span>Speed: <strong className="text-slate-200">{cleanText(progress.speed) || 'Calculating'}</strong></span>
                <span>ETA: <strong className="text-slate-200">{cleanText(progress.eta) || 'Calculating'}</strong></span>
              </div>
            )}
          </div>
        )}

        {/* Error Details */}
        {isFailed && (
          <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs my-4 leading-relaxed">
            {progress.error || 'An unexpected error occurred during extraction or muxing.'}
          </div>
        )}

        {/* Completed Actions: Unsaved State */}
        {isCompleted && !savedPath && (
          <div className="mt-6 flex flex-col gap-2.5">
            {/* Primary: Quick Save to Downloads */}
            <button
              onClick={handleSaveToDownloads}
              disabled={isSaving}
              className="w-full flex items-center justify-center gap-2 bg-gradient-to-r from-emerald-600 to-teal-500 hover:from-emerald-500 hover:to-teal-400 text-white font-bold py-3.5 px-4 rounded-xl shadow-lg shadow-emerald-600/30 transition text-sm disabled:opacity-50 cursor-pointer"
            >
              {isSaving ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Download className="w-4 h-4" />
              )}
              <span>{isSaving ? 'Saving File...' : 'Save to Downloads'}</span>
            </button>

            {/* Secondary: Choose Where to Save (Save As...) */}
            <button
              onClick={handleSaveAs}
              disabled={isSaving}
              className="w-full flex items-center justify-center gap-2 bg-slate-800/90 hover:bg-slate-700 border border-slate-700 hover:border-slate-600 text-slate-200 font-medium py-2.5 px-4 rounded-xl transition text-xs disabled:opacity-50 cursor-pointer"
            >
              <FolderDown className="w-4 h-4 text-emerald-400" />
              <span>Choose Where to Save (Save As...)</span>
            </button>

            {saveError && (
              <div className="p-2.5 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs text-center mt-1">
                {saveError}
              </div>
            )}

            <button
              onClick={onClose}
              className="w-full py-2.5 text-xs text-slate-400 hover:text-white transition rounded-lg hover:bg-slate-800/50 mt-1 cursor-pointer"
            >
              Close and download another video
            </button>
          </div>
        )}

        {/* Completed Actions: Saved State */}
        {isCompleted && savedPath && (
          <div className="mt-6 flex flex-col gap-3">
            <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/25 text-emerald-300 text-xs">
              <div className="flex items-center gap-2 font-semibold text-emerald-400 mb-1.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span>File Saved Successfully!</span>
              </div>
              <p className="text-slate-300 text-[11px] font-mono break-all line-clamp-2 bg-slate-900/60 p-2 rounded-lg border border-slate-800 select-all">
                {savedPath}
              </p>
            </div>

            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={handleOpenFolder}
                className="flex items-center justify-center gap-1.5 py-2.5 px-3 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 text-xs font-semibold rounded-xl transition cursor-pointer"
              >
                <FolderOpen className="w-3.5 h-3.5 text-teal-400" />
                <span>Open in Folder</span>
              </button>

              <button
                onClick={handleOpenFile}
                className="flex items-center justify-center gap-1.5 py-2.5 px-3 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold rounded-xl shadow-md shadow-emerald-600/20 transition cursor-pointer"
              >
                <Play className="w-3.5 h-3.5 text-white fill-white" />
                <span>Play File</span>
              </button>
            </div>

            <button
              onClick={onClose}
              className="w-full py-2.5 text-xs text-slate-400 hover:text-white transition rounded-lg hover:bg-slate-800/50 mt-1 cursor-pointer"
            >
              Close and download another video
            </button>
          </div>
        )}

        {isFailed && (
          <div className="mt-4 flex justify-end">
            <button
              onClick={onClose}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold rounded-xl transition cursor-pointer"
            >
              Dismiss
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
