"""
英文新聞學習平台 - 管理工具

用法範例:
  python manage.py fetch                  # 手動抓一次新文章、翻譯/解析
  python manage.py retry                  # 重試之前失敗的文章
  python manage.py list                   # 列出資料庫裡的文章
  python manage.py list --all             # 含處理中/失敗的文章
  python manage.py test-translate         # 測試 Gemini API 是否設定成功
"""
import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

import check_new
import storage


def cmd_fetch(_args):
    check_new._load_env_file()
    found = check_new.discover_new_articles()
    print(f"發現 {found} 篇新文章" if found else "沒有新文章")

    max_articles = int(os.environ.get("MAX_ARTICLES_PER_RUN", "8"))
    processed = check_new.process_pending(max_articles)
    print(f"完成翻譯/解析 {processed} 篇" if processed else "沒有文章需要處理")

    remaining = storage.count_pending()
    if remaining:
        print(f"還有 {remaining} 篇排隊，留到下次執行 `python manage.py fetch` 繼續處理")


def cmd_retry(_args):
    check_new._load_env_file()
    requeued = storage.requeue_errors()
    if not requeued:
        print("沒有失敗的文章需要重試")
        return
    print(f"把 {requeued} 篇失敗的文章重新排入處理佇列")

    max_articles = int(os.environ.get("MAX_ARTICLES_PER_RUN", "8"))
    processed = check_new.process_pending(max(requeued, max_articles))
    print(f"完成翻譯/解析 {processed} 篇" if processed else "沒有文章需要處理")

    remaining = storage.count_pending()
    if remaining:
        print(f"還有 {remaining} 篇排隊，留到下次執行 `python manage.py fetch` 繼續處理")


def cmd_list(args):
    articles = storage.list_articles(limit=args.limit, only_ready=not args.all)
    if not articles:
        print("目前沒有文章，先執行 `python manage.py fetch`")
        return
    for a in articles:
        flag = "已讀" if a["is_read"] else "未讀"
        print(f"[{a['id']}] ({a['status']}, {flag}) {a['source_name']}：{a['title_en']}")
        if a["status"] == "error" and a.get("error_message"):
            print(f"       錯誤：{a['error_message']}")


def cmd_export_public(args):
    import public_site

    count = public_site.export(args.output)
    out = args.output or "docs"
    print(f"已產生 {count} 篇公開版文章到 {out}/（不含完整原文，只有標題翻譯/單字/文法）")
    print(f"檢查沒問題後，把 {out}/ 加進 git 並 push，到 GitHub repo 設定 Pages 從這個資料夾發布即可。")


def cmd_test_translate(_args):
    check_new._load_env_file()
    import analyzer

    print("測試翻譯中...")
    result = analyzer.analyze(
        "Taiwan Advances Renewable Energy Goals",
        [
            "Taiwan announced a new plan on Monday to expand offshore wind capacity by 2030.",
            "Officials said the plan, which was drafted after months of deliberation, "
            "would reduce reliance on imported fossil fuels.",
        ],
    )
    print("成功！Gemini API 設定沒問題。範例輸出：")
    print(f"  標題翻譯：{result['title_zh']}")
    print(f"  段落數：{len(result['body'])}")
    print(f"  單字數：{len(result['vocab'])}")
    print(f"  文法重點數：{len(result['grammar'])}")


def main():
    parser = argparse.ArgumentParser(description="英文新聞學習平台管理工具")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("fetch", help="抓取新文章並翻譯/解析").set_defaults(func=cmd_fetch)

    sub.add_parser(
        "retry", help="把之前處理失敗的文章（例如 API 暫時性錯誤）重新排入處理"
    ).set_defaults(func=cmd_retry)

    p_list = sub.add_parser("list", help="列出文章")
    p_list.add_argument("--limit", type=int, default=20)
    p_list.add_argument("--all", action="store_true", help="包含尚未翻譯完成/失敗的文章")
    p_list.set_defaults(func=cmd_list)

    sub.add_parser(
        "test-translate", help="測試 Gemini API 翻譯/解析是否設定成功"
    ).set_defaults(func=cmd_test_translate)

    p_export = sub.add_parser(
        "export-public", help="把文章匯出成靜態網頁（標題翻譯/單字/文法，不含完整原文），給 GitHub Pages 用"
    )
    p_export.add_argument("--output", default=None, help="輸出資料夾，預設 docs/")
    p_export.set_defaults(func=cmd_export_public)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
