
import React from 'react';

export const Loader: React.FC = () => {
  return (
    <div className="flex flex-col items-center justify-center space-y-4">
      <div className="w-16 h-16 border-4 border-t-4 border-slate-600 border-t-cyan-400 rounded-full animate-spin"></div>
      <p className="text-slate-300 text-lg font-medium">Generating audio summary with Gemini...</p>
      <p className="text-slate-400 text-sm">This may take a moment.</p>
    </div>
  );
};
