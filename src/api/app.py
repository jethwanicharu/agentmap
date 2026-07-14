
import streamlit as st
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from src.ingestion.github_fetcher import fetch_repo_files
from src.chunking.chunker import chunk_all_files
from src.embeddings.vector_store import get_chroma_client, get_or_create_collection, add_chunks_to_store
from src.retrieval.rag_chain import ask_question

st.set_page_config(
    page_title="AgentMap",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background: radial-gradient(circle at 15% 0%, #1a1f3d 0%, #0e1117 45%); }
    section[data-testid="stSidebar"] { background: #131722; border-right: 1px solid #262b3d; }
    .am-hero {
        padding: 1.75rem 2rem; border-radius: 16px;
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 55%, #0ea5e9 100%);
        margin-bottom: 1.75rem; box-shadow: 0 8px 30px rgba(79, 70, 229, 0.25);
    }
    .am-hero h1 { color: white; font-size: 2.1rem; font-weight: 800; margin: 0; letter-spacing: -0.5px; }
    .am-hero p { color: rgba(255,255,255,0.88); font-size: 0.98rem; margin: 0.35rem 0 0 0; font-weight: 500; }
    .am-badge {
        display: inline-block; background: rgba(255,255,255,0.18); color: white;
        padding: 3px 12px; border-radius: 20px; font-size: 0.72rem; font-weight: 600;
        margin-top: 0.6rem; letter-spacing: 0.3px;
    }
    .am-metric { background: #161b2c; border: 1px solid #262b3d; border-radius: 12px; padding: 1rem 1.2rem; text-align: left; }
    .am-metric .val { font-size: 1.6rem; font-weight: 800; color: #a78bfa; }
    .am-metric .lbl { font-size: 0.78rem; color: #9099b0; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px; }
    .am-user-msg {
        background: #262b45; border-radius: 14px 14px 4px 14px; padding: 0.8rem 1.1rem;
        margin: 0.4rem 0; color: #e5e7eb; max-width: 85%; margin-left: auto; border: 1px solid #363c5c;
    }
    .am-bot-msg {
        background: #14182a; border-radius: 14px 14px 14px 4px; padding: 0.9rem 1.1rem;
        margin: 0.4rem 0; color: #d7dae5; max-width: 90%; border: 1px solid #232842;
    }
    .am-source-tag {
        display: inline-block; background: rgba(167, 139, 250, 0.12); color: #a78bfa;
        border: 1px solid rgba(167, 139, 250, 0.3); padding: 2px 10px; border-radius: 20px;
        font-size: 0.72rem; font-family: 'JetBrains Mono', monospace; margin: 3px 4px 0 0;
    }
    .stButton > button {
        background: linear-gradient(135deg, #6366f1, #8b5cf6); color: white; border: none;
        border-radius: 10px; font-weight: 600; padding: 0.5rem 1rem; transition: all 0.2s ease;
    }
    .stButton > button:hover { box-shadow: 0 4px 16px rgba(139, 92, 246, 0.4); transform: translateY(-1px); }
    .stTextInput > div > div > input { background: #161b2c; border: 1px solid #2a3050; border-radius: 8px; color: #e5e7eb; }
    .am-status-ready { color: #34d399; font-weight: 600; font-size: 0.85rem; }
    .am-status-empty { color: #f59e0b; font-weight: 600; font-size: 0.85rem; }
    div[data-testid="stExpander"] { background: #12162555; border: 1px solid #262b3d; border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

for key, default in {
    "indexed": False, "collection": None, "chat_history": [],
    "repo_name_indexed": "", "file_count": 0, "chunk_count": 0,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

st.markdown("""
<div class="am-hero">
    <h1>🗺️ AgentMap</h1>
    <p>Codebase Context & Consistency Assistant — RAG-powered code understanding</p>
    <span class="am-badge">⚡ Groq LLaMA 3.3</span>
    <span class="am-badge">🧠 LangChain + LangGraph</span>
    <span class="am-badge">🔍 ChromaDB</span>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### 📦 Index a Repository")
    st.caption("Point AgentMap at any GitHub repo to start asking questions.")
    repo_name = st.text_input("GitHub repo", placeholder="owner/repo", label_visibility="collapsed")

    if st.button("🚀 Index Repository", use_container_width=True):
        if not repo_name:
            st.error("Please enter a repo name")
        else:
            progress = st.progress(0, text="Fetching files from GitHub...")
            files = fetch_repo_files(repo_name)
            progress.progress(40, text=f"Fetched {len(files)} files. Chunking...")
            chunks = chunk_all_files(files)
            progress.progress(70, text=f"Created {len(chunks)} chunks. Embedding...")
            client = get_chroma_client()
            collection = get_or_create_collection(client, collection_name=repo_name.replace("/", "_"))
            add_chunks_to_store(collection, chunks)
            progress.progress(100, text="Done!")
            st.session_state.collection = collection
            st.session_state.indexed = True
            st.session_state.repo_name_indexed = repo_name
            st.session_state.file_count = len(files)
            st.session_state.chunk_count = len(chunks)
            st.session_state.chat_history = []
            st.success(f"Indexed {repo_name}")
            st.rerun()

    st.divider()
    if st.session_state.indexed:
        st.markdown(f'<span class="am-status-ready">● Ready</span> &nbsp; `{st.session_state.repo_name_indexed}`', unsafe_allow_html=True)
    else:
        st.markdown('<span class="am-status-empty">○ No repo indexed yet</span>', unsafe_allow_html=True)

    st.divider()
    st.markdown("### ℹ️ About")
    st.caption(
        "AgentMap indexes a codebase, understands its component patterns, "
        "and answers questions with grounded, cited sources — built for "
        "the real pain of inheriting an unfamiliar codebase under time pressure."
    )

if st.session_state.indexed:
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f'<div class="am-metric"><div class="val">{st.session_state.file_count}</div><div class="lbl">Files Indexed</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="am-metric"><div class="val">{st.session_state.chunk_count}</div><div class="lbl">Chunks Created</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="am-metric"><div class="val">{len(st.session_state.chat_history)}</div><div class="lbl">Questions Asked</div></div>', unsafe_allow_html=True)
    st.write("")

st.markdown("### 💬 Ask about the codebase")

if not st.session_state.indexed:
    st.info("👈 Index a GitHub repo from the sidebar to start chatting.")
else:
    for msg in st.session_state.chat_history:
        st.markdown(f'<div class="am-user-msg">🧑 {msg["question"]}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="am-bot-msg">🤖 {msg["answer"]}</div>', unsafe_allow_html=True)
        sources_html = "".join(f'<span class="am-source-tag">📄 {s}</span>' for s in msg["sources"])
        st.markdown(sources_html, unsafe_allow_html=True)
        st.write("")

    question = st.chat_input("Ask something about this codebase...")
    if question:
        with st.spinner("Thinking..."):
            result = ask_question(st.session_state.collection, question)
            st.session_state.chat_history.append({
                "question": question, "answer": result["answer"], "sources": result["sources"]
            })
        st.rerun()
