import importlib
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

PAGEINDEX_API_KEY = os.getenv("PAGEINDEX_API_KEY", "")
STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"


def upload_documents():
    if not PAGEINDEX_API_KEY:
        print("PAGEINDEX_API_KEY chưa được cấu hình.")
        return

    if importlib.util.find_spec("pageindex") is None:
        print("Thư viện pageindex chưa được cài đặt.")
        return

    try:
        import pageindex
        PageIndex = getattr(pageindex, "PageIndex", None)
        if PageIndex is None:
            print("Không tìm thấy lớp PageIndex trong package pageindex.")
            return

        client = PageIndex(api_key=PAGEINDEX_API_KEY)
        upload = getattr(client, "upload", None)
        if upload is None:
            print("PageIndex client không có phương thức upload.")
            return

        for md_file in sorted(STANDARDIZED_DIR.rglob("*.md")):
            content = md_file.read_text(encoding="utf-8", errors="ignore")
            metadata = {"filename": md_file.name, "type": md_file.parent.name}
            try:
                upload(content=content, metadata=metadata)
                print(f"  ✓ Uploaded: {md_file.name}")
            except Exception as exc:
                print(f"  ⚠ Không upload được {md_file.name}: {exc}")
    except Exception as exc:
        print(f"Upload PageIndex thất bại: {exc}")


def pageindex_search(query: str, top_k: int = 5) -> list[dict]:
    if not PAGEINDEX_API_KEY:
        return []

    if importlib.util.find_spec("pageindex") is None:
        return []

    try:
        import pageindex
        PageIndex = getattr(pageindex, "PageIndex", None)
        if PageIndex is None:
            return []

        client = PageIndex(api_key=PAGEINDEX_API_KEY)
        query_fn = getattr(client, "query", None) or getattr(client, "search", None)
        if query_fn is None:
            return []

        results = query_fn(query=query, top_k=top_k)
        output = []
        for item in results:
            text = getattr(item, "text", None) or getattr(item, "content", None) or str(item)
            score = float(getattr(item, "score", 0.0) or 0.0)
            metadata = getattr(item, "metadata", {}) or {}
            output.append({
                "content": text,
                "score": score,
                "metadata": metadata,
                "source": "pageindex",
            })
        return output
    except Exception:
        return []


if __name__ == "__main__":
    if not PAGEINDEX_API_KEY:
        print("⚠ Hãy set PAGEINDEX_API_KEY trong file .env")
        print("  Đăng ký tại: https://pageindex.ai/")
    else:
        print("Uploading documents...")
        upload_documents()

        print("\nTest query:")
        results = pageindex_search("hình phạt sử dụng ma tuý", top_k=3)
        for r in results:
            print(f"[{r['score']:.3f}] {r['content'][:100]}...")
