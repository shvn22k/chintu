'use client';

import { useState } from 'react';

interface SidebarProps {
  onNewAnalysis: () => void;
}

const recentItems = [
  'US–China trade analysis',
  'NATO expansion impact',
  'OPEC supply chain',
  'Taiwan strait tensions',
];

export default function Sidebar({ onNewAnalysis }: SidebarProps) {
  const [activeIndex, setActiveIndex] = useState<number | null>(null);

  return (
    <aside className="w-[220px] h-screen flex flex-col bg-bg2 border-r border-border fixed left-0 top-0 z-10">
      {/* Logo */}
      <div className="flex items-center gap-2 px-4 pt-5 pb-4">
        <div className="border border-border2 rounded px-1.5 py-0.5 font-jetbrains text-[11px] text-accent tracking-wider">
          CHN
        </div>
        <span className="font-sora text-sm font-medium text-text tracking-wide">CHINTU</span>
      </div>

      {/* New analysis button */}
      <div className="px-3 pb-4">
        <button
          onClick={onNewAnalysis}
          className="w-full flex items-center gap-2 px-3 py-2 rounded-md border border-border2 text-text text-sm font-sora hover:bg-bg3 transition-colors duration-150"
        >
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M7 1v12M1 7h12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
          </svg>
          New analysis
        </button>
      </div>

      {/* Recent */}
      <div className="flex-1 overflow-y-auto px-3">
        <div className="text-[11px] font-jetbrains text-muted uppercase tracking-wider px-2 pb-2">
          Recent
        </div>
        <div className="space-y-0.5">
          {recentItems.map((item, i) => (
            <button
              key={i}
              onClick={() => setActiveIndex(i)}
              className={`w-full text-left px-2 py-1.5 rounded text-sm font-sora truncate transition-colors duration-150 ${
                activeIndex === i
                  ? 'bg-bg3 text-text'
                  : 'text-muted hover:text-text hover:bg-bg3'
              }`}
            >
              {item}
            </button>
          ))}
        </div>
      </div>

      {/* User */}
      <div className="px-3 py-4 border-t border-border">
        <div className="flex items-center gap-2 px-2">
          <div className="w-7 h-7 rounded-full bg-bg3 border border-border2 flex items-center justify-center text-xs font-jetbrains text-accent">
            A
          </div>
          <span className="text-sm font-sora text-muted">analyst</span>
        </div>
      </div>
    </aside>
  );
}
