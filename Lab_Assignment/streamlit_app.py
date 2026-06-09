"""
RAG Chatbot sử dụng Streamlit + Gemini + RAG Pipeline.

Chạy: streamlit run streamlit_app.py
"""

import os
import sys
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

# Setup path
ROOT_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT_DIR))

load_dotenv()

from src.task9_retrieval_pipeline import retrieve
from src.task10_generation import SYSTEM_PROMPT, build_citation_answer, reorder_for_llm, format_context

# Try import Gemini
try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

# ===========================================================================
# PAGE CONFIG
# ===========================================================================

st.set_page_config(
    page_title="Drug Law RAG Chatbot",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("⚖️ Pháp Luật Ma Tuý - RAG Chatbot")
st.markdown("Trả lời câu hỏi về pháp luật phòng chống ma tuý và tin tức liên quan")

# ===========================================================================
# SIDEBAR - CONFIG
# ===========================================================================

with st.sidebar:
    st.header("⚙️ Cấu hình")

    # Check if Gemini is available
    gemini_available = False
    if HAS_GEMINI:
        api_key = os.getenv("GEMINI_API_KEY", "")
        if api_key:
            try:
                genai.configure(api_key=api_key)
                gemini_available = True
            except:
                gemini_available = False
    
    if not gemini_available:
        st.info("💡 **Sử dụng Extraction Mode** (không cần API key). App sẽ extract & format answer từ documents.")
        use_gemini = False
    else:
        use_gemini = st.checkbox("🤖 Thử dùng Gemini (nếu khả dụng)", value=False)

    top_k = st.slider("Top K (retrieval)", 3, 10, 5)
    temperature = st.slider("Temperature", 0.0, 1.0, 0.3)
    top_p = st.slider("Top P", 0.0, 1.0, 0.9)

    st.divider()
    st.markdown("### 📊 Thông tin")
    st.info(
        """
        **2 bộ dữ liệu:**
        - 📜 Pháp luật (từ data/standardized/legal/)
        - 📰 Tin tức (từ data/standardized/news/)

        **Pipeline:**
        1. Semantic + Lexical Search (Hybrid)
        2. Reranking
        3. Generation (Extraction hoặc Gemini LLM)
        """
    )

# ===========================================================================
# SESSION STATE - CONVERSATION MEMORY
# ===========================================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "show_sources" not in st.session_state:
    st.session_state.show_sources = True

if "working_model" not in st.session_state:
    st.session_state.working_model = None

# ===========================================================================
# HELPER FUNCTIONS
# ===========================================================================

def generate_with_gemini(query: str, context_chunks: list[dict], temperature: float, top_p: float) -> str:
    """Generate answer using Gemini API. Returns None if Gemini fails, caller should fallback."""
    if not HAS_GEMINI:
        return None

    try:
        # Try different model names
        model_names = ["gemini-pro", "gemini-1.5-flash", "gemini-1.5-pro"]
        model = None
        
        for model_name in model_names:
            try:
                model = genai.GenerativeModel(model_name)
                st.session_state.working_model = model_name
                break
            except Exception:
                continue
        
        if model is None:
            return None

        reordered = reorder_for_llm(context_chunks)
        context = format_context(reordered)

        full_prompt = f"""{SYSTEM_PROMPT}

---
## CONTEXT

{context}

---
## USER QUESTION

{query}

---
## ANSWER
"""

        response = model.generate_content(
            full_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=temperature,
                top_p=top_p,
                max_output_tokens=1024,
            ),
        )

        return response.text
    except Exception as e:
        # Fallback on any error (model not found, API error, etc)
        return None


def process_query(user_query: str, use_gemini: bool, top_k: int, temperature: float, top_p: float) -> dict:
    """Process user query through RAG pipeline."""
    chunks = retrieve(user_query, top_k=top_k)

    if not chunks:
        return {
            "answer": "❌ Không tìm thấy tài liệu phù hợp",
            "sources": [],
        }

    answer = None
    if use_gemini and HAS_GEMINI:
        answer = generate_with_gemini(user_query, chunks, temperature, top_p)

    if not answer:
        answer = build_citation_answer(user_query, chunks, top_k=top_k)

    return {
        "answer": answer,
        "sources": chunks,
    }


# ===========================================================================
# MAIN CHAT INTERFACE
# ===========================================================================

# Display conversation history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant" and "sources" in msg:
            with st.expander("📄 Xem sources"):
                for i, src in enumerate(msg["sources"], 1):
                    st.markdown(f"**[{i}] {src['metadata'].get('source', 'Unknown')}**")
                    st.markdown(f"> {src['content'][:300]}...")

# Chat input
user_input = st.chat_input("Hỏi về pháp luật ma tuý hoặc tin tức liên quan...")

if user_input:
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Display user message
    with st.chat_message("user"):
        st.markdown(user_input)

    # Process and generate response
    with st.chat_message("assistant"):
        with st.spinner("⏳ Đang xử lý..."):
            result = process_query(
                user_input,
                use_gemini=use_gemini,
                top_k=top_k,
                temperature=temperature,
                top_p=top_p,
            )

        answer = result["answer"]
        st.markdown(answer)

        # Show sources
        if result["sources"] and st.session_state.show_sources:
            st.divider()
            with st.expander("📄 **Xem sources** (click để mở)"):
                for i, src in enumerate(result["sources"], 1):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"**[{i}] {src['metadata'].get('source', 'Unknown')}** ({src['metadata'].get('type', 'unknown')})")
                        st.markdown(f"> {src['content'][:250]}...")
                    with col2:
                        st.metric("Score", f"{src.get('score', 0):.2f}")

    # Add assistant message to history
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": answer,
            "sources": result["sources"],
        }
    )

# ===========================================================================
# FOOTER
# ===========================================================================

st.divider()
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🔄 Clear Conversation"):
        st.session_state.messages = []
        st.rerun()

with col2:
    st.session_state.show_sources = st.checkbox("Show sources by default", value=True)

with col3:
    if st.button("📊 View Evaluation Results"):
        st.info("📌 Xem kết quả đánh giá tại: `group_project/evaluation/results.md`")

st.markdown(
    """
    ---
    **Day 08 RAG Pipeline v2** | Powered by Gemini + Weaviate + Streamlit
    """
)
