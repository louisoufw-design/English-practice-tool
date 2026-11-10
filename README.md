# 摩登家庭片語本 · Modern Family Phrase Book

看《Modern Family》學美式口語的單頁網站：11 季 250 集、2,510 個日常片語，搭配間隔複習、片語盲盒、情境挑戰、造句本、點字收藏、防劇透與追劇進度。介面為繁體中文（台灣），手機優先。

## 專案用途
- **依集數整理片語**：每集都有劇情簡介、片語卡（中文、情境、例句、小技巧）、錄音題目與情境挑戰。
- **遺忘曲線複習**：每天上限 10 個，有休假模式，每週可漏一天不斷連續天數。
- **找片語**：關鍵字搜尋，加上 10 類主題、基礎／進階篩選。
- **防劇透 + 追劇進度**：沒標記看完的集數，劇情會先模糊。
- **造句本與收藏字詞**：需在 claude.ai 環境中使用。
  - Claude 會檢查你寫的句子，包括語塊與搭配詞。
  - 例句裡點字就能收藏，複習時用它造句。

## 執行方式
不需要安裝任何套件，網站就是一個 HTML 檔：

```bash
# 1. 重新產生網站（修改內容或程式後執行）
python3 build.py

# 2. 用瀏覽器直接打開
open dist/index.html            # macOS（Windows 直接雙擊檔案）

# 或開本機伺服器
python3 -m http.server -d dist 8000
# 然後打開 http://localhost:8000
```

`build.py` 會做三件事：
1. 讀取 `base.json`、`seasons/*.txt`、`tags/*.txt`。
2. 檢查格式和片語是否重複。
3. 把資料注入 `template.html`，輸出兩個檔案：
   - `dist/index.html`：完整網頁，可放上 GitHub Pages 等任何靜態網站空間。
   - `dist/artifact.html`：給 claude.ai Artifact 用的版本。

### 放上 GitHub Pages
1. 把整個資料夾推上 GitHub。
2. 到 Settings → Pages，Source 選 `main` 分支、資料夾選 `/ (root)`。
3. 網址是 `https://<你的帳號>.github.io/<repo>/dist/`。

## 需要的套件與版本
| 項目 | 版本 | 用途 |
|---|---|---|
| Python | 3.8 以上（只用標準函式庫） | 執行 `build.py` |
| 現代瀏覽器 | Chrome / Safari / Edge / Firefox 近兩年版本 | 執行網站（用到 CSS `color-mix`、`conic-gradient`、Web Speech API） |

- 沒有 npm 或 pip 依賴。
- 字型從 Google Fonts 載入，離線時會用系統字型代替。

## 環境變數
**目前不需要設定任何環境變數。** 在一般瀏覽器開啟時，網站會自動進入「本機模式」：
- 進度存在瀏覽器的 localStorage。
- Claude 審核和查字功能會隱藏，其他功能完整可用。

`.env.example` 列出之後「自架並恢復雲端同步與 Claude 審核」才需要的變數：

| 變數 | 說明 |
|---|---|
| `ANTHROPIC_API_KEY` | Anthropic API 金鑰（只能放在伺服器端中繼） |
| `ANTHROPIC_MODEL` | 審核用的模型 ID |
| `FIREBASE_API_KEY` / `FIREBASE_AUTH_DOMAIN` / `FIREBASE_PROJECT_ID` / `FIREBASE_APP_ID` | Firebase 登入與資料庫設定 |
| `REVIEW_PROXY_URL` | 前端呼叫的審核中繼網址 |

使用方式：複製成 `.env` 並填入真正的值。`.env` 已被 `.gitignore` 排除，**絕對不要把金鑰寫進程式碼或上傳到 GitHub**。

## 檔案結構
```
.
├── README.md            專案說明（本檔）
├── AGENTS.md            技術文件：架構、內容格式、資料結構、開發慣例
├── docs/HISTORY.md      開發紀錄與設計決策
├── build.py             組裝與檢查腳本
├── template.html        整個網站的 HTML / CSS / JavaScript
├── base.json            S01E01、S01E02 的內容
├── seasons/             其餘 248 集的內容（每季兩個檔，a = 前半季，b = 後半季）
├── tags/part1~4.txt     每個片語的主題與程度標籤
├── dist/                build.py 的輸出（index.html、artifact.html）
├── .env.example         環境變數範本（皆為佔位符）
└── .gitignore
```

## 修改內容
- **片語、劇情、挑戰題**：改 `seasons/*.txt`，格式見 `AGENTS.md` 的「Content format」。
  - 片語必須全站不重複。
  - 新增或刪除片語時，要同步更新 `tags/` 對應那一行。
- **版面與功能**：改 `template.html`。
- 不要直接改 `dist/`，改完一律重新執行 `python3 build.py`。

## 版權說明
例句、劇情摘要與練習題均為原創或改寫，不含劇本原文。劇情摘要參考英文維基百科各季集數介紹。《Modern Family》為其權利人所有，本專案僅供個人學習使用。
