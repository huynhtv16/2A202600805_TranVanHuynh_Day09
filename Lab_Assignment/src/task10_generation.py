"""
Task 10 — Generation Có Citation.

Hướng dẫn:
    1. Chọn top_k, top_p phù hợp (giải thích lý do)
    2. Sắp xếp lại chunks sau reranking để tránh "lost in the middle"
    3. Inject context vào prompt
    4. Yêu cầu LLM trả lời có citation
    5. Nếu không đủ evidence → "I cannot verify this information"
"""

import os
import re
from dotenv import load_dotenv

load_dotenv()

from .task9_retrieval_pipeline import retrieve

TOP_K = 5
TOP_P = 0.9
TEMPERATURE = 0.3

SYSTEM_PROMPT = """Answer the following question comprehensively in Vietnamese.
For every statement of fact or claim, immediately insert a citation in brackets
linking to the specific source (e.g., [Luật Phòng chống ma tuý 2021, Điều 3]
or [VnExpress, 2024]).

If the information is not explicitly stated in the provided context or knowledge
base, state 'Tôi không thể xác minh thông tin này từ nguồn hiện có' rather than
guessing.

Rules:
- Only use information from the provided context
- Every factual claim MUST have a citation
- If context is insufficient, say so clearly
- Structure your answer with clear paragraphs"""


def _tokenize(text: str) -> list[str]:
    return re.findall(r"\w+", text.lower())


def reorder_for_llm(chunks: list[dict]) -> list[dict]:
    if len(chunks) <= 2:
        return chunks

    reordered = []
    for i in range(0, len(chunks), 2):
        reordered.append(chunks[i])
    for i in range(len(chunks) - 1, 0, -2):
        reordered.append(chunks[i])
    return reordered


def format_context(chunks: list[dict]) -> str:
    context_parts = []
    for idx, chunk in enumerate(chunks, start=1):
        metadata = chunk.get("metadata", {})
        source = metadata.get("source", f"Source {idx}")
        doc_type = metadata.get("type", "unknown")
        chunk_id = metadata.get("chunk_id", f"chunk_{idx}")
        context_parts.append(
            f"[Document {idx} | Source: {source} | Type: {doc_type} | ID: {chunk_id}]\n{chunk['content']}"
        )
    return "\n\n---\n\n".join(context_parts)


def build_citation_answer(query: str, chunks: list[dict], top_k: int = TOP_K) -> str:
    if not chunks:
        return "Tôi không thể xác minh thông tin này từ nguồn hiện có."

    reordered = reorder_for_llm(chunks[:top_k])
    query_tokens = set(_tokenize(query))
    selected_sentences = []

    for chunk in reordered:
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", chunk["content"]) if s.strip()]
        scored_sentences = []
        for sentence in sentences:
            score = sum(1 for token in query_tokens if token in sentence.lower())
            if score > 0:
                scored_sentences.append((score, sentence))

        if scored_sentences:
            best_sentence = max(scored_sentences, key=lambda x: x[0])[1]
            source = chunk.get("metadata", {}).get("source", "Unknown")
            selected_sentences.append((best_sentence, source))

    if not selected_sentences:
        for chunk in reordered:
            first_sentence = chunk["content"].split("\n")[0].strip()
            if first_sentence:
                source = chunk.get("metadata", {}).get("source", "Unknown")
                selected_sentences.append((first_sentence, source))

    if not selected_sentences:
        return "Tôi không thể xác minh thông tin này từ nguồn hiện có."

    answer_lines = [
        "Dựa trên các tài liệu thu thập được, tôi tổng hợp như sau:",
    ]
    seen = set()
    for sentence, source in selected_sentences:
        normalized = re.sub(r"\s+", " ", sentence).strip()
        normalized_key = normalized.lower()
        if normalized_key in seen:
            continue
        seen.add(normalized_key)
        if len(normalized) > 280:
            normalized = normalized[:280].rstrip() + "..."
        answer_lines.append(f"- {normalized} [{source}]")

    return "\n".join(answer_lines)


def generate_with_citation(query: str, top_k: int = TOP_K) -> dict:
    chunks = retrieve(query, top_k=top_k)
    if not chunks:
        return {
            "answer": "Tôi không thể xác minh thông tin này từ nguồn hiện tại.",
            "sources": [],
            "retrieval_source": "none",
        }

    answer = build_citation_answer(query, chunks, top_k=top_k)
    return {
        "answer": answer,
        "sources": chunks,
        "retrieval_source": chunks[0].get("source", "hybrid"),
    }


if __name__ == "__main__":
    test_queries = [
        "Hình phạt cho tội tàng trữ trái phép chất ma tuý theo pháp luật Việt Nam?",
        "Những nghệ sĩ nào đã bị bắt vì liên quan tới ma tuý?",
        "Quy trình cai nghiện bắt buộc theo Luật Phòng chống ma tuý 2021?",
    ]

    for q in test_queries:
        print(f"\n{'='*70}")
        print(f"Q: {q}")
        print("=" * 70)
        result = generate_with_citation(q)
        print(f"\nA: {result['answer']}")
        print(f"\n[Sources: {len(result['sources'])} chunks | via {result['retrieval_source']}]")
