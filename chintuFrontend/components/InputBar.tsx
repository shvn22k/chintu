'use client';

import { useRef, useEffect, KeyboardEvent, ChangeEvent } from 'react';

interface InputBarProps {
  value: string;
  onChange: (value: string) => void;
  onSend: () => void;
  disabled?: boolean;
}

export default function InputBar({ value, onChange, onSend, disabled }: InputBarProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const ta = textareaRef.current;
    if (ta) {
      ta.style.height = 'auto';
      ta.style.height = Math.min(ta.scrollHeight, 200) + 'px';
    }
  }, [value]);

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (value.trim() && !disabled) {
        onSend();
      }
    }
  };

  const handleChange = (e: ChangeEvent<HTMLTextAreaElement>) => {
    onChange(e.target.value);
  };

  return (
    <div className="px-4 pb-3 pt-2">
      <div className="rounded-xl border border-border2 bg-bg2 focus-within:border-[rgba(200,124,90,0.35)] transition-colors duration-150">
        <textarea
          ref={textareaRef}
          value={value}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          placeholder="Ask about geopolitical events..."
          rows={1}
          className="w-full bg-transparent text-text text-sm font-sora px-4 pt-3 pb-1 placeholder:text-muted/60 leading-relaxed"
        />
        <div className="flex items-center justify-between px-4 pb-2.5">
          <span className="text-[11px] font-jetbrains text-muted">
            CHINTU · TigerGraph
          </span>
          <button
            onClick={() => { if (value.trim() && !disabled) onSend(); }}
            disabled={disabled || !value.trim()}
            className="w-7 h-7 rounded-lg flex items-center justify-center bg-accent/90 text-bg hover:bg-accent disabled:opacity-30 disabled:cursor-not-allowed transition-colors duration-150"
          >
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M7 12V2M7 2L3 6M7 2l4 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </button>
        </div>
      </div>
      <p className="text-center text-[11px] font-jetbrains text-muted/50 mt-2">
        Enter to send · CHINTU renders graph intelligence
      </p>
    </div>
  );
}
