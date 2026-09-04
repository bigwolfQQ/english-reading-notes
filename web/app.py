"""
英文新聞學習平台 - 網頁介面

用法:
  python web/app.py
  瀏覽器打開 http://localhost:5001 （或這台電腦的區網 IP:5001）
"""
import datetime as dt
import os
import secrets
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from flask import Flask, Response, abort, flash, redirect, render_template, request, url_for

import analyzer
import storage

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


_load_env_file()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or secrets.token_hex(16)

WEB_USERNAME = os.environ.get("WEB_USERNAME")
WEB_PASSWORD = os.environ.get("WEB_PASSWORD")


@app.before_request
def _require_login():
    if not WEB_USERNAME or not WEB_PASSWORD:
        return  # 沒設定帳密就不擋（本機/區網使用情境）
    auth = request.authorization
    ok = (
        auth
        and secrets.compare_digest(auth.username, WEB_USERNAME)
        and secrets.compare_digest(auth.password, WEB_PASSWORD)
    )
    if not ok:
        return Response(
            "需要登入", 401, {"WWW-Authenticate": 'Basic realm="english-reading-coach"'}
        )


@app.route("/")
def index():
    show_all = request.args.get("all") == "1"
    articles = storage.list_articles(limit=50, only_ready=not show_all)
    pending_count = storage.count_pending()
    return render_template("index.html", articles=articles, show_all=show_all, pending_count=pending_count)


@app.route("/article/<int:article_id>")
def article_detail(article_id):
    article = storage.get_article(article_id)
    if article is None or article["status"] != "ready":
        abort(404)
    storage.mark_read(article_id)
    return render_template("article.html", article=article)


@app.route("/add", methods=["GET", "POST"])
def add_manual():
    """手動貼上文章（例如 CommonWealth Magazine 這類抓不到的網站），一樣會跑翻譯/解析流程。"""
    if request.method == "GET":
        return render_template("add.html")

    title = request.form.get("title", "").strip()
    source_name = request.form.get("source_name", "").strip() or "手動貼上"
    body_raw = request.form.get("body", "").strip()

    if not title or not body_raw:
        flash("請填標題和內文", "error")
        return redirect(url_for("add_manual"))

    paragraphs = [line.strip() for line in body_raw.splitlines() if line.strip()]
    if not paragraphs:
        flash("內文不能是空的", "error")
        return redirect(url_for("add_manual"))

    now = dt.datetime.now(dt.timezone.utc).isoformat()
    article_id = storage.insert_pending_with_body("manual", source_name, title, paragraphs, now)

    try:
        result = analyzer.analyze(title, paragraphs)
        storage.save_analysis(article_id, result["title_zh"], paragraphs, result["body"], result["vocab"], result["grammar"])
        flash("已加入並完成翻譯/解析！", "success")
        return redirect(url_for("article_detail", article_id=article_id))
    except Exception as e:
        storage.mark_error(article_id, str(e))
        flash(f"翻譯/解析失敗：{e}", "error")
        return redirect(url_for("index"))


if __name__ == "__main__":
    # 預設綁 0.0.0.0，本機/區網手機都能直接連。部署到雲端主機、前面有反向代理 (HTTPS) 時，
    # 在 config/.env 設 WEB_HOST=127.0.0.1，改成只給反向代理連、不直接對外。
    host = os.environ.get("WEB_HOST", "0.0.0.0")
    app.run(host=host, port=5001, debug=False)
