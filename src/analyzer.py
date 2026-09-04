"""
用 Google Gemini API 把一篇英文文章翻譯成繁體中文，並產出單字解析、文法重點。
"""
import json
import os
import re

from google import genai
from google.genai import errors

_DEFAULT_MODEL = "gemini-3.6-flash"

PROMPT_TEMPLATE = """你是專門幫台灣英語學習者精讀英文新聞的老師。以下是一篇英文新聞文章，請完成三件事：

1. 把每一段翻譯成流暢、精準的繁體中文（保留新聞語氣，不要漏譯、不要加內容）。
2. 從文章中挑出 8~15 個對中高級英語學習者有幫助的單字或片語（優先挑新聞常見但學習者不一定熟悉的詞彙、
   片語動詞、慣用語，不要挑太簡單的字），附詞性、精準的繁體中文解釋，以及「直接取自文章」的例句。
3. 找出 3~6 個文章中出現、值得學習的文法或句構重點（例如分詞構句、倒裝句、被動語態、關係子句、
   假設語氣、名詞子句等），附「直接取自文章」的原句，以及用繁體中文解說這個文法點怎麼運作。

文章標題：{title}

文章內文（已依段落編號，一行一段）：
{numbered_paragraphs}

請「只」回傳一個 JSON 物件，不要加任何說明文字、不要用 markdown code fence，格式如下：
{{
  "title_zh": "標題的繁體中文翻譯",
  "paragraphs_zh": ["第1段的繁體中文翻譯", "第2段的繁體中文翻譯", "..."],
  "vocab": [
    {{"word": "單字或片語", "pos": "詞性", "meaning_zh": "繁體中文解釋", "example_en": "文章中的原句"}}
  ],
  "grammar_notes": [
    {{"point": "文法重點名稱", "example_en": "文章中的原句", "explanation_zh": "繁體中文解說"}}
  ]
}}

"paragraphs_zh" 陣列的長度必須跟輸入的段落數完全一樣，且順序要一一對應，不能合併或拆分段落。
"""


class AnalyzeError(RuntimeError):
    pass


def _client() -> genai.Client:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key or "請貼上" in api_key:
        raise AnalyzeError("尚未設定 GEMINI_API_KEY，請先在 config/.env 填入 Gemini API key")
    return genai.Client(api_key=api_key)


def analyze(title: str, paragraphs: list) -> dict:
    """回傳 {"title_zh", "body": [{"en","zh"}...], "vocab": [...], "grammar": [...]}"""
    numbered = "\n".join(f"{i + 1}. {p}" for i, p in enumerate(paragraphs))
    prompt = PROMPT_TEMPLATE.format(title=title, numbered_paragraphs=numbered)
    model = os.environ.get("GEMINI_MODEL") or _DEFAULT_MODEL

    client = _client()
    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config={"response_mime_type": "application/json"},
        )
    except errors.APIError as e:
        raise AnalyzeError(f"Gemini API 呼叫失敗（{e.code}）：{e.message}") from e

    data = _parse_json(response.text or "")

    paragraphs_zh = data.get("paragraphs_zh") or []
    if len(paragraphs_zh) != len(paragraphs) and paragraphs:
        # 段數對不上時的保底處理：把譯文全部塞進第一段，寧可排版跑掉也別遺失翻譯內容
        joined = "\n".join(paragraphs_zh)
        paragraphs_zh = [joined] + [""] * (len(paragraphs) - 1)

    body_pairs = [{"en": en, "zh": zh} for en, zh in zip(paragraphs, paragraphs_zh)]
    return {
        "title_zh": data.get("title_zh", ""),
        "body": body_pairs,
        "vocab": data.get("vocab", []),
        "grammar": data.get("grammar_notes", []),
    }


def _parse_json(text: str) -> dict:
    text = text.strip()
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        text = match.group(0)
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise AnalyzeError(f"Gemini 回傳的內容不是有效 JSON：{e}") from e
