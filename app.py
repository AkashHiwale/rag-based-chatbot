"""
Continuous RAG chatbot using Chroma + HuggingFace embeddings + Groq Llama 3.3 70B.

Run:
    python rag_chat_loop.py
"""

import os
from dotenv import load_dotenv

# Embeddings + Vector DB
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# Groq LLM
from langchain_groq import ChatGroq

load_dotenv()

PERSIST_DIR = "./chroma_db"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
GROQ_MODEL = "llama-3.3-70b-versatile"
TOP_K = 5


def load_retriever():
    emb = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    db = Chroma(persist_directory=PERSIST_DIR, embedding_function=emb)
    return db.as_retriever(search_type="similarity", search_kwargs={"k": TOP_K})


def build_context(docs):
    parts = []
    for d in docs:
        md = d.metadata or {}
        filename = md.get("filename", "unknown")
        chunk = md.get("chunk_index", 0)
        content = d.page_content.strip().replace("\n", " ")

        if len(content) > 1000:
            content = content[:1000] + "..."

        citation = f"[{filename}::chunk_{chunk}]"
        parts.append(f"{citation}\n{content}")

    return "\n\n---\n\n".join(parts)


def answer_query(query, retriever, llm):
    docs = retriever.invoke(query)
    if not docs:
        return "No relevant context found."

    context = build_context(docs)

    prompt = f"""
You are a log-analysis assistant. Use ONLY the information from the context.

CONTEXT:
{context}

USER QUESTION:
{query}

RULES:
- Use citations like [filename::chunk].
- If answer not found, say "Information not found in context."

Answer:
"""

    response = llm.invoke(prompt)
    return response.content


def main():
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        raise SystemExit("Missing GROQ_API_KEY in .env")

    retriever = load_retriever()

    llm = ChatGroq(
        groq_api_key=groq_api_key,
        model_name=GROQ_MODEL,
        temperature=0
    )

    print("\n🚀 RAG Log Analyzer Chatbot (Groq + Chroma)")
    print("Type 'exit' to quit.\n")

    while True:
        query = input("Enter your query: ")

        if query.lower() in ["exit", "quit"]:
            print("Exiting chatbot...")
            break

        answer = answer_query(query, retriever, llm)
        print("\n🟦 Answer:")
        print(answer)
        print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    main()
