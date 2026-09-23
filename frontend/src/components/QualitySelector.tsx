import React, { useState } from 'react';
import { VideoInfo } from '../types';
import { Video, Music, Download, Check, Sparkles } from 'lucide-react';

interface QualitySelectorProps {
  info: VideoInfo;
  onDownload: (formatType: 'video' | 'audio', quality: string) => void;
  isStarting: boolean;
}

export const QualitySelector: React.FC<QualitySelectorProps> = ({ info, onDownload, isStarting }) => {
  const [tab, setTab] = useState<'video' | 'audio'>('video');
  const [selectedQuality, setSelectedQuality] = useState<string>(
    info.available_resolutions[0]?.height.toString() || '1080'
  );

  const handleTabChange = (newTab: 'video' | 'audio') => {
    setTab(newTab);
    if (newTab === 'video') {
      setSelectedQuality(info.available_resolutions[0]?.height.toString() || '1080');
    } else {
      setSelectedQuality('320k');
    }
  };

  const handleStart = () => {
    onDownload(tab, selectedQuality);
  };

  return (
    <div className="glass-panel rounded-2xl p-4 sm:p-6 mt-4">
      {/* Format Type Selector Tabs */}
      <div className="flex items-center justify-between pb-4 border-b border-slate-800/80 mb-5">
        <h3 className="text-base sm:text-lg font-bold text-white flex items-center gap-2">
          <span>Choose Format & Quality</span>
        </h3>

        <div className="flex bg-slate-900/90 p-1 rounded-xl border border-slate-800">
          <button
            onClick={() => handleTabChange('video')}
            className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition ${
              tab === 'video'
                ? 'bg-rose-600 text-white shadow-md shadow-rose-600/30'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Video className="w-3.5 h-3.5" />
            <span>Video (MP4)</span>
          </button>
          <button
            onClick={() => handleTabChange('audio')}
            className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition ${
              tab === 'audio'
                ? 'bg-rose-600 text-white shadow-md shadow-rose-600/30'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Music className="w-3.5 h-3.5" />
            <span>Audio (MP3)</span>
          </button>
        </div>
      </div>

      {/* Grid of Qualities */}
      {tab === 'video' ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {info.available_resolutions.map((res) => {
            const isSelected = selectedQuality === res.height.toString();
            return (
              <button
                key={res.height}
                onClick={() => setSelectedQuality(res.height.toString())}
                className={`relative flex flex-col p-3.5 rounded-xl border text-left transition-all ${
                  isSelected
                    ? 'border-rose-500 bg-rose-500/10 shadow-lg shadow-rose-500/10'
                    : 'border-slate-800 bg-slate-900/50 hover:bg-slate-800/60 hover:border-slate-700'
                }`}
              >
                <div className="flex items-center justify-between w-full mb-1">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-sm sm:text-base text-white">
                      {res.format_note}
                    </span>
                    {res.height === 2160 && (
                      <span className="inline-flex items-center gap-1 text-[10px] font-bold px-1.5 py-0.5 rounded bg-purple-500/20 text-purple-300 border border-purple-500/30">
                        <Sparkles className="w-2.5 h-2.5" />
                        4K Ultra HD
                      </span>
                    )}
                    {res.height === 1440 && (
                      <span className="inline-flex items-center gap-1 text-[10px] font-bold px-1.5 py-0.5 rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                        <Sparkles className="w-2.5 h-2.5" />
                        2K QHD
                      </span>
                    )}
                    {res.height === 1080 && (
                      <span className="inline-flex items-center gap-1 text-[10px] font-bold px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30">
                        <Sparkles className="w-2.5 h-2.5" />
                        Full HD
                      </span>
                    )}
                    {res.height === 144 && (
                      <span className="inline-flex items-center gap-1 text-[10px] font-bold px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                        Data Saver
                      </span>
                    )}
                  </div>
                  {isSelected && (
                    <div className="w-5 h-5 rounded-full bg-rose-500 flex items-center justify-center text-white">
                      <Check className="w-3 h-3 stroke-[3]" />
                    </div>
                  )}
                </div>

                <div className="flex items-center justify-between text-xs text-slate-400 mt-1">
                  <span>MP4 Video + AAC Audio</span>
                  <span className="font-medium text-slate-300">
                    {res.filesize_est_formatted ? `~${res.filesize_est_formatted}` : 'Adaptive'}
                  </span>
                </div>
              </button>
            );
          })}
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {info.audio_formats.map((audio) => {
            const isSelected = selectedQuality === audio.quality.replace('bps', '');
            return (
              <button
                key={audio.quality}
                onClick={() => setSelectedQuality(audio.quality.replace('bps', ''))}
                className={`flex flex-col p-4 rounded-xl border text-left transition-all ${
                  isSelected
                    ? 'border-rose-500 bg-rose-500/10 shadow-lg shadow-rose-500/10'
                    : 'border-slate-800 bg-slate-900/50 hover:bg-slate-800/60 hover:border-slate-700'
                }`}
              >
                <div className="flex items-center justify-between w-full mb-1">
                  <span className="font-bold text-white text-base">MP3 {audio.quality}</span>
                  {isSelected && (
                    <div className="w-5 h-5 rounded-full bg-rose-500 flex items-center justify-center text-white">
                      <Check className="w-3 h-3 stroke-[3]" />
                    </div>
                  )}
                </div>
                <div className="flex items-center justify-between text-xs text-slate-400 mt-1">
                  <span>Standard Stereo</span>
                  <span className="font-medium text-slate-300">
                    {audio.filesize_est_formatted ? `~${audio.filesize_est_formatted}` : 'Optimized'}
                  </span>
                </div>
              </button>
            );
          })}
        </div>
      )}

      {/* Action CTA */}
      <div className="mt-6 flex flex-col sm:flex-row items-center justify-between gap-4 pt-4 border-t border-slate-800/80">
        <div className="text-xs text-slate-400">
          Target: <span className="text-white font-semibold">{tab === 'video' ? `${selectedQuality}p MP4 Video` : `${selectedQuality} MP3 Audio`}</span>
        </div>

        <button
          onClick={handleStart}
          disabled={isStarting}
          className="w-full sm:w-auto flex items-center justify-center gap-2 bg-gradient-to-r from-rose-600 via-rose-500 to-amber-500 hover:opacity-95 text-white font-bold text-sm sm:text-base px-8 py-3.5 rounded-xl shadow-xl shadow-rose-600/25 transition transform active:scale-95 disabled:opacity-50"
        >
          <Download className="w-5 h-5" />
          <span>{isStarting ? 'Preparing Task...' : 'Download Now'}</span>
        </button>
      </div>
    </div>
  );
};
