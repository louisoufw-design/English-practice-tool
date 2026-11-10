# AGENTS.md — 摩登家庭片語本 (Modern Family phrase book)

Technical notes for developers and AI coding assistants. Read this file first, then `docs/HISTORY.md` for the decisions and the owner's preferences.

## What this is
A single-page web app for Taiwanese learners practicing spoken American English to learn everyday phrases from the TV show *Modern Family*.
- All 11 seasons / 250 episodes are done: 10 phrases per episode (S01E01–E02 have 15) = **2,510 phrases**, all unique across the site.
- Each episode has a Chinese plot summary (lede), 1–4 story groups, phrase cards, 3 speaking prompts and 3–6 situation challenges.
- UI language: **Traditional Chinese (zh-Hant, Taiwan)**. Talk to the owner in Traditional Chinese too.
- It was originally built and published as a claude.ai Artifact (`YOUR_ARTIFACT_URL`).

## Repo layout
```
build.py            # parses content, validates, injects data into template → dist/
template.html       # the whole app: CSS + JS (vanilla, no framework), placeholder const EPISODES=__EPISODES__;
base.json           # S01E01 + S01E02 content (JSON, 15 phrases each; older format)
seasons/s01a.txt …  # all other episodes in a compact text format (two files per season, a = first half, b = second half)
tags/part1-4.txt    # theme + level for every phrase (one line per episode, codes in phrase order)
dist/index.html     # build output: full standalone page (open in a browser / host anywhere)
dist/artifact.html  # build output: body-only version for claude.ai Artifacts (host adds <html>/<head>)
docs/HISTORY.md     # what was built, why, and the owner's preferences
```

## Build & preview
```
python3 build.py          # validates everything, writes dist/index.html and dist/artifact.html
python3 build.py --force  # write output even if validation errors exist (don't ship that)
```
Open `dist/index.html` directly in a browser, or `python3 -m http.server -d dist 8000` → http://localhost:8000.
There are no npm dependencies. Fonts come from Google Fonts (page still works offline with fallbacks).
**Never hand-edit `dist/`** — edit `template.html` / content files and rebuild.

## Content format (`seasons/*.txt`)
```
# s01e03 | Come Fly with Me
L: 中文劇情簡介（1–2 句）
S: storyid | 顯示名稱 | 角色 · 角色 | 這段劇情
P: phrase | 中文意思 | 劇情情境 | English example sentence | 例句中文翻譯 | 標籤：說明
Q: 錄音題目（exactly 3 per episode）
C: 挑戰情境 | phrase1; phrase2 | reference answer   (3–6 per episode; we write 4)
```
- `P:` lines belong to the most recent `S:` story. Tip `標籤：說明` becomes `<b>標籤：</b>說明`. Labels used: 用法 對比 延伸 畫面 語氣 發音 文化 來源 搭配 注意 同義 反義 縮寫 句型 文法.
- Story ids in use: `dunphy`, `jay`, `mitch`, `kids`, `family`, `gloria`. **`all` is reserved** (it is the 全部 filter tab); build.py rejects it.
- No `<` or `>` characters in content. Challenge `uses` must exactly match phrases of the same episode.
- **Phrases must be unique across the whole site.** build.py normalizes (lowercase, strips punctuation, someone/something/one's, leading be/to/get) and errors on duplicates. Also avoid near-duplicates like "a blast from the past" vs "blast from the past" (not caught automatically).
- Example sentences are original everyday sentences, NOT script quotes (copyright). Examples/challenges use varied Taiwan daily-life situations (work, school, friends, family, travel, sports…); military-service situations are kept to roughly 1 in 10.
- Plots come from Wikipedia season pages; when unsure, keep scene descriptions general.

## Tags (`tags/part*.txt`)
`s01e03: 4a 2a 10b ...` — one code per phrase, in the same order the `P:` lines appear (base.json: stories order). Code = theme number + level letter.
Themes: 1 感情, 2 家人朋友, 3 工作學校, 4 情緒, 5 衝突, 6 安慰鼓勵, 7 聊天反應, 8 生活日常, 9 形容人事, 10 計畫行動. Level: a = 基礎, b = 進階.
build.py attaches them to items as `it.th` (1–10) and `it.lv` (1|2) and errors if counts don't match. **If you add/remove/reorder a phrase, update its tag line.**

## App architecture (`template.html`)
Vanilla JS, one `render()` that rebuilds `#app` innerHTML from state; hash routing.
- Routes: `#home` `#episodes` (選集 + finder) `#sXXeYY` (episode) `#learn` (片語盲盒) `#review` `#challenge` `#notes` (造句本) `#stats` (進度).
- Event delegation: buttons carry `data-act="..."`, handled in one big `switch` in the `app` click listener. Input/change listeners for `#q` (search), `#sent-input`, `#hidezh`, `#spoilguard`.
- `EPISODES` (injected), `ITEMS` (flat list `{k,p,it,st}`), `IDX["sXXeYY|phrase"]`, `EKEYS` (sorted episode keys).
- `epLabel(k)` → "S01 E01" (with a space — owner's request; use it everywhere).

### State & storage
`S = {profile, eps}` persisted to `localStorage["mf-v2"]` (cache / local mode) and, on claude.ai, to the Artifact db.
- `S.eps[k].cards[phrase] = {s, due, last, reps, lapses, added, sent?:{t, v, at}}` — a card exists once the user presses 「搞定」.
- `S.profile = {days:{"YYYY-MM-DD":{r,n,x,w,ch:{}}}, pause, pauses[], migrated, watched:{k:day}, spoil:bool}`.
- Day numbers are UTC day counts (`dayNum()`), keys via `dkey()`.
- SRS ladder `[1,3,7,14,30,60,120,240]` days; ratings 忘了/模糊/想起來了 (0/1/2); daily review cap `CAP=10`; mastered = `s>=3`; weak = not mastered with ≥2 lapses.
- Pause/vacation mode shifts due dates; streak allows one missed day per Monday-based week.
- Sentence review verdicts: good / minor / wrong / fixed. PASS = good or fixed. Only PASS sentences appear in 「我的金句」 on home.

### claude.ai runtime dependency (important when moving off claude.ai)
`connect()` uses `window.claude.use("db")` and `window.claude.use("user")` for per-user cloud sync (collection `data/users/<uid>`, docs `profile` + one per episode). `window.claude.use("sample")` + `sfn.json(prompt,{modelTier:"quick"})` powers the Claude sentence review (`reviewPrompt()` defines the JSON contract).
Outside claude.ai these don't exist → the app automatically runs in **local mode** (localStorage only, review button disappears). Everything else works.
To self-host with sync + review you need replacements, e.g. Firebase Auth + Firestore behind the same small interface (`col().onSnapshot`, doc set/get) and a server-side proxy (Cloudflare Worker / Firebase Function) calling the Anthropic API with the same prompt/JSON. **Never put an API key in client code or in the repo.**
Progress the owner made on claude.ai lives in that Artifact's db and does not move automatically.

### Features (all live)
- Home: streak + mini 5-week calendar; 追劇卡 (next episode slate, season strip, 「這集看完了」); review task; 片語盲盒; 情境挑戰; 今日一句 (one sentence per day); 休假模式; 今日學習 (today's new phrases + play all); 我的金句.
- Episode page: spoiler guard, 我看完這集了, story filter tabs, 遮住中文 toggle, phrase cards (搞定 / 記憶中 · date, click again to undo), practice steps + prompts, pager.
- Spoiler guard: `isSpoil(k)` = guard on && `k > frontier()` (latest watched). Plots/scenes wrapped with `sp()` are blurred, click to peek; story names become neutral (`STORY_NAMES`).
- 選集: search box (phrase / 中文 / example), hidden 篩選 panel (theme, level, 只看還沒學的), 15 results per page, click → episode with card highlighted (`pendingFocus`). Without filters it shows season tabs + episode grid (✓ watched, 下一集 badge).
- Notes (造句本): 今日例句 at top, 收藏的字詞 section (manual add + list), written sentences, editor with Claude review.
- Sentence review also checks word chunks/collocations (`chunkOk`, `chunkNote`) and suggests one extra collocation (`collocation.en/zh/ex`) with a 「收進片語本」 button.
- Tap-to-collect: example sentences are rendered with `tapText()`; tapping words selects a span, `#pickbar` asks Claude (`lookupPrompt`) for base form / 中文 / note / example, then saves.
- Custom phrases: if a saved phrase normalizes (`normP` / `NIDX`) to a dataset phrase, that phrase is marked learned instead; otherwise it is stored in `S.eps.custom.cards[phrase]` with `.custom={zh,ex,note,src,from}`. Always use `itemOf(k,p)` (not `IDX[...]`) where a card may be custom; `srcLabel`/`srcFull` give the source label. In review, custom cards use a Toko-style mode: write a sentence with the word → Claude review → rate.
- Stats: tiles, 5-week calendar, most-forgotten + extra practice, 各季進度 ring grid.

## Conventions / owner preferences
- Mobile first (~400px). Sticky nav. No horizontal scroll. Light + dark themes via CSS variables in `:root`.
- Keep UI light: the owner dislikes long text rows and pages that feel like a burden; prefers compact, visual summaries.
- Wording in Taiwan Mandarin, friendly, not too 白話. Button wording matters (e.g. 「搞定」, not 「加入複習」).
- Phrase underline (not highlight). Avoid self-correcting text in content.
- The owner said designs tend to all look the same — when redesigning, offer distinct style options to choose from.
- After any change: `python3 build.py`, then check in a browser at phone width.

## Backlog (suggested, not done)
1. Home is long — collapse finished tasks into one line; move 休假模式 to stats.
2. Stats top: show only 3 tiles, smaller calendar.
3. First-run 3-step onboarding card (看劇 → 搞定 → 複習 → 挑戰/造句).
4. Episode cards: collapse 小技巧 by default.
5. Shadowing: 0.75× playback + record & compare (MediaRecorder). Dictation: 5/day from learned phrases' examples on the 挑戰 page + a home task (no API needed).
6. Gentle daily new-phrase limit reminder (~6–7 per day).
7. Self-hosting as an installable PWA (manifest + service worker), GitHub Pages, Firebase sync, API proxy for review.
