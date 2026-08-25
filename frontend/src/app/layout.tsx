import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import CircuitBackground from "@/components/Circuitbackground";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "AgentMap — Multi-Agent RAG for GitHub Repos",
  description: "AgentMap indexes any GitHub repo using a LangGraph multi-agent pipeline and answers questions with grounded, cited sources — built to make understanding unfamiliar codebases fast.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${geistSans.variable} ${geistMono.variable}`}>
      <body>
      <CircuitBackground />

        {children}</body>
    </html>
  );
}
