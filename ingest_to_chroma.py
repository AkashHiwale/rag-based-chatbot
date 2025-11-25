"""
Ingest all PDFs from ./pdfs, chunk them, create embeddings (sentence-transformers),
and store into a local Chroma instance at ./chroma_db.

Usage:
1. Put PDFs into ./pdfs
2. python ingest_to_chroma.py
"""

from pathlib import Path
import os
import pdfplumber
from dotenv import load_dotenv

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

load_dotenv()

# Config
PDF_FOLDER = Path("./context")
PERSIST_DIR = "./chroma_db"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"  # fast, free, good for retrieval
CHUNK_SIZE = 1000        # adjust up/down depending on expected answer length
CHUNK_OVERLAP = 200

def extract_text_from_pdf(pdf_path: Path) -> str:
    text_parts = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            # Normalize whitespace
            page_text = page_text.replace("\r", "\n")
            text_parts.append(page_text)
    return "\n\n".join(text_parts)

def pdf_documents_generator(pdf_folder: Path):
    for pdf_file in sorted(pdf_folder.glob("*.pdf")):
        try:
            text = extract_text_from_pdf(pdf_file)
            if not text.strip():
                print(f"[WARN] {pdf_file.name} has no extractable text.")
                continue
            yield {
                "source": str(pdf_file.resolve()),
                "text": text,
                "filename": pdf_file.name
            }
        except Exception as e:
            print(f"[ERROR] Failed to extract {pdf_file}: {e}")

def main():
    if not PDF_FOLDER.exists():
        raise SystemExit(f"Create a folder named {PDF_FOLDER} and put PDFs inside it.")

    # Initialize text splitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", " ", ""]
    )

    # Initialize embeddings (local, free)
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)

    # Initialize or connect to Chroma
    vectordb = Chroma(persist_directory=PERSIST_DIR, embedding_function=embeddings)

    total_chunks = 0
    records_added = 0

    for doc in pdf_documents_generator(PDF_FOLDER):
        source = doc["source"]
        filename = doc["filename"]
        text = doc["text"]

        # Split into chunks
        chunks = text_splitter.split_text(text)

        metadatas = []
        docs = []
        ids = []

        for i, chunk in enumerate(chunks):
            chunk_id = f"{filename}__chunk_{i}"
            ids.append(chunk_id)
            docs.append(chunk)
            metadatas.append({
                "source": source,
                "filename": filename,
                "chunk_index": i
            })

        # add to chroma
        if docs:
            vectordb.add_texts(texts=docs, metadatas=metadatas, ids=ids)
            total_chunks += len(docs)
            records_added += 1
            print(f"[INFO] Added {len(docs)} chunks from {filename}")

    # persist to disk
    vectordb.persist()
    print(f"\n[FINISHED] Documents processed: {records_added}")
    print(f"Total chunks stored: {total_chunks}")
    print(f"Chroma DB persisted at: {os.path.abspath(PERSIST_DIR)}")

if __name__ == "__main__":
    main()
