
import React from 'react';

export const Header: React.FC = () => {
  return (
    <header className="p-4 bg-slate-900/50 backdrop-blur-sm sticky top-0 z-10">
      <div className="container mx-auto flex justify-between items-center">
        <h1 className="text-2xl font-bold text-slate-100 tracking-wider">
          AI Audio<span className="text-cyan-400">Book</span>
        </h1>
      </div>
    </header>
  );
};
