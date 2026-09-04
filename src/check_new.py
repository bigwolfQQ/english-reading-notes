"""
主排程：抓 RSS 找新文章 -> 下載內文 -> 翻譯/解析 -> 存進資料庫。

用法:
  python src/check_new.py
"""
import datetime as dt
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import analyzer
import fetcher
import storage
from sources import SOURCE_BY_KEY, SOURCES

ENV_PATH = Path(__file__).resolve().parent.parent / "config" / ".env"


def _load_env_file():
    if not ENV_PATH.exists():
        return
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def discover_new_articles() -> int:
    """掃過所有 RSS 來源，把還沒看過的文章存成 pending，回傳新發現的篇數。"""
    seen = storage.known_urls()
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    found = 0
    for source in SOURCES:
        try:
            entries = fetcher.list_new_entries(source, seen)
        except Exception as e:
            print(f"[{source.name}] 抓 RSS 失敗：{e}")
            continue
        for entry in entries:
            storage.insert_pending(
                source.key, source.name, entry["url"], entry["title"],
                entry["published_at"], now,
            )
            found += 1
    return found


def process_pending(max_articles: int) -> int:
    """把 pending 的文章下載內文（手動貼上的已經有內文）、送去翻譯解析，最多處理 max_articles 篇。"""
    pending = storage.list_pending(max_articles)
    processed = 0
    for article in pending:
        try:
            if article.get("body_en_json"):
                paragraphs = json.loads(article["body_en_json"])
            else:
                source = SOURCE_BY_KEY.get(article["source_key"])
                if source is None:
                    storage.mark_error(article["id"], f"未知來源 {article['source_key']}")
                    continue
                paragraphs = fetcher.fetch_body(source, article["url"])
            if not paragraphs:
                storage.mark_error(article["id"], "抓不到文章內文（網站版面可能改了）")
                continue

            result = analyzer.analyze(article["title_en"], paragraphs)
            storage.save_analysis(
                article["id"], result["title_zh"], paragraphs, result["body"],
                result["vocab"], result["grammar"],
            )
            processed += 1
            print(f"已完成：[{article['source_name']}] {article['title_en']}")
        except Exception as e:
            storage.mark_error(article["id"], str(e))
            print(f"處理失敗：[{article['source_name']}] {article['title_en']}：{e}")
    return processed


def main():
    _load_env_file()
    max_articles = int(os.environ.get("MAX_ARTICLES_PER_RUN", "8"))

    found = discover_new_articles()
    if found:
        print(f"發現 {found} 篇新文章")

    processed = process_pending(max_articles)
    if processed:
        print(f"本次完成翻譯/解析 {processed} 篇")

    remaining = storage.count_pending()
    if remaining:
        print(f"還有 {remaining} 篇排隊，留到下次排程處理")


if __name__ == "__main__":
    main()
