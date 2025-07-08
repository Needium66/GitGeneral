
import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import { PlayIcon } from './icons/PlayIcon';
import { PauseIcon } from './icons/PauseIcon';
import { StopIcon } from './icons/StopIcon';

interface ResultDisplayProps {
  script: string;
}

interface Word {
  text: string;
  charIndex: number;
}

export const ResultDisplay: React.FC<ResultDisplayProps> = ({ script }) => {
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [currentWordIndex, setCurrentWordIndex] = useState(-1);
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);

  const words = useMemo<Word[]>(() => {
    let index = 0;
    return script.split(/(\s+)/).filter(w => w.length > 0).map(w => {
        const wordObj = { text: w, charIndex: index };
        index += w.length;
        return wordObj;
    });
  }, [script]);

  const cleanupSpeech = useCallback(() => {
    if (speechSynthesis.speaking) {
      speechSynthesis.cancel();
    }
    setIsSpeaking(false);
    setIsPaused(false);
    setCurrentWordIndex(-1);
  }, []);

  useEffect(() => {
    // Cleanup on component unmount
    return () => {
      cleanupSpeech();
    };
  }, [cleanupSpeech]);
  
  const handlePlay = useCallback(() => {
    if (isPaused && utteranceRef.current) {
      speechSynthesis.resume();
      setIsSpeaking(true);
      setIsPaused(false);
      return;
    }
    
    cleanupSpeech();

    const utterance = new SpeechSynthesisUtterance(script);
    utteranceRef.current = utterance;

    utterance.onboundary = (event) => {
      if (event.name === 'word') {
        const word = words.find(w => w.charIndex >= event.charIndex);
        if (word) {
            const index = words.indexOf(word);
            setCurrentWordIndex(index);
        }
      }
    };
    
    utterance.onend = () => {
      setIsSpeaking(false);
      setIsPaused(false);
      setCurrentWordIndex(-1);
      utteranceRef.current = null;
    };
    
    utterance.onerror = (event) => {
      console.error("SpeechSynthesis Error", event);
      setIsSpeaking(false);
      setIsPaused(false);
      setCurrentWordIndex(-1);
    };

    speechSynthesis.speak(utterance);
    setIsSpeaking(true);
    setIsPaused(false);
  }, [script, words, isPaused, cleanupSpeech]);

  const handlePause = useCallback(() => {
    if (speechSynthesis.speaking && !isPaused) {
      speechSynthesis.pause();
      setIsPaused(true);
      setIsSpeaking(false); // Visually, it's not progressing
    }
  }, [isPaused]);

  const handleStop = useCallback(() => {
    cleanupSpeech();
  }, [cleanupSpeech]);

  return (
    <div className="w-full max-w-4xl bg-slate-800/50 rounded-lg shadow-xl p-6 md:p-8 flex flex-col h-[80vh]">
      <div className="flex-shrink-0 mb-6">
        <h2 className="text-3xl font-bold text-slate-100 mb-2">Generated Audio Script</h2>
        <div className="flex items-center justify-center space-x-4 p-4 bg-slate-900 rounded-lg">
          <button
            onClick={isSpeaking ? handlePause : handlePlay}
            disabled={!isSpeaking && isPaused}
            className="p-3 bg-slate-700 rounded-full text-slate-200 hover:bg-cyan-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            aria-label={isSpeaking ? "Pause" : "Play"}
          >
            {isSpeaking && !isPaused ? <PauseIcon className="w-6 h-6"/> : <PlayIcon className="w-6 h-6"/>}
          </button>
          <button
            onClick={handleStop}
            disabled={!isSpeaking && !isPaused}
            className="p-3 bg-slate-700 rounded-full text-slate-200 hover:bg-red-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            aria-label="Stop"
          >
            <StopIcon className="w-6 h-6"/>
          </button>
        </div>
      </div>
      <div className="flex-grow bg-slate-900 p-4 sm:p-6 rounded-md overflow-y-auto text-left leading-relaxed text-lg text-slate-300 scrollbar-thin scrollbar-thumb-slate-600 scrollbar-track-slate-800">
        <p>
          {words.map((word, index) => (
            <span
              key={index}
              className={`transition-colors duration-200 ${
                index === currentWordIndex
                  ? 'bg-cyan-500/30 text-cyan-200 rounded-md'
                  : 'bg-transparent'
              }`}
            >
              {word.text}
            </span>
          ))}
        </p>
      </div>
    </div>
  );
};
