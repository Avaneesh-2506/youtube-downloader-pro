import React, { useEffect } from 'react';
import { DownloadProgress } from '../types';
import { Loader2, CheckCircle2, AlertCircle, Download, X, Layers, Cpu } from 'lucide-react';
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
  if (!progress) return null;

  const isCompleted = progress.stage === 'completed';
  const isFailed = progress.stage === 'failed';

  useEffect(() => {
    if (isCompleted) {
      // Trigger festive celebration confetti
      confetti({
        particleCount: 80,
        spread: 70,
        origin: { y: 0.6 }
      });

      // Automatically trigger file download
      if (progress.file_url) {
        const link = document.createElement('a');
        link.href = progress.file_url;
        link.setAttribute('download', '');
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      }
    }
  }, [isCompleted, progress?.file_url]);

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
        return 'Download Complete!';
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
          <div className="flex items-center gap-2.5">
            {isCompleted ? (
              <div className="w-9 h-9 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center">
                <CheckCircle2 className="w-5 h-5" />
              </div>
            ) : isFailed ? (
              <div className="w-9 h-9 rounded-full bg-rose-500/20 text-rose-400 flex items-center justify-center">
                <AlertCircle className="w-5 h-5" />
              </div>
            ) : (
              <div className="w-9 h-9 rounded-full bg-rose-500/20 text-rose-400 flex items-center justify-center">
                <Loader2 className="w-5 h-5 animate-spin" />
              </div>
            )}

            <div>
              <h3 className="font-bold text-white text-base sm:text-lg">
                {isCompleted ? 'File Ready!' : isFailed ? 'Download Failed' : 'Processing Media'}
              </h3>
              <p className="text-xs text-slate-400">{getStageLabel()}</p>
            </div>
          </div>

          {(isCompleted || isFailed) && (
            <button
              onClick={onClose}
              className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition"
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
                <span>{progress.message || getStageLabel()}</span>
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

        {/* Completed Actions */}
        {isCompleted && progress.file_url && (
          <div className="mt-6 flex flex-col gap-3">
            <a
              href={progress.file_url}
              download={progress.filename || 'download.mp4'}
              className="w-full flex items-center justify-center gap-2 bg-gradient-to-r from-emerald-600 to-teal-500 hover:from-emerald-500 hover:to-teal-400 text-white font-bold py-3 px-4 rounded-xl shadow-lg shadow-emerald-600/30 transition text-sm"
            >
              <Download className="w-4 h-4" />
              <span>Save {progress.filename ? `"${progress.filename.slice(0, 35)}..."` : 'File'}</span>
            </a>

            <button
              onClick={onClose}
              className="w-full py-2.5 text-xs text-slate-400 hover:text-white transition rounded-lg hover:bg-slate-800/50"
            >
              Close and download another video
            </button>
          </div>
        )}

        {isFailed && (
          <div className="mt-4 flex justify-end">
            <button
              onClick={onClose}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold rounded-xl transition"
            >
              Dismiss
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
