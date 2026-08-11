"use client";

export type IndexStatus = "idle" | "indexing" | "ready" | "error";

export interface SidebarProps {
  /** Current value of the repo url / owner/repo input */
  repoInput: string;
  /** Called on every keystroke in the repo input */
  onRepoInputChange: (value: string) => void;
  /** Called when the user submits the "Index repository" form */
  onIndex: () => void;
  /** Current lifecycle state of the indexing job */
  status: IndexStatus;
  /** e.g. "jethawanchanu/charr-portfolio" — shown once status is "ready" */
  indexedRepoLabel?: string;
  /** Shown when status is "error" */
  errorMessage?: string;
}

export default function Sidebar({
  repoInput,
  onRepoInputChange,
  onIndex,
  status,
  indexedRepoLabel,
  errorMessage,
}: SidebarProps) {
  const isIndexing = status === "indexing";

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!repoInput.trim() || isIndexing) return;
    onIndex();
  }

  return (
    <aside className="sidebar">
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

      <StatusLine
        status={status}
        indexedRepoLabel={indexedRepoLabel}
      />

      {status === "error" && errorMessage && (
        <p className="status-error-text">{errorMessage}</p>
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