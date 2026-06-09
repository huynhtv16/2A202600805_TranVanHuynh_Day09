"""
Task 7 — Reranking Module.

Chọn 1 trong các phương pháp:
    - Cross-encoder reranker: Jina Reranker v2 (multilingual) hoặc Qwen3-Reranker
    - MMR (Maximal Marginal Relevance): tự implement
    - RRF (Reciprocal Rank Fusion): tự implement

Nếu dùng MMR hoặc RRF, đảm bảo hiểu và giải thích được cơ chế.
"""

from .task4_chunking_indexing import get_embeddings


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(y * y for y in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def rerank_cross_encoder(
    query: str, candidates: list[dict], top_k: int = 5
) -> list[dict]:
    if not candidates:
        return []

    query_embedding = get_embeddings([query])[0]
    texts = [candidate.get("content", "") for candidate in candidates]
    embeddings = get_embeddings(texts)

    reranked = []
    for candidate, emb in zip(candidates, embeddings):
        relevance = _cosine_similarity(query_embedding, emb)
        base_score = float(candidate.get("score", 0.0))
        score = 0.65 * relevance + 0.35 * base_score
        reranked.append({**candidate, "score": float(score)})

    reranked.sort(key=lambda item: item["score"], reverse=True)
    return [dict(item) for item in reranked[:top_k]]


def rerank_mmr(
    query_embedding: list[float],
    candidates: list[dict],
    top_k: int = 5,
    lambda_param: float = 0.7,
) -> list[dict]:
    if not candidates:
        return []

    for candidate in candidates:
        if not candidate.get("embedding"):
            candidate["embedding"] = get_embeddings([candidate.get("content", "")])[0]

    selected = []
    remaining = list(range(len(candidates)))

    while remaining and len(selected) < min(top_k, len(candidates)):
        best_idx = None
        best_score = float("-inf")

        for idx in remaining:
            relevance = _cosine_similarity(query_embedding, candidates[idx]["embedding"])
            max_similarity = 0.0
            for sel_idx in selected:
                sim = _cosine_similarity(candidates[idx]["embedding"], candidates[sel_idx]["embedding"])
                max_similarity = max(max_similarity, sim)

            mmr_score = lambda_param * relevance - (1 - lambda_param) * max_similarity
            if mmr_score > best_score:
                best_score = mmr_score
                best_idx = idx

        if best_idx is None:
            break

        selected.append(best_idx)
        remaining.remove(best_idx)

    return [candidates[i] for i in selected]


def _merge_key(item: dict) -> str:
    metadata = item.get("metadata", {}) or {}
    if metadata.get("chunk_id"):
        return metadata["chunk_id"]
    if metadata.get("source"):
        return f"{metadata.get('source')}::{item.get('content', '')[:120]}"
    return item.get("content", "")[:200]


def rerank_rrf(
    ranked_lists: list[list[dict]], top_k: int = 5, k: int = 60
) -> list[dict]:
    scores = {}
    best_candidates = {}

    for ranked_list in ranked_lists:
        for rank, item in enumerate(ranked_list, start=1):
            key = _merge_key(item)
            if not key:
                continue
            scores[key] = scores.get(key, 0.0) + 1.0 / (k + rank)
            if key not in best_candidates or item.get("score", 0.0) > best_candidates[key].get("score", 0.0):
                best_candidates[key] = item

    sorted_items = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    results = []
    for key, score in sorted_items[:top_k]:
        item = dict(best_candidates.get(key, {"content": key}))
        item["score"] = float(score)
        results.append(item)
    return results


def rerank(
    query: str,
    candidates: list[dict],
    top_k: int = 5,
    method: str = "cross_encoder",
) -> list[dict]:
    if method == "cross_encoder":
        return rerank_cross_encoder(query, candidates, top_k)
    elif method == "mmr":
        query_embedding = get_embeddings([query])[0]
        return rerank_mmr(query_embedding, candidates, top_k)
    elif method == "rrf":
        if not candidates or not isinstance(candidates[0], list):
            raise ValueError("rrf method expects a list of ranked lists")
        return rerank_rrf(candidates, top_k=top_k)
    else:
        raise ValueError(f"Unknown rerank method: {method}")


if __name__ == "__main__":
    dummy_candidates = [
        {"content": "Điều 248: Tội tàng trữ trái phép chất ma tuý", "score": 0.8, "metadata": {}},
        {"content": "Nghệ sĩ X bị bắt vì sử dụng ma tuý", "score": 0.7, "metadata": {}},
        {"content": "Hình phạt tù từ 2-7 năm cho tội tàng trữ", "score": 0.6, "metadata": {}},
    ]
    results = rerank("hình phạt tàng trữ ma tuý", dummy_candidates, top_k=2)
    for r in results:
        print(f"[{r['score']:.3f}] {r['content']}")
