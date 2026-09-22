import React, { useState } from 'react';
import { Youtube, ShieldCheck, Zap, Server } from 'lucide-react';
import { ServerConfigModal } from './ServerConfigModal';
import { getBackendHost } from '../services/api';

export const Header: React.FC = () => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [host, setHost] = useState(getBackendHost());

  const refreshHost = () => {
    setHost(getBackendHost());
  };

  return (
    <>
      <header className="w-full border-b border-slate-800/80 bg-slate-950/60 backdrop-blur-xl sticky top-0 z-40">
        <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-rose-600 to-rose-500 flex items-center justify-center shadow-lg shadow-rose-600/30">
              <Youtube className="w-6 h-6 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-extrabold text-lg tracking-tight bg-gradient-to-r from-white via-slate-100 to-slate-400 bg-clip-text text-transparent">
                  YouTube Downloader Pro
                </span>
                <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/20">
                  1080p Muxer
                </span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3 text-xs text-slate-400">
            <button
              onClick={() => setIsModalOpen(true)}
              className="flex items-center gap-1.5 bg-slate-900/80 hover:bg-slate-800 border border-slate-700/80 px-3 py-1.5 rounded-lg text-slate-300 hover:text-white transition shadow-sm"
              title="Configure Backend API Server"
            >
              <Server className="w-3.5 h-3.5 text-rose-500" />
              <span>{host ? 'Cloud Server' : 'Backend API'}</span>
              <span className={`w-2 h-2 rounded-full ${host ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'}`} />
            </button>

            <div className="hidden sm:flex items-center gap-1.5 bg-slate-900/60 border border-slate-800 px-3 py-1.5 rounded-lg">
              <Zap className="w-3.5 h-3.5 text-amber-400" />
              <span>Lossless Muxing</span>
            </div>
            <div className="hidden sm:flex items-center gap-1.5 bg-slate-900/60 border border-slate-800 px-3 py-1.5 rounded-lg">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
              <span>Zero Data Stored</span>
            </div>
          </div>
        </div>
      </header>

      <ServerConfigModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSaved={refreshHost}
      />
    </>
  );
};
