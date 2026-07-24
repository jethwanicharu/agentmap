import streamlit as st
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from src.ingestion.github_fetcher import fetch_repo_files
from src.chunking.chunker import chunk_all_files
from src.embeddings.vector_store import get_chroma_client, get_or_create_collection, add_chunks_to_store
from src.agents.graph import run_agent as ask_question

st.set_page_config(
    page_title="AgentMap",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background: #0b0d12; }
    section[data-testid="stSidebar"] { background: #0f1117; border-right: 1px solid #1e2129; }

    /* Header */
    .am-header {
        padding: 1.4rem 1.6rem;
        border-radius: 10px;
        background: #12141b;
        border: 1px solid #1e2129;
        margin-bottom: 1.5rem;
    }
    .am-header h1 {
        color: #e6e8eb;
        font-size: 1.5rem;
        font-weight: 700;
        margin: 0;
        letter-spacing: -0.3px;
    }
    .am-header p {
        color: #8b8f9a;
        font-size: 0.88rem;
        margin: 0.3rem 0 0 0;
        font-weight: 400;
    }
    .am-tags { margin-top: 0.7rem; }
    .am-tag {
        display: inline-block;
        background: transparent;
        color: #6b7280;
        border: 1px solid #262a35;
        padding: 2px 10px;
        border-radius: 4px;
        font-size: 0.7rem;
        font-family: 'JetBrains Mono', monospace;
        margin: 2px 6px 0 0;
        letter-spacing: 0.2px;
    }

    /* Metrics */
    .am-metric {
        background: #12141b;
        border: 1px solid #1e2129;
        border-radius: 8px;
        padding: 0.9rem 1.1rem;
    }
    .am-metric .val { font-size: 1.4rem; font-weight: 700; color: #e6e8eb; }
    .am-metric .lbl { font-size: 0.72rem; color: #6b7280; font-weight: 500; text-transform: uppercase; letter-spacing: 0.4px; margin-top: 2px; }

    /* Chat */
    .am-user-msg {
        background: #161922;
        border-radius: 8px;
        padding: 0.75rem 1rem;
        margin: 0.35rem 0;
        color: #d6d8dd;
        max-width: 85%;
        margin-left: auto;
        border: 1px solid #1e2129;
        font-size: 0.92rem;
    }
    .am-bot-msg {
        background: #0f1117;
        border-radius: 8px;
        padding: 0.85rem 1rem;
        margin: 0.35rem 0;
        color: #c7cad1;
        max-width: 92%;
        border: 1px solid #1a1d26;
        font-size: 0.92rem;
        line-height: 1.55;
    }
    .am-source-tag {
        display: inline-block;
        background: transparent;
        color: #7c8591;
        border: 1px solid #262a35;
        padding: 2px 9px;
        border-radius: 4px;
        font-size: 0.7rem;
        font-family: 'JetBrains Mono', monospace;
        margin: 4px 5px 0 0;
    }

    /* Buttons + inputs */
    .stButton > button {
        background: #1c2029;
        color: #e6e8eb;
        border: 1px solid #2a2f3a;
        border-radius: 6px;
        font-weight: 500;
        font-size: 0.88rem;
        padding: 0.45rem 1rem;
        transition: all 0.15s ease;
    }
    .stButton > button:hover {
        background: #23283333;
        border-color: #3a4050;
    }
    .stTextInput > div > div > input {
        background: #12141b;
        border: 1px solid #262a35;
        border-radius: 6px;
        color: #e6e8eb;
        font-size: 0.88rem;
    }

    .am-status-ready { color: #4ade80; font-weight: 500; font-size: 0.82rem; }
    .am-status-empty { color: #8b8f9a; font-weight: 500; font-size: 0.82rem; }

    div[data-testid="stExpander"] { background: #12141b55; border: 1px solid #1e2129; border-radius: 8px; }
    h3 { color: #d6d8dd !important; font-weight: 600 !important; font-size: 1.05rem !important; }
</style>
""", unsafe_allow_html=True)

for key, default in {
    "indexed": False, "collection": None, "chat_history": [],
    "repo_name_indexed": "", "file_count": 0, "chunk_count": 0,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

st.markdown("""
<div class="am-header">
    <h1>AgentMap</h1>
    <p>Multi-agent RAG assistant for codebase context and consistency checks</p>
    <div class="am-tags">
        <span class="am-tag">LangGraph</span>
        <span class="am-tag">LangChain</span>
        <span class="am-tag">Groq · Llama 3.3 70B</span>
        <span class="am-tag">ChromaDB</span>
    </div>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### Index a repository")
    st.caption("Point AgentMap at any GitHub repo to start asking questions.")
    repo_name = st.text_input("GitHub repo", placeholder="owner/repo", label_visibility="collapsed")

    if st.button("Index repository", use_container_width=True):
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
            progress.progress(100, text="Done")
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
        st.markdown(f'<span class="am-status-ready">● Ready</span>&nbsp;&nbsp;<span style="color:#6b7280; font-family:JetBrains Mono, monospace; font-size:0.8rem;">{st.session_state.repo_name_indexed}</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="am-status-empty">○ No repo indexed yet</span>', unsafe_allow_html=True)

    st.divider()
    st.markdown("### About")
    st.caption(
        "AgentMap indexes a codebase and answers questions with grounded, "
        "cited sources — built for the real pain of inheriting an "
        "unfamiliar codebase under time pressure."
    )

if st.session_state.indexed:
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f'<div class="am-metric"><div class="val">{st.session_state.file_count}</div><div class="lbl">Files indexed</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="am-metric"><div class="val">{st.session_state.chunk_count}</div><div class="lbl">Chunks created</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="am-metric"><div class="val">{len(st.session_state.chat_history)}</div><div class="lbl">Questions asked</div></div>', unsafe_allow_html=True)
    st.write("")

st.markdown("### Ask about the codebase")

if not st.session_state.indexed:
    st.info("Index a GitHub repo from the sidebar to start chatting.")
else:
    for msg in st.session_state.chat_history:
        st.markdown(f'<div class="am-user-msg">{msg["question"]}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="am-bot-msg">{msg["answer"]}</div>', unsafe_allow_html=True)
        sources_html = "".join(f'<span class="am-source-tag">{s}</span>' for s in msg["sources"])
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