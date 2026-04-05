import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: "#1a1a1a",
        bg2: "#222222",
        bg3: "#2a2a2a",
        border: "rgba(255,255,255,0.08)",
        border2: "rgba(255,255,255,0.13)",
        text: "#e8e6e1",
        muted: "#7a7875",
        accent: "#c87c5a",
        blue: "#5a8fc8",
        green: "#5ab87a",
        amber: "#c8a85a",
        red: "#f85149",
      },
      fontFamily: {
        sora: ["var(--font-sora)", "sans-serif"],
        jetbrains: ["var(--font-jetbrains)", "monospace"],
        outfit: ["var(--font-outfit)", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
