"""
Task 9 — Retrieval Pipeline Hoàn Chỉnh.

Kết hợp semantic search + lexical search + reranking + PageIndex fallback
thành một pipeline thống nhất.

Logic:
    1. Chạy semantic_search + lexical_search song song
    2. Merge kết quả (RRF hoặc weighted fusion)
    3. Rerank
    4. Nếu top result score < threshold → fallback sang PageIndex
    5. Return top_k results
"""

from .task5_semantic_search import semantic_search
from .task6_lexical_search import lexical_search
from .task7_reranking import rerank, rerank_rrf
from .task8_pageindex_vectorless import pageindex_search


SCORE_THRESHOLD = 0.3
DEFAULT_TOP_K = 5
RERANK_METHOD = "cross_encoder"
HYBRID_SOURCE = "hybrid"


def _merge_hybrid_results(dense: list[dict], sparse: list[dict], top_k: int) -> list[dict]:
    if not dense and not sparse:
        return []

    merged = rerank_rrf([dense, sparse], top_k=top_k)
    for item in merged:
        item["source"] = HYBRID_SOURCE
    return merged


def retrieve(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    score_threshold: float = SCORE_THRESHOLD,
    use_reranking: bool = True,
) -> list[dict]:
    if not query:
        return []

    dense_results = semantic_search(query, top_k=top_k * 2)
    sparse_results = lexical_search(query, top_k=top_k * 2)

    merged = _merge_hybrid_results(dense_results, sparse_results, top_k=top_k * 2)
    if use_reranking and merged:
        try:
            final_results = rerank(query, merged, top_k=top_k, method=RERANK_METHOD)
        except Exception:
            final_results = merged[:top_k]
    else:
        final_results = merged[:top_k]

    if not final_results or final_results[0].get("score", 0.0) < score_threshold:
        fallback = pageindex_search(query, top_k=top_k)
        if fallback:
            return fallback

    return final_results[:top_k]


if __name__ == "__main__":
    test_queries = [
        "Hình phạt cho tội tàng trữ trái phép chất ma tuý",
        "Nghệ sĩ nào bị bắt vì sử dụng ma tuý năm 2024",
        "Luật phòng chống ma tuý 2021 quy định gì về cai nghiện",
    ]

    for q in test_queries:
        print(f"\nQuery: {q}")
        print("-" * 60)
        results = retrieve(q, top_k=3)
        for i, r in enumerate(results, 1):
            print(f"  {i}. [{r['score']:.3f}] [{r.get('source', 'unknown')}] {r['content'][:80]}...")
