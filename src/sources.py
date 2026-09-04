"""
文章來源設定：RSS 來源清單 + 各網站的內文擷取方式。

目前用 Taipei Times + Focus Taiwan (CNA 英文新聞)，兩個都有公開 RSS、
文章內文由伺服器端直接輸出（不用登入、沒有反爬蟲防護），適合排程抓取。

CommonWealth Magazine 英文站 (english.cw.com.tw) 掛了 Cloudflare 機器人驗證
（連 curl 都被擋成 "Just a moment..." 驗證頁），也找不到官方 RSS，
硬要繞過防護不合適，故不列入自動化來源。想讀天下雜誌英文版（或其他來源）的文章，
用網頁介面的「手動貼上文章」功能，把瀏覽器上看到的標題和內文貼進去即可，
一樣會走翻譯/單字/文法解析流程（見 web/app.py 的 /add）。
"""
import dataclasses
from typing import Callable, List, Optional

from bs4 import BeautifulSoup


@dataclasses.dataclass
class Source:
    key: str
    name: str
    rss_url: str
    extract: Callable[[BeautifulSoup], Optional[List[str]]]


def _extract_taipei_times(soup: BeautifulSoup) -> Optional[List[str]]:
    container = soup.select_one("div.archives")
    if not container:
        return None
    paragraphs = []
    for p in container.find_all("p"):
        if p.find_parent(class_="imgboxa"):
            continue  # 圖說文字，不是內文
        text = p.get_text(" ", strip=True)
        if text:
            paragraphs.append(text)
    return paragraphs or None


def _extract_focus_taiwan(soup: BeautifulSoup) -> Optional[List[str]]:
    container = soup.select_one("div.paragraph")
    if not container:
        return None
    paragraphs = []
    for p in container.find_all("p"):
        text = p.get_text(" ", strip=True)
        if not text:
            continue
        if text.startswith("(By") or text.startswith("Enditem"):
            continue  # 記者署名/結尾標記，不是內文
        paragraphs.append(text)
    return paragraphs or None


SOURCES = [
    Source(
        key="taipei_times",
        name="Taipei Times",
        rss_url="https://www.taipeitimes.com/xml/index.rss",
        extract=_extract_taipei_times,
    ),
    Source(
        key="focus_taiwan",
        name="Focus Taiwan (CNA)",
        rss_url="https://feeds.feedburner.com/rsscna/engnews",
        extract=_extract_focus_taiwan,
    ),
]

SOURCE_BY_KEY = {s.key: s for s in SOURCES}
