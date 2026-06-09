"""
Task 5 � Semantic Search Module.

Vi?t module t�m ki?m ng? nghia (dense retrieval) tr�n vector store.

Y�u c?u:
    - Input: query string + top_k
    - Output: danh s�ch chunks c� score, sorted descending
    - Ph?i tuong th�ch v?i embedding model v� vector store ? Task 4
"""

from math import sqrt

from .task4_chunking_indexing import get_indexed_chunks, get_embeddings

SEMANTIC_CACHE: list[dict] = []


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sqrt(sum(x * x for x in a))
    norm_b = sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _build_semantic_index() -> list[dict]:
    global SEMANTIC_CACHE
    if SEMANTIC_CACHE:
        return SEMANTIC_CACHE

    chunks = get_indexed_chunks()
    SEMANTIC_CACHE = chunks
    return SEMANTIC_CACHE


def semantic_search(query: str, top_k: int = 10) -> list[dict]:
    if not query:
        return []

    chunks = _build_semantic_index()
    if not chunks:
        return []

    query_embedding = get_embeddings([query])[0]
    scored = []
    for chunk in chunks:
        score = _cosine_similarity(query_embedding, chunk.get("embedding", []))
        scored.append(
            {
                "content": chunk["content"],
                "score": float(score),
                "metadata": chunk["metadata"],
                "source": "semantic",
            }
        )

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_k]


if __name__ == "__main__":
    results = semantic_search("hình phạt cho tội tàng trữ ma túy", top_k=5)
    for r in results:
        print(f"[{r['score']:.3f}] {r['content'][:100]}...")
