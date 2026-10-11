#!/usr/bin/env python3
"""
build_index.py (Multi-Format Support)

Builds an in-memory vector index from a corpus of documents (.txt, .json, .docx, .pdf).
Includes all necessary logic for chunking, embedding, and indexing.

Usage:
    python scripts/build_index.py --corpus data/corpus \
        --size 300 --overlap 30 --out data/embeddings_small.json
"""


import argparse
import json
import os

from pathlib import Path
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from settings import Settings

import sys
print("Python is looking in these places:", sys.path)

load_dotenv()

_settings = Settings()

# ─── Dependencies & Setup ──────────────────────────────────────────────
try:
    from openai import OpenAI
    import numpy as np
except ImportError:
    print("Error: Missing core dependencies. Please install:")
    print("  pip install openai numpy python-dotenv")
    sys.exit(1)

# Optional Dependencies for file parsing
try:
    import PyPDF2 as pypdf2
except ImportError:
    print("Warning: 'PyPDF2' not found. PDF support will be disabled.")
    pypdf2 = None

try:
    from docx import Document as DocxDocument
except ImportError:
    print("Warning: 'python-docx' not found. DOCX support will be disabled.")
    DocxDocument = None

# Configuration
EMBED_MODEL = _settings.emebedding_model
_client = OpenAI()

def assert_api_key():
    if not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError(
            "Environment variable OPENAI_API_KEY is missing. \n"
            "Please run: export OPENAI_API_KEY='your-key-here'"
        )

# ─── File Parsing Logic (New!) ────────────────────────────────────────

def extract_text_from_file(file_path: Path) -> Optional[str]:
    """Extracts text from .txt, .json, .docx, or .pdf files."""
    
    ext = file_path.suffix.lower()
    content = None
    
    try:
        if ext == '.txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

        elif ext == '.json':
            # Handle JSON files that might contain a list of docs or raw text
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, str):
                content = data
            elif isinstance(data, dict) and "transcript" in data:
                content = data["transcript"]
            elif isinstance(data, list):
                # If it's a list of docs, join them with newlines for now
                # Or return None to let the main loop handle individual items?
                # For this script, we assume JSON files are lists of documents.
                # We will return a special marker or handle in load_corpus.
                # Actually, better strategy: Return the list itself and handle in caller.
                content = data 
            else:
                print(f"Warning: Unexpected JSON structure in {file_path}")

        elif ext == '.docx':
            if DocxDocument is None:
                raise ImportError("python-docx not installed")
            doc = DocxDocument(file_path)
            paragraphs = [p.transcript for p in doc.paragraphs]
            content = "\n".join(paragraphs)

        elif ext == '.pdf':
            if pypdf2 is None:
                raise ImportError("pypdf2 not installed")
            reader = pypdf2.PdfReader(file_path)
            text_parts = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
            content = "\n".join(text_parts)

        else:
            print(f"Warning: Unsupported file format '{ext}' skipped: {file_path}")
            
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    
    return content

# ─── Chunking Logic (Copied from wk06_pipeline) ────────────────────────

def chunk_text(text: str, size: int = 200, overlap: int = 40) -> List[str]:
    if len(text) <= size:
        return [text]
    
    chunks = []
    i = 0
    while i < len(text):
        end = min(i + size, len(text))
        chunks.append(text[i:end])
        
        if end == len(text):
            break
        
        i = end - overlap
    return chunks

def chunk_documents(documents: List[Dict[str, Any]], size: int = 200, overlap: int = 40) -> List[Dict[str, Any]]:
    all_chunks = []
    for doc in documents:
        text_content = doc.get("text", "")
        doc_id = doc.get("id", "unknown")
        
        # If the document is a single string (from txt/pdf/docx), wrap it
        if isinstance(text_content, str):
            chunks = chunk_text(text_content, size, overlap)
            for idx, chunk in enumerate(chunks):
                all_chunks.append({
                    "chunk_id": f"{doc_id}#{idx}",
                    "source_id": doc_id,
                    "source_file": doc.get("source_file", doc_id),
                    "text": chunk,
                })
        elif isinstance(text_content, list):
            # Handle case where JSON returned a list of docs directly
            for sub_doc in text_content:
                sub_text = sub_doc.get("text", "")
                sub_id = sub_doc.get("id", doc_id)
                chunks = chunk_text(sub_text, size, overlap)
                for idx, chunk in enumerate(chunks):
                    all_chunks.append({
                        "chunk_id": f"{sub_id}#{idx}",
                        "source_id": sub_id,
                        "source_file": doc.get("source_file", doc_id),
                        "text": chunk,
                    })
    return all_chunks

# ─── Embedding Logic (Copied from wk06_pipeline) ──────────────────────

def embed_batch(texts: List[str], model: str = EMBED_MODEL) -> List[List[float]]:
    if not texts:
        return []
    
    resp = _client.embeddings.create(model=model, input=texts)
    return [item.embedding for item in resp.data]

def build_index(chunks: List[Dict[str, Any]], model: str = EMBED_MODEL) -> List[Dict[str, Any]]:
    texts = [c["text"] for c in chunks]
    
    BATCH_SIZE = 100 
    all_vectors = []
    
    for i in range(0, len(texts), BATCH_SIZE):
        batch_texts = texts[i : i + BATCH_SIZE]
        batch_vectors = embed_batch(batch_texts, model=model)
        all_vectors.extend(batch_vectors)

    for chunk, vec in zip(chunks, all_vectors):
        chunk["vector"] = vec
        
    return chunks

# ─── Corpus Loading Logic (Updated for Multi-Format) ──────────────────

def load_corpus(corpus_path: str) -> List[Dict[str, Any]]:
    """
    Loads a corpus from a directory. Supports .txt, .json, .docx, .pdf.
    Returns a list of dictionaries with 'id' and 'text'.
    """
    path = Path(corpus_path)
    documents = []

    if not path.exists():
        raise FileNotFoundError(f"Corpus path not found: {corpus_path}")

    print(f"Scanning directory for supported files: {path}")
    
    # Supported extensions
    supported_exts = {'.txt', '.json', '.docx', '.pdf'}
    
    all_files = [f for f in path.iterdir() if f.is_file()]
    matching_files = [f for f in all_files if f.suffix.lower() in supported_exts]

    if not matching_files:
        raise FileNotFoundError(f"No supported files (.txt, .json, .docx, .pdf) found in {corpus_path}")

    print(f"Found {len(matching_files)} files to process.")

    for file in sorted(matching_files):
        raw_content = extract_text_from_file(file)
        
        if raw_content is None:
            continue
            
        # Handle JSON lists specifically
        if isinstance(raw_content, list):
            # If the JSON file contained a list of docs, add them directly
            for item in raw_content:
                if isinstance(item, dict) and "text" in item:
                    documents.append({
                        "id": item.get("id", str(file.stem)),
                        "source_file": file.name,
                        "text": item["text"]
                    })
        else:
            # For txt, docx, pdf (and simple JSON strings), treat as one document
            if isinstance(raw_content, str):
                documents.append({
                    "id": file.stem, # Filename without extension
                    "source_file": file.name,
                    "text": raw_content
                })

    print(f"Loaded {len(documents)} raw documents.")
    return documents

# ─── Main Execution ────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Build a vector index from mixed-format text corpus."
    )
    
    parser.add_argument("--corpus", type=str, required=True, help="Path to corpus directory.")
    parser.add_argument("--size", type=int, default=200, help="Chunk size (chars).")
    parser.add_argument("--overlap", type=int, default=40, help="Overlap (chars).")
    parser.add_argument(
        "--out",
        type=str,
        required=True,
        help="Output directory for per-source embedding JSON files.",
    )

    args = parser.parse_args()

    try:
        assert_api_key()
    except RuntimeError as e:
        print(f"❌ {e}")
        sys.exit(1)

    output_dir = Path(args.out)
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        # 1. Load & Parse Documents (Multi-format)
        documents = load_corpus(args.corpus)
        
        if not documents:
            raise ValueError("No valid documents found after parsing.")

        # 2. Chunking
        print(f"Chunking text (size={args.size}, overlap={args.overlap})...")
        chunks = chunk_documents(documents, size=args.size, overlap=args.overlap)
        print(f"Created {len(chunks)} chunks.")

        # 3. Embedding & Indexing
        print(f"Generating embeddings using model: {EMBED_MODEL}...")
        index = build_index(chunks, model=EMBED_MODEL)
        
        # 4. Save each source file's chunks and embeddings separately
        indexes_by_source: Dict[str, List[Dict[str, Any]]] = {}
        for chunk in index:
            source_file = chunk["source_file"]
            indexes_by_source.setdefault(source_file, []).append(chunk)

        for source_file, source_index in indexes_by_source.items():
            output_name = f"{Path(source_file).stem}_embeddings.json"
            output_path = output_dir / output_name
            print(f"Saving {len(source_index)} chunks to {output_path}...")
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(source_index, f, indent=2, ensure_ascii=False)

        print("✅ Index built successfully!")
        
    except Exception as e:
        print(f"❌ Error during index building: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
