'use client';

import { useState } from 'react';
import Sidebar from '@/components/Sidebar';
import ChatArea from '@/components/ChatArea';
import InputBar from '@/components/InputBar';
import { ChatMessage, BackendResponse } from '@/types';

const SUGGESTIONS = [
  { label: 'Causal', prompt: 'What were the downstream effects after recent Iran diplomatic events?' },
  { label: 'Narrative', prompt: 'What led up to the latest NATO summit coverage in the news?' },
  { label: 'Region', prompt: 'Explain causal links around recent Middle East tensions.' },
  { label: 'With event id', prompt: 'What happened after evt_1292440643?' },
];

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
        body: JSON.stringify({ question: text }),
      });

      const data = (await res.json()) as BackendResponse & { error?: string; detail?: string };

      if (!res.ok) {
        const errText =
          typeof data.detail === 'string'
            ? data.detail
            : typeof data.error === 'string'
              ? data.error
              : `Request failed (${res.status})`;
        setMessages((prev) => [
          ...prev,
          {
            id: `assistant-${Date.now()}`,
            role: 'assistant',
            content: `Could not reach CHINTU backend.\n\n${errText}\n\nStart Flask: \`python -m backend\` from the repo root and set CHINTU_BACKEND_URL in the frontend if it is not http://127.0.0.1:5000.`,
          },
        ]);
        return;
      }

      const assistantMsg: ChatMessage = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: data.text?.trim() || 'No answer text returned.',
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
              <img
                src="/logo.png"
                alt="CHINTU"
                width={72}
                height={72}
                className="h-[72px] w-[72px] object-contain bg-transparent"
                decoding="async"
              />
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
