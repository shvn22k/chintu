'use client';

import { ChatMessage } from '@/types';
import VizArtifact from './VizArtifact';

interface MessageRowProps {
  message: ChatMessage;
}

export default function MessageRow({ message }: MessageRowProps) {
  const isUser = message.role === 'user';

  return (
    <div className={`flex flex-col ${isUser ? 'items-end' : 'items-start'} mb-4`}>
      {/* Sender label */}
      <span className="text-[10px] font-jetbrains text-muted mb-1 px-1">
        {isUser ? 'you' : 'chintu'}
      </span>

      {/* Message content */}
      <div
        className={
          isUser
            ? 'max-w-[75%] bg-bg3 text-text text-sm font-sora px-3.5 py-2.5 rounded-xl rounded-br-[4px] leading-relaxed'
            : 'max-w-[85%] text-text text-sm font-sora leading-relaxed whitespace-pre-wrap'
        }
      >
        {message.content}
      </div>

      {!isUser && message.response?.apiError && (
        <p className="max-w-[85%] mt-1 text-[11px] font-jetbrains text-amber/90 px-1">
          API note: {message.response.apiError}
        </p>
      )}

      {/* Viz artifact for assistant messages */}
      {!isUser && message.response && (
        <div className="w-full max-w-[85%] mt-1">
          <VizArtifact response={message.response} />
        </div>
      )}
    </div>
  );
}
