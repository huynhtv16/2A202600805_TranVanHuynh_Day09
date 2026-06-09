import html
import json
import re
from pathlib import Path

try:
    from markitdown import MarkItDown
    HAS_MARKITDOWN = True
except ImportError:
    HAS_MARKITDOWN = False

LANDING_DIR = Path(__file__).parent.parent / "data" / "landing"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "standardized"


def _strip_html(raw_html: str) -> str:
    text = re.sub(r"(?is)<script.*?>.*?</script>", "", raw_html)
    text = re.sub(r"(?is)<style.*?>.*?</style>", "", text)
    text = re.sub(r"(?s)<!--.*?-->", "", text)
    text = re.sub(r"(?s)<[^>]+>", "", text)
    text = html.unescape(text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def convert_legal_docs():
    """Convert PDF/DOCX files trong data/landing/legal/ sang markdown."""
    legal_dir = LANDING_DIR / "legal"
    output_dir = OUTPUT_DIR / "legal"
    output_dir.mkdir(parents=True, exist_ok=True)

    if not legal_dir.exists():
        print(f"Không tìm thấy thư mục legal: {legal_dir}")
        return

    for filepath in sorted(legal_dir.iterdir()):
        if filepath.suffix.lower() in (".pdf", ".docx", ".doc"):
            print(f"Converting: {filepath.name}")
            output_path = output_dir / f"{filepath.stem}.md"
            if HAS_MARKITDOWN:
                try:
                    md = MarkItDown()
                    result = md.convert(str(filepath))
                    output_path.write_text(result.text_content, encoding="utf-8")
                    print(f"  ✓ Saved: {output_path}")
                    continue
                except Exception as exc:
                    print(f"  ⚠ MarkItDown conversion failed: {exc}. Tạo placeholder thay thế.")

            placeholder = (
                f"# {filepath.stem}\n\n"
                "*Nội dung đã được tạo tự động vì MarkItDown không khả dụng hoặc chuyển đổi thất bại.*\n\n"
                f"**Nguồn gốc:** {filepath.name}\n\n"
                "---\n\n"
                "Nội dung gốc chưa được giải mã đầy đủ trong môi trường hiện tại."
            )
            output_path.write_text(placeholder, encoding="utf-8")
            print(f"  ✓ Saved placeholder: {output_path}")


def convert_news_articles():
    """Convert HTML/JSON crawled articles trong data/landing/news/ sang markdown."""
    news_dir = LANDING_DIR / "news"
    output_dir = OUTPUT_DIR / "news"
    output_dir.mkdir(parents=True, exist_ok=True)

    if not news_dir.exists():
        print(f"Không tìm thấy thư mục news: {news_dir}")
        return

    for filepath in sorted(news_dir.iterdir()):
        if filepath.suffix.lower() in (".html", ".htm"):
            print(f"Converting HTML: {filepath.name}")
            raw = filepath.read_text(encoding="utf-8", errors="ignore")
            title_match = re.search(r"<title>(.*?)</title>", raw, re.IGNORECASE | re.DOTALL)
            title = title_match.group(1).strip() if title_match else filepath.stem
            content = _strip_html(raw)
            output_path = output_dir / f"{filepath.stem}.md"
            markdown = (
                f"# {title}\n\n"
                f"**Source:** {filepath.name}\n\n"
                "---\n\n"
                f"{content}\n"
            )
            output_path.write_text(markdown, encoding="utf-8")
            print(f"  ✓ Saved: {output_path}")

        elif filepath.suffix.lower() == ".json":
            print(f"Converting JSON: {filepath.name}")
            data = json.loads(filepath.read_text(encoding="utf-8"))
            title = data.get("title") or data.get("url") or filepath.stem
            content = data.get("content_markdown") or data.get("content") or ""
            output_path = output_dir / f"{filepath.stem}.md"
            markdown = (
                f"# {title}\n\n"
                f"**Source:** {data.get('url', filepath.name)}\n"
                f"**Crawled:** {data.get('date_crawled', 'N/A')}\n\n"
                "---\n\n"
                f"{content}\n"
            )
            output_path.write_text(markdown, encoding="utf-8")
            print(f"  ✓ Saved: {output_path}")


def convert_all():
    """Convert toàn bộ files."""
    print("=" * 50)
    print("Task 3: Convert to Markdown (MarkItDown)")
    print("=" * 50)

    print("\n--- Legal Documents ---")
    convert_legal_docs()

    print("\n--- News Articles ---")
    convert_news_articles()

    print("✓ Done! Output tại:", OUTPUT_DIR)


if __name__ == "__main__":
    convert_all()
