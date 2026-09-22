import React, { useState } from 'react';
import { Search, Clipboard, ArrowRight, Loader2 } from 'lucide-react';

interface UrlInputProps {
  onSearch: (url: string) => void;
  isLoading: boolean;
}

export const UrlInput: React.FC<UrlInputProps> = ({ onSearch, isLoading }) => {
  const [inputUrl, setInputUrl] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputUrl.trim() && !isLoading) {
      onSearch(inputUrl.trim());
    }
  };

  const handlePaste = async () => {
    try {
      const text = await navigator.clipboard.readText();
      if (text) {
        setInputUrl(text);
        onSearch(text.trim());
      }
    } catch (err) {
      console.warn('Clipboard read failed:', err);
    }
  };

  return (
    <div className="w-full max-w-3xl mx-auto">
      <form onSubmit={handleSubmit} className="relative group">
        <div className="absolute -inset-1 bg-gradient-to-r from-rose-600 via-pink-600 to-amber-500 rounded-2xl blur-lg opacity-30 group-hover:opacity-60 transition duration-500"></div>
        <div className="relative flex items-center glass-input rounded-2xl shadow-2xl p-2 sm:p-2.5 focus-within:border-rose-500/80 transition-all duration-300">
          <div className="pl-3 sm:pl-4 pr-2 text-slate-400">
            <Search className="w-5 h-5 group-focus-within:text-rose-500 transition-colors" />
          </div>

          <input
            type="text"
            value={inputUrl}
            onChange={(e) => setInputUrl(e.target.value)}
            placeholder="Paste YouTube video or Shorts link here (e.g. https://youtu.be/...)"
            className="w-full bg-transparent text-sm sm:text-base text-white placeholder-slate-400/80 outline-none px-2 py-2"
            disabled={isLoading}
          />

          <div className="flex items-center gap-2 pr-1">
            <button
              type="button"
              onClick={handlePaste}
              title="Paste from clipboard"
              className="hidden sm:flex items-center gap-1 text-xs font-medium text-slate-400 hover:text-white bg-slate-800/80 hover:bg-slate-700/80 border border-slate-700/60 px-3 py-2 rounded-xl transition"
            >
              <Clipboard className="w-3.5 h-3.5" />
              <span>Paste</span>
            </button>

            <button
              type="submit"
              disabled={isLoading || !inputUrl.trim()}
              className="flex items-center gap-2 bg-gradient-to-r from-rose-600 to-rose-500 hover:from-rose-500 hover:to-rose-400 text-white font-semibold text-sm px-5 py-2.5 rounded-xl shadow-lg shadow-rose-600/30 disabled:opacity-50 disabled:cursor-not-allowed transition transform active:scale-95 whitespace-nowrap"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Fetching...</span>
                </>
              ) : (
                <>
                  <span>Fetch</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        </div>
      </form>
    </div>
  );
};
