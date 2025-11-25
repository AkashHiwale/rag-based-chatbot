# chat_app_full_response_pane.py
# Streamlit interactive chat for RAG + Groq with explicit Response pane
# Run: streamlit run chat_app_full_response_pane.py

import os
from dotenv import load_dotenv
import streamlit as st

# LangChain modular imports
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_groq import ChatGroq

load_dotenv()

# -------------------- CONFIG --------------------
PERSIST_DIR = "./chroma_db"              # must exist from ingestion step
EMBEDDING_MODEL = "all-MiniLM-L6-v2"     # same model used during ingestion
GROQ_MODEL = "llama-3.3-70b-versatile"   # your Groq model
DEFAULT_TOP_K = 5
DEFAULT_TEMP = 0.0

# -------------------- HELPERS --------------------
def load_retriever(k: int):
    emb = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    db = Chroma(persist_directory=PERSIST_DIR, embedding_function=emb)
    retriever = db.as_retriever(search_type="similarity", search_kwargs={"k": k})
    return retriever

def build_context_from_docs(docs, per_chunk_chars=800, char_limit=4000):
    parts = []
    total_len = 0
    for d in docs:
        md = d.metadata or {}
        fname = md.get("filename", md.get("source", "unknown"))
        chunk_idx = md.get("chunk_index", "0")
        content = d.page_content.strip().replace("\n", " ")
        if len(content) > per_chunk_chars:
            content = content[:per_chunk_chars] + "..."
        citation = f"[{fname}::chunk_{chunk_idx}]"
        snippet = f"{citation}\n{content}"
        parts.append(snippet)
        total_len += len(snippet)
        if total_len > char_limit:
            break
    return "\n\n---\n\n".join(parts)

def ask_groq_with_context(query: str, docs, groq_api_key: str, model_name: str, temperature: float):
    context = build_context_from_docs(docs)
    prompt = f"""
You are a helpful log-analysis assistant. Use ONLY the information in the provided CONTEXT to answer the user's query.
If the answer is not present in the CONTEXT, reply exactly: "Information not found in context." Also add more meaningful response based on input query.

CONTEXT:
{context}

USER QUERY:
{query}

INSTRUCTIONS:
- Answer concisely (2-6 sentences).
- If suggesting debugging steps, list concrete ordered steps.

Answer:
"""
    llm = ChatGroq(groq_api_key=groq_api_key, model_name=model_name, temperature=temperature)
    resp = llm.invoke(prompt)
    return resp.content

# -------------------- STREAMLIT APP --------------------
st.set_page_config(page_title="RAG Chat (Groq + Chroma)", layout="wide")
st.title("RAG Chat — Log Analyzer")

# Initialize session state keys BEFORE widgets
if "messages" not in st.session_state:
    st.session_state.messages = []  # list of {"role","text","sources"}
if "user_input" not in st.session_state:
    st.session_state.user_input = ""
# last_response holds the most recent assistant answer to show in the right pane
if "last_response" not in st.session_state:
    st.session_state.last_response = ""
if "last_sources" not in st.session_state:
    st.session_state.last_sources = []
# store settings in session_state to access inside callbacks
if "top_k" not in st.session_state:
    st.session_state.top_k = DEFAULT_TOP_K
if "temp" not in st.session_state:
    st.session_state.temp = float(DEFAULT_TEMP)

# Sidebar controls (keys map to session_state so callbacks can read them)
with st.sidebar:
    st.header("Settings")
    st.slider("Top-K (retrieval)", min_value=1, max_value=12, value=st.session_state.top_k, key="top_k")
    st.slider("Temperature", min_value=0.0, max_value=1.0, value=st.session_state.temp, step=0.05, key="temp")
    st.markdown("---")
    def clear_chat():
        st.session_state.messages = []
        st.session_state.last_response = ""
        st.session_state.last_sources = []
    st.button("Clear chat", on_click=clear_chat)

st.markdown("Ask questions about your logs and system design documents. The assistant will retrieve context from Chroma and answer using Groq.")

# ---- callback to handle sending message ----
def handle_send():
    query = st.session_state.user_input.strip()
    if not query:
        return

    groq_key = os.getenv("GROQ_API_KEY")
    if not groq_key:
        st.session_state.last_response = "Missing GROQ_API_KEY in environment. Set it in .env and restart the app."
        st.session_state.last_sources = []
        st.session_state.user_input = ""
        return

    # read settings from session_state
    k = int(st.session_state.get("top_k", DEFAULT_TOP_K))
    temp = float(st.session_state.get("temp", DEFAULT_TEMP))

    # Retrieval
    try:
        retriever = load_retriever(k=k)
        docs = retriever.invoke(query)
    except Exception as e:
        st.session_state.last_response = f"Retriever error: {e}"
        st.session_state.last_sources = []
        st.session_state.user_input = ""
        return

    if not docs:
        assistant_text = "Information not found in context."
        sources = []
    else:
        # Call Groq
        try:
            assistant_text = ask_groq_with_context(query=query, docs=docs, groq_api_key=groq_key, model_name=GROQ_MODEL, temperature=temp)
        except Exception as e:
            assistant_text = f"Groq call failed: {e}"
        sources = [d.metadata for d in docs]

    # Append messages (user then assistant)
    st.session_state.messages.append({"role": "user", "text": query})
    st.session_state.messages.append({"role": "assistant", "text": assistant_text, "sources": sources})

    # Set latest response so the right pane shows it immediately after submit
    st.session_state.last_response = assistant_text
    st.session_state.last_sources = sources

    # Clear input safely inside callback
    st.session_state.user_input = ""

# ---- Layout: left = input + history, right = latest response ----
left_col, right_col = st.columns([2, 3])

with left_col:
    st.subheader("Ask a question")
    st.text_area("Enter your message", key="user_input", height=120)
    st.button("Send", on_click=handle_send)

    st.markdown("### Conversation history")
    # show last 50 messages
    for msg in st.session_state.messages[-50:]:
        if msg["role"] == "user":
            st.markdown(f"**You:** {msg['text']}")
        else:
            st.markdown(f"**Assistant:** {msg['text']}")
            if msg.get("sources"):
                refs = ", ".join([f"[{m.get('filename','unknown')}::chunk_{m.get('chunk_index','0')}]" for m in msg["sources"][:6]])
                st.caption(f"Sources: {refs}")
        st.markdown("---")

with right_col:
    st.subheader("Response")
    if st.session_state.last_response:
        st.write(st.session_state.last_response)
        if st.session_state.last_sources:
            st.markdown("**Citations used:**")
            for md in st.session_state.last_sources:
                fname = md.get("filename", md.get("source", "unknown"))
                cidx = md.get("chunk_index", "0")
                st.markdown(f"- [{fname}::chunk_{cidx}]")
    else:
        st.info("Responses will appear here after you submit a query.")

# Footer note
st.caption("Built with Streamlit • Chroma • HuggingFace embeddings • Groq")
