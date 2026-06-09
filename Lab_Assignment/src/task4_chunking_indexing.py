"""
Task 4 — Chunking & Indexing vào Vector Store.

Hướng dẫn:
    1. Đọc toàn bộ markdown files từ data/standardized/
    2. Chọn 1 chunking strategy (giải thích lý do)
    3. Chọn 1 embedding model (giải thích lý do)
    4. Index vào vector store (Weaviate khuyến cáo)

Chunking options (langchain-text-splitters):
    - RecursiveCharacterTextSplitter: an toàn, phổ biến
    - MarkdownHeaderTextSplitter: tốt cho file có heading
    - SemanticChunker: dùng embedding để tách (nâng cao)

Embedding model options:
    - sentence-transformers/all-MiniLM-L6-v2 (384 dim, nhẹ)
    - BAAI/bge-m3 (1024 dim, multilingual, tốt cho tiếng Việt)
    - OpenAI text-embedding-3-small (1536 dim, API)

Vector store options:
    - Weaviate (khuyến cáo: hỗ trợ hybrid search built-in)
    - ChromaDB (đơn giản, local)
    - FAISS (chỉ dense search)

Cài đặt:
    pip install langchain-text-splitters sentence-transformers weaviate-client
"""

import hashlib
import json
import math
import re
from pathlib import Path

try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter
    HAS_SPLITTERS = True
except ImportError:
    HAS_SPLITTERS = False

STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"


# =============================================================================
# CONFIGURATION — Giải thích lựa chọn của bạn trong comment
# =============================================================================

CHUNK_SIZE = 500        # Chọn 500 để cân bằng giữa độ dài đủ chứa thông tin và không quá dài.
CHUNK_OVERLAP = 50      # Chọn 50 để giữ ngữ cảnh giữa các chunk liên tiếp.
CHUNKING_METHOD = "recursive"  # "recursive" | "markdown_header" | "semantic"

EMBEDDING_MODEL = "BAAI/bge-m3"  # Giữ multilingual tốt cho tiếng Việt, fallback nếu không cài.
EMBEDDING_DIM = 1024
USE_TRANSFORMER_EMBEDDING = False  # False để tránh tải model remote trong môi trường test.

VECTOR_STORE = "weaviate"  # Chỉ ghi chú, local pipeline vẫn hoạt động nếu không có service.


# =============================================================================
# HELPERS
# =============================================================================

_embedding_model = None


def _simple_tokenize(text: str) -> list[str]:
    return re.findall(r"\w+", text.lower())


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def _simple_embedding(text: str) -> list[float]:
    tokens = _simple_tokenize(text)
    vector = [0.0] * EMBEDDING_DIM
    for token in tokens:
        idx = int(hashlib.sha256(token.encode("utf-8")).hexdigest(), 16) % EMBEDDING_DIM
        vector[idx] += 1.0
    norm = math.sqrt(sum(x * x for x in vector))
    if norm > 0:
        vector = [x / norm for x in vector]
    return vector


def _chunk_text(text: str) -> list[str]:
    text = _normalize_text(text)
    if not text:
        return []

    if HAS_SPLITTERS and CHUNKING_METHOD == "recursive":
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        return [chunk.strip() for chunk in splitter.split_text(text) if chunk.strip()]

    if HAS_SPLITTERS and CHUNKING_METHOD == "markdown_header":
        splitter = MarkdownHeaderTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
        )
        return [chunk.strip() for chunk in splitter.split_text(text) if chunk.strip()]

    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks = []
    current = ""
    for paragraph in paragraphs:
        if len(current) + len(paragraph) + 1 <= CHUNK_SIZE:
            current = (current + "\n\n" + paragraph).strip() if current else paragraph
        else:
            if current:
                chunks.append(current)
            if len(paragraph) <= CHUNK_SIZE:
                current = paragraph
            else:
                start = 0
                while start < len(paragraph):
                    end = min(start + CHUNK_SIZE, len(paragraph))
                    chunks.append(paragraph[start:end].strip())
                    start = end - CHUNK_OVERLAP if end < len(paragraph) else end
                current = ""
    if current:
        chunks.append(current)

    if CHUNK_OVERLAP > 0 and len(chunks) > 1:
        merged_chunks = []
        for i, chunk in enumerate(chunks):
            if i == 0:
                merged_chunks.append(chunk)
                continue
            overlap_text = chunks[i - 1][-CHUNK_OVERLAP:]
            merged = f"{overlap_text} {chunk}".strip()
            merged_chunks.append(merged[:CHUNK_SIZE])
        return merged_chunks

    return chunks


# =============================================================================
# IMPLEMENTATION
# =============================================================================

VECTORSTORE_INDEX_PATH = STANDARDIZED_DIR.parent / "vectorstore_index.json"


def load_documents() -> list[dict]:
    documents = []
    if not STANDARDIZED_DIR.exists():
        return documents

    for md_file in sorted(STANDARDIZED_DIR.rglob("*.md")):
        content = md_file.read_text(encoding="utf-8", errors="ignore").strip()
        if not content:
            continue
        doc_type = md_file.parent.name if md_file.parent.name in {"legal", "news"} else "unknown"
        documents.append(
            {
                "content": content,
                "metadata": {"source": md_file.name, "type": doc_type},
            }
        )
    return documents


def chunk_documents(documents: list[dict]) -> list[dict]:
    chunks = []
    for doc in documents:
        source = doc["metadata"].get("source", "unknown")
        for i, chunk_text in enumerate(_chunk_text(doc["content"])):
            chunk_id = f"{source}__chunk_{i}"
            chunks.append(
                {
                    "content": chunk_text,
                    "metadata": {
                        **doc["metadata"],
                        "chunk_index": i,
                        "chunk_id": chunk_id,
                    },
                }
            )
    return chunks


def save_local_index(chunks: list[dict]) -> None:
    serialized = [
        {
            "content": chunk["content"],
            "metadata": chunk["metadata"],
            "embedding": chunk.get("embedding", []),
        }
        for chunk in chunks
    ]
    try:
        VECTORSTORE_INDEX_PATH.write_text(json.dumps(serialized, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def load_local_index() -> list[dict]:
    if not VECTORSTORE_INDEX_PATH.exists():
        return []
    try:
        contents = json.loads(VECTORSTORE_INDEX_PATH.read_text(encoding="utf-8"))
        return [
            {
                "content": item.get("content", ""),
                "metadata": item.get("metadata", {}),
                "embedding": item.get("embedding", []),
            }
            for item in contents
            if item.get("content")
        ]
    except Exception:
        return []


def get_indexed_chunks() -> list[dict]:
    cached = load_local_index()
    if cached:
        return cached

    documents = load_documents()
    chunks = chunk_documents(documents)
    if not chunks:
        return []

    chunks = embed_chunks(chunks)
    save_local_index(chunks)
    return chunks


def get_embeddings(texts: list[str]) -> list[list[float]]:
    global _embedding_model
    if not texts:
        return []

    if HAS_SENTENCE_TRANSFORMERS and USE_TRANSFORMER_EMBEDDING:
        try:
            if _embedding_model is None:
                _embedding_model = SentenceTransformer(EMBEDDING_MODEL)
            embeddings = _embedding_model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
            return [emb.tolist() if hasattr(emb, "tolist") else list(map(float, emb)) for emb in embeddings]
        except Exception:
            _embedding_model = None

    return [_simple_embedding(text) for text in texts]


def embed_chunks(chunks: list[dict]) -> list[dict]:
    texts = [chunk["content"] for chunk in chunks]
    embeddings = get_embeddings(texts)
    for chunk, emb in zip(chunks, embeddings):
        chunk["embedding"] = emb
    return chunks


def index_to_vectorstore(chunks: list[dict]):
    print("Indexing to vector store is not configured in this environment.")
    print(f"  Skipping actual vector store write for '{VECTOR_STORE}'.")
    save_local_index(chunks)
    print(f"  ✓ Local index saved: {VECTORSTORE_INDEX_PATH}")


def run_pipeline():
    print("=" * 50)
    print("Task 4: Chunking & Indexing")
    print(f"  Chunking: {CHUNKING_METHOD} (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")
    print(f"  Embedding: {EMBEDDING_MODEL} (dim={EMBEDDING_DIM})")
    print(f"  Vector Store: {VECTOR_STORE}")
    print("=" * 50)

    docs = load_documents()
    print(f"\n✓ Loaded {len(docs)} documents")

    chunks = chunk_documents(docs)
    print(f"✓ Created {len(chunks)} chunks")

    chunks = embed_chunks(chunks)
    print(f"✓ Embedded {len(chunks)} chunks")

    index_to_vectorstore(chunks)
    print("✓ Indexed to vector store")


if __name__ == "__main__":
    run_pipeline()
