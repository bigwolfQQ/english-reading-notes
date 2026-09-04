"""
把資料庫裡的文章匯出成靜態網頁（給 GitHub Pages 這類靜態託管用）。

刻意「不放」完整英文原文和逐段中文翻譯——公開版只放標題翻譯、原文連結、
單字解析、文法重點（附短句引用），避免公開重製整篇有版權的新聞內容。
完整文章的中英對照閱讀＋整篇朗讀，留在 web/app.py 那個私人版本。

用法（見 manage.py）:
  python manage.py export-public
"""
import shutil
from pathlib import Path

import jinja2

import storage

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = PROJECT_ROOT / "public_site" / "templates"
STATIC_SRC_DIR = PROJECT_ROOT / "public_site" / "static"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "docs"


def _public_fields(article: dict) -> dict:
    return {
        "id": article["id"],
        "source_name": article["source_name"],
        "title_en": article["title_en"],
        "title_zh": article["title_zh"],
        "url": article["url"],
        "published_at": (article["published_at"] or article["fetched_at"])[:10],
        "vocab": article["vocab"],
        "grammar": article["grammar"],
    }


def export(output_dir=None) -> int:
    output_dir = Path(output_dir) if output_dir else DEFAULT_OUTPUT_DIR
    articles_dir = output_dir / "articles"
    output_dir.mkdir(parents=True, exist_ok=True)
    articles_dir.mkdir(parents=True, exist_ok=True)

    all_ready = storage.list_articles(limit=1000, only_ready=True)
    # 手動貼上的文章沒有原文網址可查證來源，公開版不收錄（只收有 url 的自動抓取文章）
    articles = [_public_fields(a) for a in all_ready if a.get("url")]

    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=jinja2.select_autoescape(["html"]),
    )

    index_html = env.get_template("index.html").render(
        articles=articles, static_prefix="static/", root_prefix=""
    )
    (output_dir / "index.html").write_text(index_html, encoding="utf-8")

    article_tpl = env.get_template("article.html")
    for article in articles:
        html = article_tpl.render(article=article, static_prefix="../static/", root_prefix="../")
        (articles_dir / f"{article['id']}.html").write_text(html, encoding="utf-8")

    static_dst = output_dir / "static"
    if static_dst.exists():
        shutil.rmtree(static_dst)
    shutil.copytree(STATIC_SRC_DIR, static_dst)

    # GitHub Pages 預設用 Jekyll 處理內容，會忽略底線開頭的檔案/資料夾；
    # 放一個空的 .nojekyll 停用這個行為，避免靜態檔案被漏掉。
    (output_dir / ".nojekyll").write_text("", encoding="utf-8")

    return len(articles)
