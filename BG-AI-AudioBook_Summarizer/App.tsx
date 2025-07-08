
import React, { useState, useCallback } from 'react';
import { Header } from './components/Header';
import { Loader } from './components/Loader';
import { ResultDisplay } from './components/ResultDisplay';
import { generateBookSummary } from './services/geminiService';
import { BookOpenIcon } from './components/icons/BookOpenIcon';

const App: React.FC = () => {
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [script, setScript] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleGenerate = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    setScript(null);

    try {
      const summary = await generateBookSummary();
      setScript(summary);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(`Failed to generate summary: ${err.message}`);
      } else {
        setError("An unknown error occurred.");
      }
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  return (
    <div className="min-h-screen bg-slate-900 text-slate-200 font-sans flex flex-col">
      <Header />
      <main className="flex-grow flex flex-col items-center justify-center p-4 sm:p-6 md:p-8 text-center">
        {isLoading ? (
          <Loader />
        ) : error ? (
          <div className="bg-red-900/50 border border-red-700 text-red-300 p-4 rounded-lg max-w-2xl">
            <h2 className="font-bold text-lg mb-2">An Error Occurred</h2>
            <p>{error}</p>
            <button
              onClick={handleGenerate}
              className="mt-4 px-4 py-2 bg-slate-600 hover:bg-slate-500 rounded-md transition-colors"
            >
              Try Again
            </button>
          </div>
        ) : script ? (
          <ResultDisplay script={script} />
        ) : (
          <div className="max-w-3xl mx-auto">
            <div className="flex justify-center items-center mb-6">
              <BookOpenIcon className="h-24 w-24 text-cyan-400" />
            </div>
            <h1 className="text-4xl sm:text-5xl md:text-6xl font-bold text-slate-100 mb-4 tracking-tight">
              Bill Gates: <span className="text-cyan-400">Source Code</span>
            </h1>
            <p className="text-lg sm:text-xl text-slate-400 mb-8 max-w-2xl mx-auto">
              Generate a 10-minute audio summary of Bill Gates' memoir, brought to life by AI.
            </p>
            <button
              onClick={handleGenerate}
              className="bg-cyan-600 hover:bg-cyan-500 text-white font-bold py-3 px-8 rounded-full text-lg transition-all duration-300 transform hover:scale-105 shadow-lg shadow-cyan-900/50"
            >
              Generate Audio Summary
            </button>
          </div>
        )}
      </main>
      <footer className="text-center p-4 text-slate-500 text-sm">
        <p>Powered by Gemini API and Web Speech Synthesis</p>
      </footer>
    </div>
  );
};

export default App;
