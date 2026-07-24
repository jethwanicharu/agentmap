import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

RAG_PROMPT_TEMPLATE = """You are a helpful assistant that answers questions about a codebase.
Use ONLY the following context (code snippets) to answer the question.
If the context doesn't contain enough information, say so — don't make things up.

Context:
{context}

Question: {question}

Answer:"""


def get_llm():
    """
    Initializes the Groq LLM.
    """
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0,  # deterministic answers — important for a code-context tool
        groq_api_key=os.getenv("GROQ_API_KEY")
    )


def format_context(query_results: dict) -> str:
    """
    Formats ChromaDB query results into a readable context string,
    tagging each chunk with its source file path (for citations).
    """
    documents = query_results["documents"][0]
    metadatas = query_results["metadatas"][0]

    context_parts = []
    for doc, meta in zip(documents, metadatas):
        context_parts.append(f"[Source: {meta['path']}]\n{doc}")

    return "\n\n---\n\n".join(context_parts)


def ask_question(collection, question: str, n_results: int = 5):
    """
    Full RAG pipeline: retrieve relevant chunks -> build prompt -> call LLM -> return answer + sources.
    """
    # 1. Retrieve
    query_results = collection.query(query_texts=[question], n_results=n_results)
    context = format_context(query_results)

    # 2. Build prompt
    prompt = ChatPromptTemplate.from_template(RAG_PROMPT_TEMPLATE)
    llm = get_llm()
    parser = StrOutputParser()

    # 3. LCEL chain
    chain = prompt | llm | parser

    # 4. Generate answer
    answer = chain.invoke({"context": context, "question": question})

    # 5. Extract unique source files for citation
    sources = list(set(meta["path"] for meta in query_results["metadatas"][0]))

    return {
        "answer": answer,
        "sources": sources
    }


if __name__ == "__main__":
    from src.embeddings.vector_store import get_chroma_client, get_or_create_collection

    client = get_chroma_client()
    collection = get_or_create_collection(client)

    result = ask_question(collection, "how do I sum a list of numbers?")
    print("Answer:", result["answer"])
    print("Sources:", result["sources"])