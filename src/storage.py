"""
文章資料儲存（SQLite，單一檔案 data/articles.db）。
"""
import json
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "articles.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_key TEXT NOT NULL,
    source_name TEXT NOT NULL,
    url TEXT UNIQUE,
    title_en TEXT NOT NULL,
    title_zh TEXT,
    published_at TEXT,
    fetched_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    body_en_json TEXT,
    body_json TEXT,
    vocab_json TEXT,
    grammar_json TEXT,
    error_message TEXT,
    is_read INTEGER NOT NULL DEFAULT 0
);
"""


def _connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute(_SCHEMA)
    return conn


def known_urls() -> set:
    with _connect() as conn:
        rows = conn.execute("SELECT url FROM articles WHERE url IS NOT NULL").fetchall()
        return {row["url"] for row in rows}


def insert_pending(source_key, source_name, url, title_en, published_at, fetched_at):
    with _connect() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO articles "
            "(source_key, source_name, url, title_en, published_at, fetched_at, status) "
            "VALUES (?, ?, ?, ?, ?, ?, 'pending')",
            (source_key, source_name, url, title_en, published_at, fetched_at),
        )
        conn.commit()


def insert_pending_with_body(source_key, source_name, title_en, body_en, fetched_at):
    """手動貼上文章用：內文已經有了，直接進 pending 佇列等翻譯/解析。"""
    with _connect() as conn:
        cur = conn.execute(
            "INSERT INTO articles "
            "(source_key, source_name, url, title_en, published_at, fetched_at, status, body_en_json) "
            "VALUES (?, ?, NULL, ?, ?, ?, 'pending', ?)",
            (source_key, source_name, title_en, fetched_at, fetched_at, json.dumps(body_en, ensure_ascii=False)),
        )
        conn.commit()
        return cur.lastrowid


def requeue_errors() -> int:
    """把處理失敗的文章重新排回 pending（例如 API 暫時性錯誤），回傳重新排入的篇數。"""
    with _connect() as conn:
        cur = conn.execute("UPDATE articles SET status='pending', error_message=NULL WHERE status='error'")
        conn.commit()
        return cur.rowcount


def list_pending(limit: int) -> list:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM articles WHERE status = 'pending' ORDER BY id ASC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]


def count_pending() -> int:
    with _connect() as conn:
        row = conn.execute("SELECT COUNT(*) AS c FROM articles WHERE status = 'pending'").fetchone()
        return row["c"]


def save_analysis(article_id, title_zh, body_en, body_pairs, vocab, grammar):
    with _connect() as conn:
        conn.execute(
            "UPDATE articles SET status='ready', title_zh=?, body_en_json=?, body_json=?, "
            "vocab_json=?, grammar_json=?, error_message=NULL WHERE id=?",
            (
                title_zh,
                json.dumps(body_en, ensure_ascii=False),
                json.dumps(body_pairs, ensure_ascii=False),
                json.dumps(vocab, ensure_ascii=False),
                json.dumps(grammar, ensure_ascii=False),
                article_id,
            ),
        )
        conn.commit()


def mark_error(article_id, message):
    with _connect() as conn:
        conn.execute(
            "UPDATE articles SET status='error', error_message=? WHERE id=?",
            (message, article_id),
        )
        conn.commit()


def list_articles(limit=50, only_ready=True) -> list:
    with _connect() as conn:
        query = "SELECT * FROM articles"
        if only_ready:
            query += " WHERE status = 'ready'"
        query += " ORDER BY COALESCE(published_at, fetched_at) DESC LIMIT ?"
        rows = conn.execute(query, (limit,)).fetchall()
        return [_row_to_article(r) for r in rows]


def get_article(article_id):
    with _connect() as conn:
        row = conn.execute("SELECT * FROM articles WHERE id=?", (article_id,)).fetchone()
        return _row_to_article(row) if row else None


def mark_read(article_id):
    with _connect() as conn:
        conn.execute("UPDATE articles SET is_read=1 WHERE id=?", (article_id,))
        conn.commit()


def _row_to_article(row):
    d = dict(row)
    d["body_en"] = json.loads(d["body_en_json"]) if d.get("body_en_json") else []
    d["body"] = json.loads(d["body_json"]) if d.get("body_json") else []
    d["vocab"] = json.loads(d["vocab_json"]) if d.get("vocab_json") else []
    d["grammar"] = json.loads(d["grammar_json"]) if d.get("grammar_json") else []
    return d
