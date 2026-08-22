"use client";
import { useEffect, useState } from "react";

const INDEXING_MESSAGES = [
  "Fetching repository files…",
  "Splitting into chunks…",
  "Generating embeddings…",
  "Storing in vector DB…",
  "Almost there…",
];

const STORAGE_KEY = "agentmap_repo_input";
const REPO_STORAGE_KEY = "agentmap_repo_input";
const INDEX_CACHE_KEY = "agentmap_index_cache";

interface IndexCache {
  repo: string;
  files: number;
  chunks: number;
}


function useStepProgress(steps: string[], active: boolean, intervalMs = 1800) {
  const [index, setIndex] = useState(0);

  useEffect(() => {
    if (!active) { setIndex(0); return; }
    const id = setInterval(() => {
      setIndex((i) => (i < steps.length - 1 ? i + 1 : i));
    }, intervalMs);
    return () => clearInterval(id);
  }, [active, steps.length, intervalMs]);

  return index;
}


export type IndexStatus = "idle" | "indexing" | "ready" | "error";

export interface SidebarProps {
  repoInput: string;
  onRepoInputChange: (value: string) => void;
  onIndex: () => void;
  status: IndexStatus;
  indexedRepoLabel?: string;
  errorMessage?: string;
  isOpen?: boolean;
  onClose?: () => void;
}

function parseErrorMessage(err: unknown): string {
  if (!err) return "Something went wrong";
  if (typeof err === "string") return err;
  if (typeof err === "object") {
    const e = err as Record<string, unknown>;
    if (typeof e.message === "string") return e.message;
    if (typeof e.detail === "string") return e.detail;
    if (typeof e.detail === "object" && e.detail !== null) {
      const d = e.detail as Record<string, unknown>;
      if (typeof d.message === "string") return d.message;
    }
  }
  return "Something went wrong";
}

export default function Sidebar({
  repoInput,
  onRepoInputChange,
  onIndex,
  status,
  indexedRepoLabel,
  errorMessage,
  isOpen = false,
  onClose,
}: SidebarProps) {
  const isIndexing = status === "indexing";
  const currentStep = useStepProgress(INDEXING_MESSAGES, isIndexing);

  // Load saved repo URL on mount
  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved && !repoInput) onRepoInputChange(saved);
  }, []);

  // Save repo URL on change
  useEffect(() => {
    if (repoInput) localStorage.setItem(STORAGE_KEY, repoInput);
  }, [repoInput]);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!repoInput.trim() || isIndexing) return;
    onIndex();
  }

  function CloseIcon() {
    return (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M6 6l12 12M6 18L18 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
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

  function handleReset() {
  localStorage.removeItem(STORAGE_KEY);
  localStorage.removeItem("agentmap_index_cache");
  onRepoInputChange("");
}

  const displayError = parseErrorMessage(errorMessage);

  return (
      <aside className={`sidebar${isOpen ? " sidebar-open" : ""}`}>
      <button
        type="button"
        className="sidebar-close-btn"
        onClick={onClose}
        aria-label="Close sidebar"
      >
        <CloseIcon />
      </button>
      <h2 className="sidebar-title">Index a repository</h2>
      <p className="sidebar-desc">
        Point AgentMap at any GitHub repo to start asking questions about it.
      </p>

      <form className="sidebar-form" onSubmit={handleSubmit}>
        <div className="repo-input-wrap">
          <GithubIcon />
          <input
            className="repo-input"
            type="text"
            placeholder="owner/repo"
            value={repoInput}
            disabled={isIndexing}
            onChange={(e) => onRepoInputChange(e.target.value)}
            aria-label="Repository owner and name"
          />
          {repoInput && !isIndexing && (
            <button
              type="button"
              className="url-reset-btn"
              onClick={handleReset}
              aria-label="Clear repository URL"
              title="Clear URL"
            >
              <ResetIcon />
            </button>
          )}
        </div>

        <button
          type="submit"
          className="btn-primary"
          disabled={isIndexing || !repoInput.trim()}
        >
          {isIndexing ? (
            <>
              <Spinner /> Indexing…
            </>
          ) : (
            "Index repository"
          )}
        </button>
      </form>

      <StatusLine status={status} indexedRepoLabel={indexedRepoLabel} />

      {(isIndexing || status === "ready") && (
        <IndexTimeline
          steps={INDEXING_MESSAGES}
          currentStep={currentStep}
          isReady={status === "ready"}
        />
      )}

      {status === "error" && displayError && (
        <p className="status-error-text">{displayError}</p>
      )}

      <hr className="sidebar-divider" />

      <div>
        <div className="sidebar-about-title">About</div>
        <p className="sidebar-about-text">
          AgentMap indexes a codebase and answers questions with grounded,
          cited sources — built for the pain of inheriting an unfamiliar
          codebase under time pressure.
        </p>
      </div>
    </aside>
  );
}

function StatusLine({
  status,
  indexedRepoLabel,
}: {
  status: IndexStatus;
  indexedRepoLabel?: string;
}) {
  let dotClass = "idle";
  let text = "No repository indexed yet";

  if (status === "indexing") {
    dotClass = "indexing";
    text = "Indexing repository…";
  } else if (status === "ready") {
    dotClass = "ready";
    text = indexedRepoLabel ? `Ready · ${indexedRepoLabel}` : "Ready";
  } else if (status === "error") {
    dotClass = "error";
    text = "Indexing failed";
  }

  return (
    <div className="status-row">
      <span className={`status-dot ${dotClass}`} />
      <span>{text}</span>
    </div>
  );
}

function GithubIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path
        d="M12 2C6.48 2 2 6.58 2 12.25c0 4.53 2.87 8.37 6.84 9.73.5.1.68-.22.68-.5 0-.24-.01-1.04-.01-1.88-2.78.62-3.37-1.21-3.37-1.21-.45-1.18-1.11-1.5-1.11-1.5-.9-.63.07-.62.07-.62 1 .07 1.53 1.05 1.53 1.05.89 1.56 2.34 1.11 2.91.85.09-.66.35-1.11.63-1.37-2.22-.26-4.56-1.14-4.56-5.07 0-1.12.39-2.03 1.03-2.75-.1-.26-.45-1.31.1-2.73 0 0 .84-.28 2.75 1.05a9.3 9.3 0 0 1 5 0c1.91-1.33 2.75-1.05 2.75-1.05.55 1.42.2 2.47.1 2.73.64.72 1.03 1.63 1.03 2.75 0 3.94-2.34 4.8-4.57 5.06.36.32.68.94.68 1.9 0 1.37-.01 2.47-.01 2.81 0 .27.18.6.69.5A10.26 10.26 0 0 0 22 12.25C22 6.58 17.52 2 12 2Z"
        fill="currentColor"
      />
    </svg>
  );
}

function Spinner() {
  return (
    <svg
      width="13"
      height="13"
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      style={{ animation: "spin 0.8s linear infinite" }}
    >
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      <circle cx="12" cy="12" r="9" stroke="rgba(255,255,255,0.35)" strokeWidth="3" />
      <path d="M21 12a9 9 0 0 0-9-9" stroke="#fff" strokeWidth="3" strokeLinecap="round" />
    </svg>
  );
}

function IndexTimeline({
  steps,
  currentStep,
  isReady,
}: {
  steps: string[];
  currentStep: number;
  isReady: boolean;
}) {
  return (
    <div className="index-timeline">
      {steps.map((step, i) => {
        const done = isReady || i < currentStep;
        const active = !isReady && i === currentStep;
        return (
          <div
            key={step}
            className={`timeline-step${done ? " done" : ""}${active ? " active" : ""}`}
          >
            <span className={`timeline-check${done ? " done" : ""}`}>
              <CheckIcon />
            </span>
            {step}
          </div>
        );
      })}
      {isReady && (
        <div className="timeline-start-badge">
          <span className="status-dot ready" /> Start
        </div>
      )}
    </div>
  );
}

function CheckIcon() {
  return (
    <svg width="10" height="10" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M5 13l4 4L19 7" stroke="#0a0f0a" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}