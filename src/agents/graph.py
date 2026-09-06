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



def is_file_tree_question(question: str) -> bool:
    keywords = [
        "files", "folders", "directory", "structure",
        "how many files", "list files", "kaun si files",
        "folder", "tree", "sab files", "kitni files"
    ]
    return any(k in question.lower() for k in keywords)


def file_tree_node(state: AgentState) -> AgentState:
    all_data = state["collection"].get()
    paths = sorted(set(
        meta["path"] for meta in all_data["metadatas"]
    ))

    # Tree structure
    tree = {}
    for path in paths:
        parts = path.replace("\\", "/").split("/")
        current = tree
        for part in parts:
            current = current.setdefault(part, {})

   
    def render_tree(node, indent=0):
        lines = []
        for key, children in sorted(node.items()):
            prefix = "  " * indent + ("📁 " if children else "📄 ")
            lines.append(f"{prefix}{key}")
            lines.extend(render_tree(children, indent + 1))
        return lines

    tree_str = "\n".join(render_tree(tree))
    answer = f"**Total files: {len(paths)}**\n\n```\n{tree_str}\n```"

    return {**state, "answer": answer, "sources": paths}


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


#  Router function
def route_question(state: AgentState) -> str:
    if is_file_tree_question(state["question"]):
        return "file_tree"
    return "retrieve"


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("file_tree", file_tree_node) 
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("generate", generate_node)

    # Conditional entry 
    graph.set_conditional_entry_point(
        route_question,
        {
            "file_tree": "file_tree",
            "retrieve": "retrieve"
        }
    )

    graph.add_edge("file_tree", END)           
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