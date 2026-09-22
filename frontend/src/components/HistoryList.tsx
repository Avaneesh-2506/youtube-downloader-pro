import React from 'react';
import { HistoryItem } from '../types';
import { History, Trash2, ArrowUpRight } from 'lucide-react';

interface HistoryListProps {
  items: HistoryItem[];
  onSelect: (videoId: string) => void;
  onClear: () => void;
}

export const HistoryList: React.FC<HistoryListProps> = ({ items, onSelect, onClear }) => {
  if (items.length === 0) return null;

  return (
    <div className="glass-panel rounded-2xl p-4 sm:p-6 mt-8 max-w-4xl mx-auto">
      <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-4">
        <div className="flex items-center gap-2">
          <History className="w-4 h-4 text-rose-500" />
          <h3 className="font-bold text-sm sm:text-base text-white">Recent Downloads</h3>
          <span className="text-xs text-slate-500 font-medium">({items.length})</span>
        </div>

        <button
          onClick={onClear}
          className="flex items-center gap-1 text-xs text-slate-400 hover:text-rose-400 transition"
        >
          <Trash2 className="w-3.5 h-3.5" />
          <span>Clear</span>
        </button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {items.slice(0, 6).map((item) => (
          <div
            key={item.id}
            onClick={() => onSelect(`https://www.youtube.com/watch?v=${item.videoId}`)}
            className="flex items-center gap-3 p-2.5 rounded-xl border border-slate-800/80 bg-slate-900/40 hover:bg-slate-800/60 hover:border-slate-700 transition cursor-pointer group"
          >
            <img
              src={item.thumbnail}
              alt={item.title}
              className="w-16 h-10 object-cover rounded-lg flex-shrink-0 bg-slate-950"
            />
            <div className="flex-1 min-w-0">
              <p className="text-xs font-semibold text-white truncate group-hover:text-rose-400 transition-colors">
                {item.title}
              </p>
              <div className="flex items-center gap-2 text-[11px] text-slate-400 mt-0.5">
                <span className="uppercase text-[10px] font-bold px-1.5 py-0.2 rounded bg-slate-800 text-slate-300">
                  {item.quality} {item.format}
                </span>
                <span>{item.author}</span>
              </div>
            </div>
            <ArrowUpRight className="w-4 h-4 text-slate-500 group-hover:text-white transition-colors" />
          </div>
        ))}
      </div>
    </div>
  );
};
