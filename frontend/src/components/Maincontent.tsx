"use client";

import { useState, useRef, useEffect } from "react";
import StatsCards from "./Statscards";

const CHAT_STORAGE_KEY = "agentmap_chat_history";

export interface AskResult {
  answer: string;
  /** e.g. ["src/components/ui/Button.tsx", "src/app/page.tsx"] */
  sources?: string[];
}

interface QAMessage {
  id: string;
  question: string;
  status: "loading" | "done" | "error";
  answer?: string;
  sources?: string[];
  errorMessage?: string;
}

export interface MainContentProps {
  /** Called with the user's question; resolve with the answer or throw/reject on failure */
  onAsk: (question: string) => Promise<AskResult>;
  /** Whether a repo has been indexed yet — gates the ask bar */
  isReady: boolean;
  filesIndexed: number;
  chunksCreated: number;
  questionsAsked: number;
  statsLoading?: boolean;
  /** A suggested question shown next to the top search field */
  suggestedQuestion?: string;
  onResetChat?: () => void; 
}

export default function MainContent({
  onAsk,
  isReady,
  filesIndexed,
  chunksCreated,
  questionsAsked,
  statsLoading = false,
  suggestedQuestion = "how many buttons do we have in this codebase",
  onResetChat, 
}: MainContentProps) {
  const [searchValue, setSearchValue] = useState("");
  const [askValue, setAskValue] = useState("");
  const feedEndRef = useRef<HTMLDivElement>(null);

  const [messages, setMessages] = useState<QAMessage[]>(() => {
  if (typeof window === "undefined") return [];
  try {
    const saved = localStorage.getItem(CHAT_STORAGE_KEY);
    return saved ? JSON.parse(saved) : [];
  } catch {
    return [];
  }
});

  useEffect(() => {
    feedEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
  try {
    localStorage.setItem(CHAT_STORAGE_KEY, JSON.stringify(messages));
  } catch {
    // storage full ya blocked — silently ignore
  }
}, [messages]);

  async function submitQuestion(question: string) {
    const trimmed = question.trim();
    if (!trimmed || !isReady) return;

    const id = `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
    setMessages((prev) => [
      ...prev,
      { id, question: trimmed, status: "loading" },
    ]);
    setAskValue("");
    setSearchValue("");

    try {
      const result = await onAsk(trimmed);
      setMessages((prev) =>
        prev.map((m) =>
          m.id === id
            ? { ...m, status: "done", answer: result.answer, sources: result.sources }
            : m
        )
      );
    } catch (err) {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === id
            ? {
                ...m,
                status: "error",
                errorMessage:
                  err instanceof Error
                    ? err.message
                    : "Something went wrong answering that. Please try again.",
              }
            : m
        )
      );
    }
  }

  function retry(message: QAMessage) {
    setMessages((prev) => prev.filter((m) => m.id !== message.id));
    submitQuestion(message.question);
  }
  function resetChat() {
  setMessages([]);
  try {
    localStorage.removeItem(CHAT_STORAGE_KEY);
  } catch {}
  onResetChat?.();
}

  function handleAskSubmit(e: React.FormEvent) {
    e.preventDefault();
    submitQuestion(askValue);
  }

  function handleSearchSubmit(e: React.FormEvent) {
    e.preventDefault();
    submitQuestion(searchValue);
  }

  return (
    <div className="main-content">
      <header className="main-header">
        <h1 className="main-title">AgentMap</h1>
        <p className="main-subtitle">
          Multi-agent RAG assistant for code, text, and consistency checks
        </p>
      </header>

      <StatsCards
        filesIndexed={filesIndexed}
        chunksCreated={chunksCreated}
        questionsAsked={questionsAsked}
        loading={statsLoading}
      />

      <form className="query-row" onSubmit={handleSearchSubmit}>
        <div className="search-input-wrap">
          <SearchIcon />
          <input
            className="search-input"
            type="text"
            placeholder="Search anything about this codebase"
            value={searchValue}
            disabled={!isReady}
            onChange={(e) => setSearchValue(e.target.value)}
            aria-label="Search the codebase"
          />
        </div>
        <button
          type="button"
          className="suggested-chip"
          disabled={!isReady}
          onClick={() => submitQuestion(suggestedQuestion)}
          title={suggestedQuestion}
        >
          {suggestedQuestion}
        </button>
      </form>

      <div className="feed">
        {messages.length === 0 && (
          <div className="empty-state">
            {isReady
              ? "Ask a question below to get a grounded answer with cited sources."
              : "Index a repository from the sidebar to start asking questions."}
          </div>
        )}

        {messages.length > 0 && (
  <div className="chat-reset-row">
    <button
      type="button"
      className="chat-reset-btn"
      onClick={resetChat}
      title="Clear chat"
      aria-label="Clear chat history"
    >
      <ResetIcon />
      Clear chat
    </button>
  </div>
)}

        {messages.map((message) => (
          <QABlock key={message.id} message={message} onRetry={() => retry(message)} />
        ))}
        <div ref={feedEndRef} />
      </div>

      <div className="ask-bar-wrap">
        <div style={{ width: "100%", display: "flex", flexDirection: "column", alignItems: "center" }}>
          <form className="ask-bar" onSubmit={handleAskSubmit}>
            <input
              className="ask-input"
              type="text"
              placeholder={
                isReady
                  ? "Ask something about this codebase..."
                  : "Index a repository to start asking questions"
              }
              value={askValue}
              disabled={!isReady}
              onChange={(e) => setAskValue(e.target.value)}
              aria-label="Ask a question about this codebase"
            />
            <button
              type="submit"
              className="ask-send-btn"
              disabled={!isReady || !askValue.trim()}
              aria-label="Send question"
            >
              <ArrowIcon />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

function QABlock({
  message,
  onRetry,
}: {
  message: QAMessage;
  onRetry: () => void;
}) {
  return (
    <div className="qa-block">
      <div className="qa-question">
        <span className="qa-question-icon">?</span>
        <div className="qa-question-body">
          <div className="qa-question-label">User input</div>
          <div className="qa-question-text">{message.question}</div>
        </div>
      </div>

      <div className={`qa-answer${message.status === "error" ? " is-error" : ""}`}>
        <div className="qa-answer-label">
          <span className="brand-dot" />
          AgentMap AI answer
        </div>

        {message.status === "loading" && (
          <span className="typing-dots" aria-label="Thinking">
            <span />
            <span />
            <span />
          </span>
        )}

        {message.status === "error" && (
          <>
            <p className="qa-error-text">
              {message.errorMessage || "Couldn't get an answer. Please try again."}
            </p>
            <button className="qa-retry-btn" onClick={onRetry}>
              Retry
            </button>
          </>
        )}

        {message.status === "done" && (
          <>
            <p className="qa-answer-text">{message.answer}</p>
            {message.sources && message.sources.length > 0 && (
              <div className="source-chips">
                {chunk(message.sources, 2).map((row, i) => (
                  <div className="source-chip-row" key={i}>
                    {row.map((src, j) => (
                      <span className="source-chip" key={`${src}-${j}`}>
                        {src}
                      </span>
                    ))}
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

/** Groups a flat source list into rows of `size` for the pill display —
 *  e.g. ["a.tsx","b.tsx","c.tsx"] with size 2 -> [["a.tsx","b.tsx"],["c.tsx"]] */
function chunk<T>(items: T[], size: number): T[][] {
  const rows: T[][] = [];
  for (let i = 0; i < items.length; i += size) {
    rows.push(items.slice(i, i + size));
  }
  return rows;
}

function SearchIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="11" cy="11" r="7" stroke="currentColor" strokeWidth="2" />
      <path d="M21 21l-4.3-4.3" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

function ArrowIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path
        d="M4 12h16M13 5l7 7-7 7"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function ResetIcon() {
  return (
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path
        d="M3 12a9 9 0 1 1 2.64 6.36M3 12V6m0 6h6"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}