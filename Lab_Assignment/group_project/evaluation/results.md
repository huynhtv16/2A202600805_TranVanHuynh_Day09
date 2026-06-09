# RAG Evaluation Results

## Framework sử dụng

> DeepEval-style local scoring (fallback nội bộ nếu chưa cài deepeval)

---

## Overall Scores (Config A: hybrid + rerank)

| Metric | Config A | Config B (dense-only) | Δ |
|--------|----------|----------------------|---|
| Faithfulness | 0.454 | 0.402 | 0.052 |
| Relevance | 0.454 | 0.402 | 0.052 |
| Context Recall | 0.333 | 0.267 | 0.066 |
| Context Precision | 0.2 | 0.16 | 0.04 |
| Average | 0.361 | 0.308 | 0.053 |

---

## A/B Comparison Analysis

**Config A (hybrid + rerank):** Sử dụng semantic + lexical retrieval, rồi reranking để ưu tiên kết quả liên quan nhất.

**Config B (dense-only):** Chỉ dùng semantic search và trả về kết quả theo score ban đầu, không ráp lại.

**Kết luận:** Config A hoạt động tốt hơn về điểm trung bình trên bộ golden dataset.

---

## Worst Performers (Bottom 3)

| # | Question | Relevance | Faithfulness | Recall | Precision |
|---|----------|-----------|--------------|--------|-----------|
| 1 | Yêu cầu đối với tài liệu trong RAG pipeline khi trả lời có citation là gì? | 0.222 | 0.222 | 0.0 | 0.0 |
| 2 | Trong Luật Phòng chống ma tuý 2021, ai có trách nhiệm tổ chức cai nghiện bắt buộc? | 0.25 | 0.25 | 0.0 | 0.0 |
| 3 | Luật Phòng chống ma tuý quy định xử lý hành chính đối với người sử dụng ma tuý lần đầu như thế nào? | 0.25 | 0.25 | 0.0 | 0.0 |

---

## Recommendations

### Cải tiến 1
**Action:** Tăng độ chính xác của generation bằng cách sử dụng một LLM chuyên sâu với prompt rõ ràng và citation.
**Expected impact:** Cải thiện faithfulness và relevance, giảm tình trạng answer trùng lặp hoặc không chính xác.

### Cải tiến 2
**Action:** Thêm reranking tốt hơn hoặc cross-encoder thực sự để phân biệt điểm liên quan.
**Expected impact:** Nâng cao chất lượng top-k risultati và precision của context.

### Cải tiến 3
**Action:** Mở rộng golden dataset với các câu hỏi phức tạp hơn dựa trên văn bản pháp luật và tin tức.
**Expected impact:** Đánh giá sâu hơn, phát hiện các kịch bản thất bại và cải thiện pipeline.
