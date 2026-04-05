import type { Metadata } from "next";
import { Sora, JetBrains_Mono, Outfit } from "next/font/google";
import "./globals.css";

const sora = Sora({
  variable: "--font-sora",
  subsets: ["latin"],
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-jetbrains",
  subsets: ["latin"],
  display: "swap",
});

const outfit = Outfit({
  variable: "--font-outfit",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "CHINTU — Geopolitical Knowledge Graph",
  description:
    "Query geopolitical events, causal chains, entity relationships, and topic timelines with CHINTU.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${sora.variable} ${jetbrainsMono.variable} ${outfit.variable}`}>
      <body className="antialiased">{children}</body>
    </html>
  );
}
