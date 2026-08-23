"use client";
import { useState, useRef, useEffect } from "react";
import Sidebar, { IndexStatus } from "@/components/Sidebar";
import MainContent, { AskResult } from "@/components/Maincontent";

const REPO_STORAGE_KEY = "agentmap_repo_input";
const INDEX_CACHE_KEY = "agentmap_index_cache";

interface IndexCache {
  repo: string;
  files: number;
  chunks: number;
}

function MenuIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M4 6h16M4 12h16M4 18h16" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

export default function Page() {
  const [repoInput, setRepoInput] = useState("");
  const [status, setStatus] = useState<IndexStatus>("idle");
  const [stats, setStats] = useState({ files: 0, chunks: 0, questions: 0 });
  const [errorMessage, setErrorMessage] = useState<string | undefined>();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const isIndexing = useRef(false);

  useEffect(() => {
    try {
      const savedRepo = localStorage.getItem(REPO_STORAGE_KEY) || "";
      const cached = localStorage.getItem(INDEX_CACHE_KEY);
      setRepoInput(savedRepo);
      if (cached && savedRepo) {
        const parsed: IndexCache = JSON.parse(cached);
        if (parsed.repo === savedRepo) {
          setStatus("ready");
          setStats({ files: parsed.files, chunks: parsed.chunks, questions: 0 });
        }
      }
    } catch {}
  }, []);

  async function handleIndex() {
    if (isIndexing.current) return;
    isIndexing.current = true;
    setStatus("indexing");
    setErrorMessage(undefined);
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/index`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ repo_name: repoInput }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || err.message || "Indexing failed");
      }
      const raw = await res.json();
      const files = raw.file_count ?? 0;
      const chunks = raw.chunk_count ?? 0;
      setStats({ files, chunks, questions: 0 });
      setStatus("ready");
      localStorage.setItem(REPO_STORAGE_KEY, repoInput);
      localStorage.setItem(
        INDEX_CACHE_KEY,
        JSON.stringify({ repo: repoInput, files, chunks })
      );
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : "Indexing failed");
      setStatus("error");
    } finally {
      isIndexing.current = false;
    }
  }

  async function handleAsk(question: string): Promise<AskResult> {
    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/ask`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ repo_name: repoInput, question }),
    });
    if (!res.ok) throw new Error("Couldn't reach the backend");
    const raw = await res.json();
    setStats((s) => ({ ...s, questions: s.questions + 1 }));
    return { answer: raw.answer, sources: raw.sources ?? [] };
  }

  function handleRepoInputChange(value: string) {
    setRepoInput(value);
    try {
      const cached = localStorage.getItem(INDEX_CACHE_KEY);
      if (cached) {
        const parsed: IndexCache = JSON.parse(cached);
        if (parsed.repo !== value) {
          localStorage.removeItem(INDEX_CACHE_KEY);
          setStatus("idle");
          setStats({ files: 0, chunks: 0, questions: 0 });
        }
      }
    } catch {}
  }

  return (
    <div className="app-shell">
      <button
        type="button"
        className="sidebar-open-btn"
        onClick={() => setSidebarOpen(true)}
        aria-label="Open sidebar"
      >
        <MenuIcon />
      </button>

      {sidebarOpen && (
        <div className="sidebar-overlay" onClick={() => setSidebarOpen(false)} />
      )}

      <Sidebar
        repoInput={repoInput}
        onRepoInputChange={handleRepoInputChange}
        onIndex={handleIndex}
        status={status}
        indexedRepoLabel={repoInput}
        errorMessage={errorMessage}
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />
      <MainContent
        onAsk={handleAsk}
        isReady={status === "ready"}
        filesIndexed={stats.files}
        chunksCreated={stats.chunks}
        questionsAsked={stats.questions}
      />
    </div>
  );
}