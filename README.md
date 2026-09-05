# 英文新聞學習平台

自動抓 **Taipei Times** 和 **Focus Taiwan (CNA 英文新聞)** 的最新文章，用 Google Gemini API 翻譯成繁體中文、
挑出值得學的單字/片語（**選字以 TOEIC 多益測驗範圍為主**：職場溝通、商業、財經、行銷、人資、旅遊、
辦公室日常等多益核心主題）、標出文法重點，網頁上可以中英對照閱讀，還能用瀏覽器內建語音朗讀整篇或單句，
方便邊聽邊練發音。每個單字的例句都附「朗讀按鈕」+「繁體中文翻譯」，聽完馬上能對照確認自己聽懂多少。

- **來源**：Taipei Times、Focus Taiwan 都有公開 RSS、文章內文伺服器端直接輸出，不用登入、沒有反爬蟲防護。
  **CommonWealth Magazine 英文站沒有列入自動抓取**——它掛了 Cloudflare 機器人驗證（連 curl 都被擋），
  也找不到官方 RSS，硬繞過防護不合適。想讀天下雜誌的文章，用網頁上的「手動貼上文章」功能，
  自己在瀏覽器打開文章複製貼上即可，一樣會跑完整的翻譯/單字/文法流程。
- **翻譯與解析**：Google Gemini API（預設 `gemini-3.5-flash-lite`），一次呼叫同時產出翻譯、單字表、文法重點，
  個人低用量通常落在 Google 的免費額度內，等於不用花錢。**注意模型選擇**：最新的 `gemini-3.6-flash`
  免費額度只有每天 20 次呼叫，個人這種累積抓取量很容易瞬間超額；`flash-lite` 系列免費額度寬鬆很多，
  品質也還是很夠用，所以預設用它。
- **語音朗讀**：瀏覽器內建 Web Speech API，免費、不用金鑰，可調語速、選發音、逐段或整篇播放。
- **執行方式**：Windows 工作排程器，預設每 30 分鐘檢查一次新文章。
- **兩種介面**：私人版（`web/app.py`，完整原文+逐段翻譯+整篇朗讀，只有你自己用）跟
  公開版（`manage.py export-public` 產生的靜態網頁，只有標題翻譯/單字/文法短句摘錄，
  可以放上 GitHub Pages 公開分享，不涉及重製整篇有版權的新聞內容）。

---

## 1. 安裝套件

```powershell
cd "D:\claude Agent\english-reading-coach"
python -m pip install -r requirements.txt
```

## 2. 設定 Gemini API 金鑰

1. 到 [Google AI Studio](https://aistudio.google.com/apikey) 用 Google 帳號登入，申請一組免費 API key。
2. 打開 `config/.env.example`，另存成 `config/.env`，貼上金鑰：

```
GEMINI_API_KEY=你的金鑰
```

3. 測試翻譯/解析是否正常：

```powershell
python manage.py test-translate
```

看到「成功！Gemini API 設定沒問題」就代表設定完成。

**費用**：Google AI Studio 的免費額度通常就足夠這種「一天幾篇文章」的個人用量，多半是 $0。
如果之後用量變大超過免費額度，付費價格也很低（`gemini-3.5-flash-lite` 大約每百萬 token 輸入
US$0.3、輸出 US$2.5 左右）。想換品質更好、但免費額度嚴格很多（每天只有 20 次）的
`gemini-3.6-flash` 也可以，在 `.env` 改 `GEMINI_MODEL` 即可，但個人這種累積抓取的用法很容易超額。
`.env` 裡的 `MAX_ARTICLES_PER_RUN`（預設 8）限制每次排程最多處理幾篇新文章，
避免新聞一次湧入時超過免費額度或費用暴衝，處理不完的文章會留到下一次排程繼續。

## 3. 手動抓一次文章

```powershell
python manage.py fetch
```

會先掃 RSS 找新文章，再把還沒翻譯的文章（含之前排隊但沒處理完的）送去 Gemini 解析。

```powershell
python manage.py list          # 列出目前所有文章跟狀態
python manage.py list --all    # 含處理中/失敗的文章
python manage.py retry         # 重新處理之前失敗（error）的文章
python manage.py reanalyze     # 把已完成的文章全部重新翻譯/解析一次
                                # （改了 src/analyzer.py 的 prompt 規則後，用這個指令套用到舊文章）
```

## 4. 設定自動排程（Windows 工作排程器）

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\register_task.ps1
```

會註冊一個名為 `EnglishReadingCoach-Fetch` 的排程工作，每 30 分鐘執行一次 `src/check_new.py`。

- 想暫停：開始功能表搜尋「工作排程器」(Task Scheduler)，找到該工作按「停用」。
- 想完全移除：`Unregister-ScheduledTask -TaskName 'EnglishReadingCoach-Fetch' -Confirm:$false`
- 執行紀錄可以自己導向 log 檔查看，例如把工作排程的動作改成先寫 log，或直接手動執行
  `python src/check_new.py` 看終端機輸出。

## 5. 手機/網頁閱讀介面

```powershell
python web/app.py
```

跑起來之後：
- **這台電腦上**：瀏覽器打開 `http://localhost:5001`
- **手機上**（跟這台電腦連同一個 WiFi）：打開 `http://<這台電腦的區網IP>:5001`
  （用 `ipconfig` 查目前的 IPv4 位址）

畫面上可以看到文章列表（依發布時間排序），點進去可以：
- 中英對照閱讀（可切換只看英文）
- 按「▶ 播放整篇」用語音朗讀，或按段落旁的 🔊 只聽那一段，方便重複練習跟讀
- 調整語速、選擇不同的英文發音（清單來自瀏覽器/系統內建的語音）
- 看單字解析（詞性、中文意思、文章原句），單字也可以按 🔊 單獨聽發音
- 看文法重點（文章原句 + 中文解說）

**設定成一開機就自動啟動**（這樣手機隨時打得開，不用自己先跑指令）：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\register_web_task.ps1
```

> **安全提醒**：這個網頁預設沒有帳號密碼保護，同一個 WiFi 裡的其他裝置只要知道網址就能看到你的文章列表。
> 只在自己家用網路開，不要對外開放（不要設定路由器 port forwarding）。

## 6. 手動貼上文章（給 CommonWealth Magazine 這類抓不到的網站用）

網頁上按右上角「＋ 手動貼上文章」，把來源、標題、內文（每段一行）貼上送出，
會走跟自動抓取一樣的翻譯/單字/文法解析流程，處理完直接跳到文章頁面。
**這類手動貼上的文章沒有原文網址可查證來源，不會出現在第 7 節的公開版**，只留在私人版本。

## 7. 公開版（GitHub Pages）

私人版本（第 5 節）有完整英文原文、逐段中文翻譯、整篇朗讀，這些內容公開發布會構成
重製整篇有版權新聞的問題，所以**不會**放上公開版。公開版只放：

- 文章標題（中譯 + 英文原文）+ 連回原始新聞網站的連結
- 單字解析（單字、詞性、中文意思、一句取自文章的例句 + 朗讀按鈕）
- 文法重點（文法點、一句取自文章的例句 + 朗讀按鈕、中文解說）

產生公開版靜態網頁：

```powershell
python manage.py export-public
```

會把資料庫裡已完成翻譯、而且有原文網址的文章（手動貼上的文章沒有網址，會被排除）匯出成
純靜態 HTML，寫到 `docs/` 資料夾。可以先用瀏覽器直接打開 `docs/index.html` 預覽，
或本機起個簡易伺服器看：`python -m http.server 8899 --directory docs`。

### 發布到 GitHub Pages

**先確認一件事**：GitHub Pages 要設成「只有你自己看得到」，帳號必須是付費的 GitHub Pro
以上方案；免費帳號的話，Pages 網站一定是公開給任何人看的。這個專案的公開版內容
（標題翻譯、單字、文法、短句引用）刻意設計成即使公開也不構成版權問題，所以用免費帳號、
public repo 也可以，只是要記得**不要**把 `data/articles.db`、`config/.env` 這些私人資料也一起
推上這個 public repo（`.gitignore` 已經排除了）。

1. 在 GitHub 上開一個新的 public repository（例如 `english-reading-notes`）。
2. 把這個專案的程式碼推上去（或者只推 `docs/` 也可以，看你想不想公開原始碼）。
3. GitHub repo 的 **Settings → Pages**，Source 選 `Deploy from a branch`，
   Branch 選 `main`，資料夾選 `/docs`，Save。
4. 等一兩分鐘，GitHub 會給一個 `https://<你的帳號>.github.io/<repo名稱>/` 網址。

之後每次想更新公開版，重新執行 `python manage.py export-public`，
把 `docs/` 的變動 commit + push 上去就會自動更新（GitHub Pages 沒有另外的建置步驟，
純粹是把 `docs/` 底下的檔案當網站發布）。想自動化這個 push 動作（例如接在
`scripts/register_task.ps1` 排程之後），這台機器需要先設定好 git 的推送權限
（SSH deploy key 或 personal access token），這步驟需要你自己的 GitHub 帳號權限，
我沒辦法代勞；設定好之後可以在排程腳本裡加一段 `git add docs && git commit -m "update" && git push`。

## 8. 部署到雲端主機（不用開電腦、24 小時常駐）

跟 `stock-alert` 專案一樣的做法，可以搬到同一台 GCP Always Free VM 上常駐：
`check_new.py` 用 systemd timer 每 30 分鐘觸發一次，`web/app.py` 用 systemd service 常駐、
前面掛 Caddy 反向代理提供 HTTPS，網頁對外時記得在雲端主機的 `config/.env` 設 `WEB_USERNAME`/
`WEB_PASSWORD` 開 Basic Auth。細節可以參考 `stock-alert/README.md` 的「部署到雲端主機」章節，
架構完全一樣，只是把 `stock-alert-check` / `stock-alert-web` 換成這個專案的路徑跟服務名稱。
這一步目前還沒有實際部署，等你確定要用雲端常駐再進行。

## 檔案結構

```
english-reading-coach/
  manage.py                    # 命令列管理工具（抓文章/列出/測試翻譯）
  config/
    .env.example                # Gemini API 金鑰範本，複製成 .env 後填入自己的值
  data/
    articles.db                  # SQLite 資料庫（文章、翻譯、單字、文法），不會進 git
  src/
    sources.py                    # RSS 來源清單 + 各網站內文擷取規則
    fetcher.py                     # 抓 RSS、下載文章頁面、擷取內文
    analyzer.py                     # 呼叫 Gemini API 做翻譯/單字/文法解析
    storage.py                       # SQLite 存取
    check_new.py                      # 主邏輯：發現新文章 -> 翻譯解析 -> 存檔
    public_site.py                     # 匯出公開版靜態網頁（給 GitHub Pages 用）
  web/
    app.py                              # 私人版網頁介面 (Flask)：完整原文+翻譯+整篇朗讀
    templates/                           # 文章列表、文章詳細頁、手動貼上文章表單
    static/
      style.css
      reader.js                          # 語音朗讀（Web Speech API）互動邏輯
  public_site/
    templates/                            # 公開版模板：只有標題翻譯/單字/文法，無完整原文
    static/                                # 公開版樣式 + 朗讀 JS（跟私人版共用大部分 CSS）
  docs/                                    # `manage.py export-public` 的輸出，會進 git，GitHub Pages 從這裡發布
  scripts/
    register_task.ps1                     # 註冊抓文章排程（每 30 分鐘）
    register_web_task.ps1                  # 註冊網頁介面開機自動啟動
  logs/
```

## 限制與注意事項

- 目前只自動抓 Taipei Times（首頁 RSS）+ Focus Taiwan（RSS），想加更多分類/來源，
  在 `src/sources.py` 的 `SOURCES` 清單加一筆 `Source`，並寫一個對應網站結構的 `extract` 函式即可。
- 翻譯/解析完全依賴 Gemini 的輸出格式（要求回傳固定結構的 JSON），
  極少數情況下模型輸出格式跑掉會讓那篇文章翻譯失敗，`manage.py list --all` 可以看到失敗原因，
  直接重新執行 `python manage.py fetch` 會重試（失敗的文章目前不會自動重試，
  之後有需要可以加一個 `retry` 指令）。
- Web Speech API 的音質、可選發音種類依瀏覽器/作業系統而定，Chrome/Edge 在 Windows 上通常
  有多組內建英文語音（美式/英式）可以選。
- RSS/網站的 HTML 結構之後可能改版，導致抓不到內文或抓錯內容，`src/sources.py` 裡的
  `_extract_taipei_times` / `_extract_focus_taiwan` 是這兩個網站目前（2026 年）的版面寫的，
  改版時需要更新對應的 CSS 選擇器。
