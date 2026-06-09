"""
Task 6 — Lexical Search Module (BM25).

Mặc định sử dụng BM25. Nếu dùng phương pháp khác (TF-IDF, Elasticsearch,
Weaviate BM25 built-in), hãy giải thích cơ chế trong buổi demo → +5 bonus.

Cài đặt:
    pip install rank-bm25

BM25 hoạt động thế nào:
    - Term Frequency (TF): từ xuất hiện nhiều trong document → điểm cao
    - Inverse Document Frequency (IDF): từ hiếm → quan trọng hơn
    - Document length normalization: document dài không bị ưu tiên quá mức
    - Formula: score(q,d) = Σ IDF(qi) * (tf(qi,d) * (k1+1)) / (tf(qi,d) + k1*(1-b+b*|d|/avgdl))
    - k1=1.5 (term saturation), b=0.75 (length normalization)
"""

import json
import re
from pathlib import Path

try:
    from rank_bm25 import BM25Okapi
    HAS_BM25 = True
except ImportError:
    HAS_BM25 = False

from .task4_chunking_indexing import chunk_documents, load_documents

CORPUS: list[dict] = []
_BM25_INDEX = None
_TOKENIZED_CORPUS: list[list[str]] = []


def _tokenize(text: str) -> list[str]:
    return re.findall(r"\w+", text.lower())


def _build_corpus():
    global CORPUS, _BM25_INDEX, _TOKENIZED_CORPUS
    if CORPUS:
        return CORPUS

    documents = load_documents()
    if not documents:
        return []

    CORPUS = chunk_documents(documents)
    if not CORPUS:
        return CORPUS

    if HAS_BM25:
        _TOKENIZED_CORPUS = [_tokenize(doc["content"]) for doc in CORPUS]
        _BM25_INDEX = BM25Okapi(_TOKENIZED_CORPUS)
    return CORPUS


def build_bm25_index(corpus: list[dict]):
    if not HAS_BM25:
        raise ImportError("rank_bm25 is not installed")
    tokenized_corpus = [_tokenize(doc["content"]) for doc in corpus]
    return BM25Okapi(tokenized_corpus)


def lexical_search(query: str, top_k: int = 10) -> list[dict]:
    corpus = _build_corpus()
    if not corpus:
        return []

    query_tokens = _tokenize(query)
    if not query_tokens:
        return []

    scores = []
    if HAS_BM25 and _BM25_INDEX is not None:
        scores = _BM25_INDEX.get_scores(query_tokens)
    else:
        for doc in corpus:
            doc_tokens = _tokenize(doc["content"])
            scores.append(sum(doc_tokens.count(token) for token in query_tokens))

    results = []
    for idx, score in enumerate(scores):
        if score <= 0:
            continue
        results.append(
            {
                "content": corpus[idx]["content"],
                "score": float(score),
                "metadata": {**corpus[idx].get("metadata", {}), "source": "lexical"},
            }
        )

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]


if __name__ == "__main__":
    results = lexical_search("Điều 248 tàng trữ trái phép chất ma tuý", top_k=5)
    for r in results:
        print(f"[{r['score']:.3f}] {r['content'][:100]}...")
