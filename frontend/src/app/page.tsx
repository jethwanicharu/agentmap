"use client";
import { useState } from "react";
import Sidebar, { IndexStatus } from "@/components/Sidebar";
import MainContent, { AskResult } from "@/components/Maincontent";

export default function Page() {
  const [repoInput, setRepoInput] = useState("");
  const [status, setStatus] = useState<IndexStatus>("idle");
  const [stats, setStats] = useState({ files: 0, chunks: 0, questions: 0 });

  async function handleIndex() {
    setStatus("indexing");
    try {
      const res = await fetch("/api/index", { method: "POST", body: JSON.stringify({ repo: repoInput }) });
      if (!res.ok) throw new Error("Indexing failed");
      const data = await res.json();
      setStats({ files: data.filesIndexed, chunks: data.chunksCreated, questions: 0 });
      setStatus("ready");
    } catch {
      setStatus("error");
    }
  }

  async function handleAsk(question: string): Promise<AskResult> {
    const res = await fetch("/api/ask", { method: "POST", body: JSON.stringify({ question }) });
    if (!res.ok) throw new Error("Couldn't reach the backend");
    const data = await res.json();
    setStats((s) => ({ ...s, questions: s.questions + 1 }));
    return { answer: data.answer, sources: data.sources };
  }

  return (
    <div className="app-shell">
      <Sidebar repoInput={repoInput} onRepoInputChange={setRepoInput} onIndex={handleIndex} status={status} indexedRepoLabel={repoInput} />
      <MainContent onAsk={handleAsk} isReady={status === "ready"} filesIndexed={stats.files} chunksCreated={stats.chunks} questionsAsked={stats.questions} />
    </div>
  );
}