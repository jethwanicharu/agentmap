# AgentMap — a multi-agent LangGraph system that indexes any GitHub repo and answers questions with grounded, cited sources

![LangGraph](https://img.shields.io/badge/LangGraph-multi--agent-blue)
![RAG](https://img.shields.io/badge/RAG-retrieval--augmented--generation-green)clea
![FastAPI](https://img.shields.io/badge/FastAPI-backend-009688?logo=fastapi&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-frontend-black?logo=next.js&logoColor=white)
![ChromaDB](https://img.shields.io/badge/ChromaDB-vector--store-orange)
![Groq](https://img.shields.io/badge/LLM%20serving-Groq-purple)

Point AgentMap at any GitHub repo URL. It fetches and chunks the codebase, embeds it into a vector
store, and runs a **LangGraph multi-agent pipeline** to answer questions about it — with real
citations back to the files the answer came from. Built for the pain of inheriting an unfamiliar
codebase under time pressure.

**Live demo:** [charu-agentmap.vercel.app](https://charu-agentmap.vercel.app)

---

## Highlights

- **Multi-agent LangGraph pipeline** — a router inspects each question and sends it down one of
  two paths: a **Retriever Agent** for semantic code questions, or a dedicated **file-structure
  path** for repo-layout questions ("how many files", "what's the folder structure"), which
  answers directly from indexed metadata instead of spending an LLM call on something
  deterministic.
- **Retrieval-Augmented Generation (RAG)** — questions are answered strictly from the codebase's
  own embedded content via ChromaDB similarity search, not the LLM's general training knowledge,
  which keeps every answer grounded and traceable to a source file.
- **Grounded, cited answers** — the Answer Agent only responds from retrieved context and returns
  the source file paths alongside the answer.
- **Any public (or token-authorized private) GitHub repo** — repos are fetched, chunked, and
  embedded per-request into their own ChromaDB collection, keyed by `owner/repo`.
- **Full-stack, split deployment** — FastAPI backend on Render, Next.js frontend on Vercel,
  talking over a CORS-enabled REST API.
- **Production-style error handling** — the API distinguishes invalid repo format, private repos
  without a token, expired/bad tokens, GitHub rate limits, and unindexed repos, each with its own
  error code instead of a generic 500.
- **Persistent chat & stats on the frontend** — indexed repo, chat history, and file/chunk counts
  survive a page refresh via localStorage, so the app resumes exactly where you left off.
- **Zero infrastructure cost** — runs entirely on free tiers (Groq for LLM inference, HuggingFace
  for embeddings, Render + Vercel for hosting), with no paid API keys or GPU rental required.

---

## How It Works (Flow)

**1. Indexing a repo**

```
User enters "owner/repo" in the sidebar
        │
        ▼
   POST /index
        │
        ▼
fetch_repo_files()   →  pulls raw files from GitHub via PyGithub (token-aware)
        │
        ▼
chunk_all_files()    →  splits files into overlapping text chunks
        │
        ▼
get_embeddings()     →  HuggingFace inference API turns chunks into vectors
        │
        ▼
ChromaDB collection  →  one collection per repo, keyed by owner_repo
        │
        ▼
Frontend shows file/chunk counts + "ready" status
```

**2. Asking a question**

```
User types a question
        │
        ▼
   POST /ask
        │
        ▼
LangGraph pipeline
        │
        ├── Router node classifies the question
        │
        ├── File-structure question ──► File Tree node
        │                               (answers directly from collection metadata,
        │                                no LLM call needed)
        │
        └── Code / semantic question ──► Retriever Agent
                                          (ChromaDB similarity search)
                                                │
                                                ▼
                                          Answer Agent
                                          (Groq LLM, context-only prompt)
                                                │
                                                ▼
                                   Grounded answer + cited source files
        │
        ▼
Frontend renders answer + source chips in the chat feed
```

The router means a structural question never pays for an LLM call it doesn't need — it's answered
straight from the vector store's metadata, while code questions still go through full retrieval
and generation.

---

## Repository Structure

```
agentmap/
│
├── chroma_db/
│
├── frontend/
│   └── src/
│       ├── app/
│       │   ├── page.tsx
│       │   ├── layout.tsx
│       │   └── globals.css
│       │
│       └── components/
│           ├── Maincontent.tsx
│           ├── Sidebar.tsx
│           ├── Statscards.tsx
│           └── Circuitbackground.tsx
│
├── src/
│   ├── __init__.py
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   └── main.py
│   │
│   ├── ingestion/
│   │   ├── __init__.py
│   │   └── github_fetcher.py
│   │
│   ├── chunking/
│   │   ├── __init__.py
│   │   └── chunker.py
│   │
│   ├── embeddings/
│   │   ├── __init__.py
│   │   └── vector_store.py
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   └── graph.py
│   │
│   └── retrieval/
│       ├── __init__.py
│       └── rag_chain.py
│
├── .env
├── .gitignore
├── Dockerfile
├── LICENSE
├── README.md
└── requirements.txt
```

---

## Backend (FastAPI)

| Module | Responsibility |
|---|---|
| `api/main.py` | FastAPI app — `/health`, `/index`, `/ask` routes, request validation, structured error handling |
| `ingestion/github_fetcher.py` | Fetches repo files via PyGithub (token-aware, skips excluded dirs/binary files) |
| `chunking/chunker.py` | Splits fetched files into overlapping character-based chunks |
| `embeddings/vector_store.py` | HuggingFace embeddings + ChromaDB client, per-repo collection management |
| `agents/graph.py` | LangGraph pipeline — router, file-tree node, retriever agent, answer agent |
| `retrieval/rag_chain.py` | Prompt template + Groq LLM chain used by the Answer Agent |

### API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Health check |
| `/index` | POST | Index a repo — fetch, chunk, embed, store (`repo_name`, optional `github_token`) |
| `/ask` | POST | Ask a question about an already-indexed repo (`repo_name`, `question`) |

Errors return a structured `{ "error_code": "...", "message": "..." }` body — e.g.
`INVALID_REPO_FORMAT`, `REPO_NOT_FOUND`, `REPO_PRIVATE`, `BAD_TOKEN`, `RATE_LIMITED`,
`NOT_INDEXED` — instead of a bare stack trace.

---

## Frontend (Next.js)

Built with Next.js 14 (App Router), React, TypeScript, and plain CSS — no UI library.

| File | Responsibility |
|---|---|
| `app/page.tsx` | Central state owner — repo input, indexing status, stats, chat calls (`/index`, `/ask`) |
| `app/layout.tsx` | HTML shell, metadata, mounts `CircuitBackground` |
| `components/Sidebar.tsx` | Repo input, indexing progress timeline, status line, about section |
| `components/Maincontent.tsx` | Chat feed — search bar + ask bar, question/answer blocks, source chips |
| `components/Statscards.tsx` | Animated counters for files indexed / chunks created / questions asked |
| `components/Circuitbackground.tsx` | Decorative animated SVG background |

Repo input, indexed stats, and chat history are all persisted to `localStorage`, so the app
resumes its state after a page refresh instead of resetting.

---

## Setup

### Backend (local)

pip install -r requirements.txt

# .env
GROQ_API_KEY=...        # LLM inference (Answer Agent)
HF_API_KEY=...          # HuggingFace embeddings (vector store)
GITHUB_TOKEN=...        # optional — needed for private repos / higher rate limits

uvicorn src.api.main:app --reload

### Backend (deployed)

I've deployed the backend on Render:

https://charu-agentmap-api.onrender.com

I use this as NEXT_PUBLIC_API_URL when setting up the frontend below.

### Frontend

cd frontend
npm install
npm run dev

I've deployed the frontend on Vercel:

https://charu-agentmap.vercel.app/

Set NEXT_PUBLIC_API_URL in the frontend's environment config to either the local backend
(http://localhost:8000) or the deployed Render URL above, then open the app and point it at any
owner/repo.

## Scope & Production Gap

This is a **portfolio project**, built to demonstrate multi-agent orchestration with LangGraph,
retrieval-augmented generation, and a deployed full-stack app — not a hardened product. What's
intentionally **not** built:

- **Persistence across restarts for large repos at scale** — collections live in ChromaDB per
  repo; there's no eviction, quota, or multi-tenant isolation policy yet.
- **Auth / rate limiting on the API itself** — CORS is open; there's no per-user throttling beyond
  what GitHub's own API enforces on the token.
- **Incremental re-indexing** — a repo is indexed fresh each time rather than diffed against its
  last indexed state.

---

## Future Ideas

- **Private-repo, cross-project assistant** — letting AgentMap work against a user's own private
  repos, so anyone can point it at their own codebase and get grounded answers without digging
  through files themselves.
- **Smarter, code-aware chunking** — moving beyond fixed-size text splitting toward chunking that
  respects function/class boundaries.
- **Multi-repo questions** — comparing or cross-referencing more than one indexed repo in a single
  answer.