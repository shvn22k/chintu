'use client';

import { useRef, useEffect } from 'react';
import { ChatMessage } from '@/types';
import MessageRow from './MessageRow';

interface ChatAreaProps {
  messages: ChatMessage[];
  isThinking: boolean;
}

export default function ChatArea({ messages, isThinking }: ChatAreaProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isThinking]);

  return (
    <div className="flex-1 overflow-y-auto px-6 py-6">
      <div className="max-w-[720px] mx-auto">
        {messages.map((msg) => (
          <MessageRow key={msg.id} message={msg} />
        ))}

        {/* Thinking indicator */}
        {isThinking && (
          <div className="flex flex-col items-start mb-4">
            <span className="text-[10px] font-jetbrains text-muted mb-1 px-1">
              chintu
            </span>
            <div className="flex items-center gap-1 py-2 px-1">
              <span className="thinking-dot w-1.5 h-1.5 rounded-full bg-muted" />
              <span className="thinking-dot w-1.5 h-1.5 rounded-full bg-muted" />
              <span className="thinking-dot w-1.5 h-1.5 rounded-full bg-muted" />
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>
    </div>
  );
}
