"use client";

import { useState, useRef, useEffect } from "react";
import StatsCards from "./Statscards";

const CHAT_STORAGE_KEY = "agentmap_chat_history";

export interface AskResult {
  answer: string;
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
  onAsk: (question: string) => Promise<AskResult>;
  isReady: boolean;
  filesIndexed: number;
  chunksCreated: number;
  questionsAsked: number;
  statsLoading?: boolean;
 
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

 const [messages, setMessages] = useState<QAMessage[]>([]);

 useEffect(() => {
  try {
    const saved = localStorage.getItem(CHAT_STORAGE_KEY);
    if (saved) setMessages(JSON.parse(saved));
  } catch {}
}, []); 

  useEffect(() => {
    feedEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
  try {
    localStorage.setItem(CHAT_STORAGE_KEY, JSON.stringify(messages));
  } catch {
    
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
         Paste a GitHub repo URL and ask questions. Every answer is grounded in the repo and cited to the exact files.
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
            <div className="qa-answer-text">
              <FormattedAnswer text={message.answer || ""} />
            </div>
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

function renderInline(text: string): React.ReactNode[] {
  const tokens = text.split(/(\*\*[^*]+\*\*|`[^`]+`|\*[^*\n]+\*)/g);
  return tokens.map((token, idx) => {
    if (token.startsWith("**") && token.endsWith("**") && token.length > 4) {
      return <strong key={idx}>{renderInline(token.slice(2, -2))}</strong>;
    }
    if (token.startsWith("`") && token.endsWith("`") && token.length > 2) {
      return (
        <code key={idx} className="qa-inline-code">
          {token.slice(1, -1)}
        </code>
      );
    }
    if (token.startsWith("*") && token.endsWith("*") && token.length > 2) {
      return <em key={idx}>{renderInline(token.slice(1, -1))}</em>;
    }
    return token;
  });
}

function FormattedAnswer({ text }: { text: string }) {
  const segments = text.split(/(```[\s\S]*?```)/g);

  return (
    <div className="qa-markdown">
      {segments.map((segment, segIdx) => {
        if (segment.startsWith("```") && segment.endsWith("```")) {
          const inner = segment.slice(3, -3);
          const firstNewline = inner.indexOf("\n");
          const code =
            firstNewline !== -1 ? inner.slice(firstNewline + 1) : inner;
          return (
            <pre key={segIdx} className="qa-code-block">
              <code>{code.replace(/\n$/, "")}</code>
            </pre>
          );
        }

        const lines = segment.split("\n");
        const elements: React.ReactNode[] = [];
        let listItems: { type: "ul" | "ol"; items: React.ReactNode[] } | null =
          null;

        const flushList = (keyPrefix: string) => {
          if (!listItems) return;
          if (listItems.type === "ul") {
            elements.push(
              <ul key={keyPrefix} className="qa-list">
                {listItems.items.map((item, i) => (
                  <li key={i}>{item}</li>
                ))}
              </ul>
            );
          } else {
            elements.push(
              <ol key={keyPrefix} className="qa-list qa-list-ordered">
                {listItems.items.map((item, i) => (
                  <li key={i}>{item}</li>
                ))}
              </ol>
            );
          }
          listItems = null;
        };

        lines.forEach((rawLine, lineIdx) => {
          const trimmed = rawLine.trim();

          if (!trimmed) {
            flushList(`list-${segIdx}-${lineIdx}`);
            return;
          }

          if (/^(\*{3,}|-{3,}|_{3,})$/.test(trimmed)) {
            flushList(`list-${segIdx}-${lineIdx}`);
            elements.push(<hr key={`hr-${segIdx}-${lineIdx}`} className="qa-hr" />);
            return;
          }

          const headingMatch = trimmed.match(/^(#{1,4})\s+(.*)$/);
          if (headingMatch) {
            flushList(`list-${segIdx}-${lineIdx}`);
            elements.push(
              <div key={`h-${segIdx}-${lineIdx}`} className="qa-heading">
                {renderInline(headingMatch[2])}
              </div>
            );
            return;
          }

          const ulMatch = trimmed.match(/^[-*•]\s+(.*)$/);
          if (ulMatch) {
            if (!listItems || listItems.type !== "ul") {
              flushList(`list-${segIdx}-${lineIdx}`);
              listItems = { type: "ul", items: [] };
            }
            listItems.items.push(renderInline(ulMatch[1]));
            return;
          }

          const olMatch = trimmed.match(/^\d+\.\s+(.*)$/);
          if (olMatch) {
            if (!listItems || listItems.type !== "ol") {
              flushList(`list-${segIdx}-${lineIdx}`);
              listItems = { type: "ol", items: [] };
            }
            listItems.items.push(renderInline(olMatch[1]));
            return;
          }

          flushList(`list-${segIdx}-${lineIdx}`);
          elements.push(
            <p key={`p-${segIdx}-${lineIdx}`} className="qa-paragraph">
              {renderInline(trimmed)}
            </p>
          );
        });

        flushList(`list-end-${segIdx}`);
        return <div key={segIdx} className="qa-segment">{elements}</div>;
      })}
    </div>
  );
}

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