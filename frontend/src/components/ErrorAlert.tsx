import React from 'react';
import { AlertTriangle, X } from 'lucide-react';

interface ErrorAlertProps {
  message: string;
  onDismiss: () => void;
}

export const ErrorAlert: React.FC<ErrorAlertProps> = ({ message, onDismiss }) => {
  return (
    <div className="w-full max-w-3xl mx-auto mt-4 p-4 rounded-2xl bg-rose-950/40 border border-rose-500/30 text-rose-200 text-xs sm:text-sm flex items-start justify-between gap-3 shadow-lg shadow-rose-950/20 backdrop-blur-md animate-in fade-in slide-in-from-top-2 duration-300">
      <div className="flex items-start gap-3">
        <AlertTriangle className="w-5 h-5 text-rose-400 flex-shrink-0 mt-0.5" />
        <div>
          <h4 className="font-bold text-rose-100 text-sm">Download Encountered An Issue</h4>
          <p className="mt-0.5 text-rose-200/90 leading-relaxed">{message}</p>
        </div>
      </div>

      <button
        onClick={onDismiss}
        className="text-rose-400 hover:text-white p-1 rounded-lg hover:bg-rose-900/50 transition"
      >
        <X className="w-4 h-4" />
      </button>
    </div>
  );
};
