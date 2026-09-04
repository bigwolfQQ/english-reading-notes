"""
抓取 RSS 來源的最新文章清單、下載文章頁面並擷取內文段落。
"""
import datetime as dt

import feedparser
import requests
import truststore
from bs4 import BeautifulSoup

from sources import Source

truststore.inject_into_ssl()

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    )
}


def list_new_entries(source: Source, seen_urls: set) -> list:
    """回傳這個來源 RSS 裡，尚未出現在 seen_urls 的文章 (title/url/published_at)。"""
    feed = feedparser.parse(source.rss_url)
    entries = []
    for entry in feed.entries:
        url = entry.get("link", "").strip()
        if not url or url in seen_urls:
            continue
        published = None
        if getattr(entry, "published_parsed", None):
            published = dt.datetime(*entry.published_parsed[:6], tzinfo=dt.timezone.utc)
        entries.append(
            {
                "title": entry.get("title", "").strip(),
                "url": url,
                "published_at": published.isoformat() if published else None,
            }
        )
    return entries


def fetch_body(source: Source, url: str):
    """下載文章頁面並擷取內文段落，抓不到就回傳 None。"""
    resp = requests.get(url, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    # 用 resp.content（原始 bytes）讓 BeautifulSoup 自己從 <meta charset> 偵測編碼；
    # resp.text 會用 requests 猜的編碼，這兩個網站常常被猜錯導致中文人名/引號變亂碼。
    soup = BeautifulSoup(resp.content, "html.parser")
    return source.extract(soup)
