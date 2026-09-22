import React, { useState, useEffect } from 'react';
import { getBackendHost, setBackendHost } from '../services/api';
import { Server, CheckCircle2, AlertCircle, X, ExternalLink, Loader2 } from 'lucide-react';
import axios from 'axios';

interface ServerConfigModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSaved: () => void;
}

export const ServerConfigModal: React.FC<ServerConfigModalProps> = ({ isOpen, onClose, onSaved }) => {
  const [url, setUrl] = useState('');
  const [testStatus, setTestStatus] = useState<'idle' | 'testing' | 'success' | 'failed'>('idle');
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    if (isOpen) {
      setUrl(getBackendHost());
      setTestStatus('idle');
      setErrorMessage('');
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleTest = async () => {
    const target = url.trim().replace(/\/$/, '');
    if (!target) {
      setErrorMessage('Please enter a backend URL (e.g. https://your-app.onrender.com)');
      setTestStatus('failed');
      return;
    }

    setTestStatus('testing');
    setErrorMessage('');

    try {
      const res = await axios.get(`${target}/health`, { timeout: 8000 });
      if (res.data?.status === 'healthy') {
        setTestStatus('success');
      } else {
        setTestStatus('failed');
        setErrorMessage('Server reached but health check failed.');
      }
    } catch (err: any) {
      setTestStatus('failed');
      setErrorMessage(
        err.response?.data?.message || err.message || 'Could not reach server. Ensure the URL is live and supports CORS.'
      );
    }
  };

  const handleSave = () => {
    setBackendHost(url.trim());
    onSaved();
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-in fade-in duration-200">
      <div className="relative w-full max-w-md glass-panel rounded-2xl p-6 shadow-2xl border border-slate-700/60 overflow-hidden">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2 text-white font-bold text-base">
            <Server className="w-5 h-5 text-rose-500" />
            <span>Connect Cloud Backend</span>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <p className="text-xs text-slate-300 leading-relaxed mb-4">
          Enter your live Render or VPS backend URL. All download and FFmpeg operations will route through this instance.
        </p>

        <div className="space-y-3">
          <div>
            <label className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1.5">
              Backend API URL
            </label>
            <input
              type="text"
              value={url}
              onChange={(e) => {
                setUrl(e.target.value);
                setTestStatus('idle');
              }}
              placeholder="https://youtube-downloader-pro.onrender.com"
              className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3.5 py-2.5 text-xs text-white placeholder-slate-500 outline-none focus:border-rose-500 transition"
            />
          </div>

          {testStatus === 'success' && (
            <div className="flex items-center gap-2 text-xs text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 p-2.5 rounded-xl">
              <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
              <span>Backend connection successful! FFmpeg is ready.</span>
            </div>
          )}

          {testStatus === 'failed' && (
            <div className="flex items-start gap-2 text-xs text-rose-400 bg-rose-500/10 border border-rose-500/20 p-2.5 rounded-xl">
              <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
              <div className="leading-snug">{errorMessage}</div>
            </div>
          )}

          <div className="flex items-center justify-between pt-2">
            <button
              type="button"
              onClick={handleTest}
              disabled={testStatus === 'testing' || !url.trim()}
              className="flex items-center gap-1.5 text-xs text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 px-3 py-2 rounded-xl transition disabled:opacity-50"
            >
              {testStatus === 'testing' ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Pinging...</span>
                </>
              ) : (
                <>
                  <ExternalLink className="w-3.5 h-3.5" />
                  <span>Test Health</span>
                </>
              )}
            </button>

            <button
              type="button"
              onClick={handleSave}
              className="bg-rose-600 hover:bg-rose-500 text-white font-semibold text-xs px-5 py-2 rounded-xl shadow-lg shadow-rose-600/30 transition"
            >
              Save & Apply
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
