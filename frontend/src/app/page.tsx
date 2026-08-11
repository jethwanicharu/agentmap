"use client";
import { useState } from "react";
import Sidebar, { IndexStatus } from "@/components/Sidebar";
import MainContent, { AskResult } from "@/components/Maincontent";

export default function Page() {
  const [repoInput, setRepoInput] = useState("");
  const [status, setStatus] = useState<IndexStatus>("idle");
  const [stats, setStats] = useState({ files: 0, chunks: 0, questions: 0 });
  const [errorMessage, setErrorMessage] = useState<string | undefined>();

  async function handleIndex() {
  setStatus("indexing");
  setErrorMessage(undefined);
  try {
    const res = await fetch("/api/index", {
      method: "POST",
      body: JSON.stringify({ repo: repoInput }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || err.message || "Indexing failed");
    }
    const data = await res.json();
    setStats({ files: data.filesIndexed, chunks: data.chunksCreated, questions: 0 });
    setStatus("ready");
  } catch (err) {
    setErrorMessage(err instanceof Error ? err.message : "Indexing failed");
    setStatus("error");
  }
}

async function handleAsk(question: string): Promise<AskResult> {
    const res = await fetch("/api/ask", {
      method: "POST",
      body: JSON.stringify({ question, repo: repoInput }),
    });
    if (!res.ok) throw new Error("Couldn't reach the backend");
    const data = await res.json();
    setStats((s) => ({ ...s, questions: s.questions + 1 }));
    return { answer: data.answer, sources: data.sources };
}

  return (
    <div className="app-shell">
      <Sidebar
  repoInput={repoInput}
  onRepoInputChange={setRepoInput}
  onIndex={handleIndex}
  status={status}
  indexedRepoLabel={repoInput}
  errorMessage={errorMessage}
/>
      <MainContent onAsk={handleAsk} isReady={status === "ready"} filesIndexed={stats.files} chunksCreated={stats.chunks} questionsAsked={stats.questions} />
    </div>
  );
}