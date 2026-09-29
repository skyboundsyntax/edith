import React, { useState } from 'react';
import { MessageSquare, ArrowRight, Loader2 } from 'lucide-react';

/**
 * Floating Command Bar
 * Matches the bottom frosted pill from the user's reference image:
 * Features "Consult EDITH... Type your question or role requirements here."
 * with a clean speech bubble / submit icon and the "SEP 29, 2026" timestamp.
 */
export default function FloatingCommandBar({
  onLaunchPrompt,
  isRunning = false,
  initialPrompt = ''
}) {
  const [inputVal, setInputVal] = useState(initialPrompt || '');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!inputVal.trim() || isRunning) return;
    onLaunchPrompt(inputVal.trim());
  };

  return (
    <div className="bottom-command-dock">
      <form className="floating-command-bar glass-panel-glow" onSubmit={handleSubmit}>
        <input
          type="text"
          className="command-bar-input"
          placeholder="Consult EDITH... Type your question or role requirements here."
          value={inputVal}
          onChange={(e) => setInputVal(e.target.value)}
          disabled={isRunning}
          aria-label="Ask EDITH"
        />

        <button
          type="submit"
          className="command-bubble-btn"
          disabled={isRunning}
          title={isRunning ? 'Executing ingestion...' : 'Send prompt to EDITH'}
          aria-label="Send prompt"
        >
          {isRunning ? (
            <Loader2 size={18} className="spin-animation" />
          ) : (
            <MessageSquare size={18} />
          )}
        </button>
      </form>

      <span className="bottom-command-date">SEP 29, 2026</span>
    </div>
  );
}
