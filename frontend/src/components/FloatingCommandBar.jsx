import React, { useState, useEffect, useRef } from 'react';
import { Mic, ArrowRight, Loader2 } from 'lucide-react';

const SUGGESTIONS = [
  "Show me jobs with > ₹15 LPA in Bengaluru or Pune...",
  "Python & AI/ML engineer roles with Remote work modality...",
  "Freshers with 0-2 yrs exp in FastAPI, React & PyTorch...",
  "Direct ATS openings at tech startups with disclosed CTC..."
];

export default function FloatingCommandBar({
  onLaunchPrompt,
  isRunning = false,
  initialPrompt = ''
}) {
  const [inputVal, setInputVal] = useState(initialPrompt || '');
  const [placeholderIndex, setPlaceholderIndex] = useState(0);
  const [isRippling, setIsRippling] = useState(false);
  const rippleTimerRef = useRef(null);

  // Rotate suggestion placeholders smoothly
  useEffect(() => {
    const timer = setInterval(() => {
      setPlaceholderIndex((prev) => (prev + 1) % SUGGESTIONS.length);
    }, 5000);
    return () => clearInterval(timer);
  }, []);

  // Cleanup ripple timer on unmount
  useEffect(() => {
    return () => {
      if (rippleTimerRef.current) clearTimeout(rippleTimerRef.current);
    };
  }, []);

  const triggerLaunch = () => {
    if (!inputVal.trim() || isRunning) return;

    // Trigger instant ripple micro-interaction
    setIsRippling(true);
    if (rippleTimerRef.current) clearTimeout(rippleTimerRef.current);
    rippleTimerRef.current = setTimeout(() => {
      setIsRippling(false);
    }, 450);

    onLaunchPrompt(inputVal.trim());
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    triggerLaunch();
  };

  const handleMicClick = () => {
    if (window.webkitSpeechRecognition || window.SpeechRecognition) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      const rec = new SpeechRecognition();
      rec.onresult = (ev) => {
        const text = ev.results[0][0].transcript;
        setInputVal(text);
      };
      rec.start();
    } else {
      setInputVal(SUGGESTIONS[placeholderIndex]);
    }
  };

  return (
    <div className="floating-command-bar-wrapper">
      <form
        className={`floating-command-bar ${isRunning ? 'is-executing' : ''}`}
        onSubmit={handleSubmit}
      >
        {/* Left Glowing 'E' Emblem */}
        <div className="command-emblem-pill" aria-hidden="true">
          <svg width="22" height="22" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <linearGradient id="cmdBrandGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#38bdf8" />
                <stop offset="100%" stopColor="#6366f1" />
              </linearGradient>
            </defs>
            <path
              d="M7 6H25C25.5 6 26 6.5 26 7V10C26 10.5 25.5 11 25 11H13V14H22C22.5 14 23 14.5 23 15V17C23 17.5 22.5 18 22 18H13V21H25C25.5 21 26 21.5 26 22V25C26 25.5 25.5 26 25 26H7C6.4 26 6 25.6 6 25V7C6 6.4 6.4 6 7 6Z"
              fill="url(#cmdBrandGrad)"
            />
          </svg>
        </div>

        {/* Center Input */}
        <input
          type="text"
          className="command-bar-input"
          placeholder={`Ask EDITH: '${SUGGESTIONS[placeholderIndex]}'`}
          value={inputVal}
          onChange={(e) => setInputVal(e.target.value)}
          disabled={isRunning}
          aria-label="Natural language job search query"
        />

        {/* Right Tools: Mic & Interactive Submit Button */}
        <div className="command-bar-actions">
          <button
            type="button"
            className="command-icon-btn mic-btn"
            onClick={handleMicClick}
            title="Dictate prompt via microphone"
            aria-label="Voice dictation"
          >
            <Mic size={16} />
          </button>

          <button
            type="submit"
            className={`command-submit-btn ${isRunning ? 'running pulse-progress' : ''} ${isRippling ? 'rippling' : ''}`}
            disabled={isRunning || !inputVal.trim()}
            title={isRunning ? 'Autonomous ingestion in progress...' : 'Execute search & scrape verified jobs'}
            aria-label={isRunning ? 'Scraping in progress' : 'Submit job query'}
          >
            {/* Ripple Wave Element */}
            {isRippling && <span className="btn-ripple-wave" aria-hidden="true" />}

            {isRunning ? (
              <Loader2 size={16} className="spin-animation" />
            ) : (
              <ArrowRight size={16} className="submit-arrow-icon" />
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
