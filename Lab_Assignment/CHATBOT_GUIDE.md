# 🎯 RAG Chatbot Streamlit - Hướng Dẫn Chạy

## 📋 Yêu cầu

Cài đặt dependencies:
```bash
pip install -r requirements.txt
```

Chắc chắn các package quan trọng:
```bash
pip install streamlit google-generativeai python-dotenv
```

## 🔑 Cấu hình API Key

Mở file `.env` và đảm bảo có:
```
GEMINI_API_KEY=AIzaSyAv9CcyIBu22QE8chZhdFq9uRiKCvSQQoA
```

## 🚀 Chạy Chatbot

```bash
streamlit run streamlit_app.py
```

Browser sẽ tự động mở tại `http://localhost:8501`.

## 💬 Sử dụng Chatbot

1. **Nhập câu hỏi** vào ô chat ở dưới cùng
2. **Xem câu trả lời** có citation từ Gemini
3. **Click "Xem sources"** để xem tài liệu gốc được retrieval
4. **Đặt câu hỏi tiếp theo** - chatbot tự động nhớ conversation history

## ⚙️ Tùy chỉnh (Sidebar)

- **Top K**: Số lượng documents retrieval (3-10, mặc định 5)
- **Temperature**: Độ sáng tạo (0.0-1.0, mặc định 0.3)
- **Top P**: Nucleus sampling (0.0-1.0, mặc định 0.9)
- **Sử dụng Gemini**: Toggle giữa Gemini generate vs extraction đơn giản

## 📊 Xem Kết quả Evaluation

Trong sidebar, click **View Evaluation Results** để xem A/B comparison scores.

## 🐛 Troubleshooting

**Lỗi: "GEMINI_API_KEY chưa được set"**
- Kiểm tra .env có `GEMINI_API_KEY` chưa
- Chạy lại app: `streamlit run streamlit_app.py`

**Lỗi: "google-generativeai chưa cài"**
```bash
pip install google-generativeai
```

**Lỗi: Retrieval không trả về kết quả**
- Kiểm tra `data/standardized/` có markdown files chưa
- Chạy task 3-4 nếu chưa convert/chunk

---

**2 bộ dữ liệu:**
- 📜 **Pháp luật**: Luật Phòng chống ma tuý 2021, Bộ luật Hình sự, Nghị định 105/2021, v.v.
- 📰 **Tin tức**: Các bài báo về ca sĩ, diễn viên liên quan ma tuý

**Pipeline:**
```
Query → Semantic + Lexical Search → Reranking → Gemini Generation → Answer with Citation
```
