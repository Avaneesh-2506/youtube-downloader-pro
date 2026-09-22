import React from 'react';
import { VideoInfo } from '../types';
import { Clock, Eye, User, Film } from 'lucide-react';

interface VideoPreviewProps {
  info: VideoInfo;
}

export const VideoPreview: React.FC<VideoPreviewProps> = ({ info }) => {
  return (
    <div className="glass-panel rounded-2xl p-4 sm:p-5 flex flex-col md:flex-row gap-5 items-start">
      <div className="relative w-full md:w-80 flex-shrink-0 aspect-video rounded-xl overflow-hidden shadow-lg border border-slate-700/50 bg-slate-900 group">
        <img
          src={info.thumbnail}
          alt={info.title}
          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
          onError={(e) => {
            // fallback if maxresdefault fails
            (e.target as HTMLImageElement).src = `https://i.ytimg.com/vi/${info.id}/hqdefault.jpg`;
          }}
        />
        <div className="absolute bottom-2.5 right-2.5 bg-black/85 backdrop-blur-md px-2 py-0.5 rounded-md text-xs font-semibold text-white flex items-center gap-1 shadow">
          <Clock className="w-3 h-3 text-rose-400" />
          <span>{info.duration_formatted}</span>
        </div>
      </div>

      <div className="flex-1 flex flex-col justify-between self-stretch">
        <div>
          <h2 className="text-lg sm:text-xl font-bold text-white line-clamp-2 leading-snug mb-2">
            {info.title}
          </h2>

          <div className="flex flex-wrap items-center gap-4 text-xs sm:text-sm text-slate-400">
            <div className="flex items-center gap-1.5 font-medium text-slate-300">
              <User className="w-4 h-4 text-rose-400" />
              <span>{info.author}</span>
            </div>
            {info.views_formatted && (
              <div className="flex items-center gap-1.5">
                <Eye className="w-4 h-4 text-slate-500" />
                <span>{info.views_formatted}</span>
              </div>
            )}
            <div className="flex items-center gap-1.5 text-emerald-400 font-medium">
              <Film className="w-4 h-4" />
              <span>Up to {info.available_resolutions[0]?.height || 1080}p Available</span>
            </div>
          </div>
        </div>

        <div className="mt-4 pt-4 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
          <span>Target ID: <code className="text-slate-300 font-mono">{info.id}</code></span>
          <span className="text-slate-500">Audio-Video DASH stream muxing enabled</span>
        </div>
      </div>
    </div>
  );
};
