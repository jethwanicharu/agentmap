from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from src.retrieval.rag_chain import get_llm, format_context, RAG_PROMPT_TEMPLATE


class AgentState(TypedDict):
    question: str
    collection: Any
    n_results: int
    context: str
    sources: List[str]
    answer: str


def retrieve_node(state: AgentState) -> AgentState:
    """Retriever Agent: pulls relevant code chunks from ChromaDB."""
    query_results = state["collection"].query(
        query_texts=[state["question"]],
        n_results=state.get("n_results", 5)
    )
    context = format_context(query_results)
    sources = list(set(meta["path"] for meta in query_results["metadatas"][0]))
    return {**state, "context": context, "sources": sources}


def generate_node(state: AgentState) -> AgentState:
    """Answer Agent: generates a grounded answer from retrieved context."""
    prompt = ChatPromptTemplate.from_template(RAG_PROMPT_TEMPLATE)
    llm = get_llm()
    parser = StrOutputParser()
    chain = prompt | llm | parser
    answer = chain.invoke({"context": state["context"], "question": state["question"]})
    return {**state, "answer": answer}


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("generate", generate_node)
    graph.set_entry_point("retrieve")
    graph.add_edge("retrieve", "generate")
    graph.add_edge("generate", END)
    return graph.compile()


_compiled_graph = None


def get_graph():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_graph()
    return _compiled_graph


def run_agent(collection, question: str, n_results: int = 5) -> Dict[str, Any]:
    """Public entrypoint — same signature/return shape as old ask_question(),
    so Streamlit UI needs almost no change."""
    graph = get_graph()
    result = graph.invoke({
        "question": question,
        "collection": collection,
        "n_results": n_results,
        "context": "",
        "sources": [],
        "answer": ""
    })
    return {"answer": result["answer"], "sources": result["sources"]}