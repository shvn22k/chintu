'use client';

import { useState } from 'react';
import Sidebar from '@/components/Sidebar';
import ChatArea from '@/components/ChatArea';
import InputBar from '@/components/InputBar';
import { ChatMessage, BackendResponse } from '@/types';

const SUGGESTIONS = [
  { label: 'Causal explosion', prompt: 'Show the causal explosion for recent US–China trade events' },
  { label: 'Entity impact', prompt: 'What is the entity impact of the United States?' },
  { label: 'Topic timeline', prompt: 'Show me the topic timeline for Indo-Pacific security' },
  { label: 'Causal chain', prompt: 'Trace the causal chain from the Russian gas pipeline shutdown' },
];

function RadialSymbol() {
  const lines = 8;
  return (
    <svg width="64" height="64" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="32" cy="32" r="3" fill="#c87c5a" />
      {Array.from({ length: lines }).map((_, i) => {
        const angle = (i * 360) / lines;
        const rad = (angle * Math.PI) / 180;
        const x1 = 32 + Math.cos(rad) * 8;
        const y1 = 32 + Math.sin(rad) * 8;
        const x2 = 32 + Math.cos(rad) * 24;
        const y2 = 32 + Math.sin(rad) * 24;
        return (
          <line
            key={i}
            x1={x1}
            y1={y1}
            x2={x2}
            y2={y2}
            stroke="#c87c5a"
            strokeWidth="1.5"
            strokeLinecap="round"
          />
        );
      })}
    </svg>
  );
}

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isThinking, setIsThinking] = useState(false);
  const [chatActive, setChatActive] = useState(false);

  const handleSend = async () => {
    const text = inputValue.trim();
    if (!text || isThinking) return;

    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: text,
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputValue('');
    setChatActive(true);
    setIsThinking(true);

    try {
      const res = await fetch('/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text }),
      });

      const data: BackendResponse = await res.json();

      const assistantMsg: ChatMessage = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: data.text || 'Analysis complete.',
        response: data,
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch {
      const errorMsg: ChatMessage = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: 'Failed to reach the analysis engine. Please try again.',
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsThinking(false);
    }
  };

  const handleNewAnalysis = () => {
    setMessages([]);
    setInputValue('');
    setChatActive(false);
    setIsThinking(false);
  };

  const handleSuggestionClick = (prompt: string) => {
    setInputValue(prompt);
  };

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar onNewAnalysis={handleNewAnalysis} />

      {/* Main column */}
      <div className="flex flex-col flex-1 ml-[220px] h-screen">
        {/* Welcome or Chat */}
        {!chatActive ? (
          <div className="flex-1 flex items-center justify-center">
            <div className="flex flex-col items-center max-w-[520px] px-6">
              <RadialSymbol />
              <h1 className="mt-6 text-2xl font-sora text-text font-light">
                What&apos;s happening <span className="font-semibold">today?</span>
              </h1>
              <p className="mt-3 text-sm font-jetbrains text-muted text-center leading-relaxed">
                Ask about geopolitical events, causal chains, entity relationships, or topic
                timelines.
              </p>
              <div className="flex flex-wrap justify-center gap-2 mt-6">
                {SUGGESTIONS.map((s) => (
                  <button
                    key={s.label}
                    onClick={() => handleSuggestionClick(s.prompt)}
                    className="px-3.5 py-1.5 rounded-full border border-border2 text-sm font-sora text-muted hover:text-text hover:border-border2 hover:bg-bg3 transition-colors duration-150"
                  >
                    {s.label}
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <ChatArea messages={messages} isThinking={isThinking} />
        )}

        {/* Input bar (always visible) */}
        <InputBar
          value={inputValue}
          onChange={setInputValue}
          onSend={handleSend}
          disabled={isThinking}
        />
      </div>
    </div>
  );
}
