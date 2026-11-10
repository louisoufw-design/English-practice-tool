#!/usr/bin/env python3
"""Parse season text files, validate, and inject all episodes into the page template.

Season file format (seasons/sNN.txt):
# s01e03 | Come Fly with Me
L: lede
S: storyid | 顯示名稱 | 角色 · 角色 | 劇情
P: phrase | 中文 | 劇情情境 | English example | 中文翻譯 | 標籤：說明
Q: 錄音題目
C: 情境 | phrase1; phrase2 | reference answer
"""
import json, re, sys, glob, os

HERE = os.path.dirname(os.path.abspath(__file__))
COUNTS = [24, 24, 24, 24, 24, 24, 22, 22, 22, 22, 18]


def norm(p):
    p = p.lower().replace("’", "'")
    p = re.sub(r"[?!.,]", "", p)
    p = re.sub(r"\b(someone|something|somebody|sb|sth|one's|someone's)\b", "", p)
    p = re.sub(r"^(be|to|get) ", "", p.strip())
    return re.sub(r"\s+", " ", p).strip()


def parse(path, errors):
    eps = {}
    cur = None
    for ln, raw in enumerate(open(path, encoding="utf-8"), 1):
        line = raw.strip()
        if not line:
            continue
        where = f"{os.path.basename(path)}:{ln}"
        if "<" in line or ">" in line:
            errors.append(f"{where}: contains < or >")
        if line.startswith("# "):
            k, _, title = line[2:].partition("|")
            k = k.strip()
            if not re.fullmatch(r"s\d\de\d\d", k):
                errors.append(f"{where}: bad key {k}")
            cur = {"title": title.strip(), "lede": "", "stories": [], "prompts": [], "challenges": []}
            eps[k] = cur
            continue
        tag, _, rest = line.partition(":")
        rest = rest.strip()
        f = [x.strip() for x in rest.split("|")]
        if cur is None:
            errors.append(f"{where}: content before header")
            continue
        if tag == "L":
            cur["lede"] = rest
        elif tag == "S":
            if len(f) != 4:
                errors.append(f"{where}: S needs 4 fields, got {len(f)}")
                continue
            cur["stories"].append({"id": f[0], "name": f[1], "who": f[2], "plot": f[3], "items": []})
        elif tag == "P":
            if len(f) != 6:
                errors.append(f"{where}: P needs 6 fields, got {len(f)}")
                continue
            if not cur["stories"]:
                errors.append(f"{where}: P before S")
                continue
            lab, sep, txt = f[5].partition("：")
            tip = f"<b>{lab}：</b>{txt}" if sep else f[5]
            cur["stories"][-1]["items"].append({"p": f[0], "zh": f[1], "scene": f[2], "en": f[3], "tr": f[4], "tip": tip})
        elif tag == "Q":
            cur["prompts"].append(rest)
        elif tag == "C":
            if len(f) != 3:
                errors.append(f"{where}: C needs 3 fields, got {len(f)}")
                continue
            cur["challenges"].append({"id": f"c{len(cur['challenges'])+1}", "sit": f[0], "uses": [u.strip() for u in f[1].split(";") if u.strip()], "ans": f[2]})
        else:
            errors.append(f"{where}: unknown tag {tag!r}")
    return eps


def main():
    errors = []
    base = json.load(open(os.path.join(HERE, "base.json"), encoding="utf-8"))
    allep = dict(base)
    for path in sorted(glob.glob(os.path.join(HERE, "seasons", "s*.txt"))):
        for k, v in parse(path, errors).items():
            if k in allep:
                errors.append(f"duplicate episode {k}")
            allep[k] = v
    seen = {}
    for k in sorted(allep):
        ep = allep[k]
        items = [it for st in ep["stories"] for it in st["items"]]
        if k not in base and len(items) != 10:
            errors.append(f"{k}: {len(items)} phrases (need 10)")
        if not ep.get("lede"):
            errors.append(f"{k}: missing lede")
        if len(ep["prompts"]) != 3:
            errors.append(f"{k}: {len(ep['prompts'])} prompts (need 3)")
        if not 3 <= len(ep["challenges"]) <= 6:
            errors.append(f"{k}: {len(ep['challenges'])} challenges")
        ids = [st["id"] for st in ep["stories"]]
        if len(set(ids)) != len(ids):
            errors.append(f"{k}: duplicate story ids {ids}")
        if "all" in ids:
            errors.append(f"{k}: story id 'all' is reserved for the 全部 filter")
        names = {it["p"] for it in items}
        for c in ep["challenges"]:
            for u in c["uses"]:
                if u not in names:
                    errors.append(f"{k} {c['id']}: uses unknown phrase {u!r}")
        for it in items:
            n = norm(it["p"])
            if n in seen:
                errors.append(f"{k}: phrase {it['p']!r} duplicates {seen[n]}")
            else:
                seen[n] = f"{k} {it['p']!r}"
            for fld in ("zh", "scene", "en", "tr", "tip"):
                if not it[fld]:
                    errors.append(f"{k} {it['p']}: empty {fld}")
    # theme/level tags: tags/part*.txt, one line per episode "sXXeYY: 8a 3b ..." in phrase order
    tags = {}
    for path in sorted(glob.glob(os.path.join(HERE, "tags", "part*.txt"))):
        for line in open(path, encoding="utf-8"):
            if ":" in line:
                k, codes = line.split(":", 1)
                tags[k.strip()] = codes.split()
    for k in sorted(allep):
        items = [it for st in allep[k]["stories"] for it in st["items"]]
        codes = tags.get(k)
        if not codes or len(codes) != len(items):
            errors.append(f"{k}: tags missing or count mismatch ({len(codes or [])} vs {len(items)})")
            continue
        for it, c in zip(items, codes):
            m = re.fullmatch(r"(10|[1-9])([ab])", c)
            if not m:
                errors.append(f"{k}: bad tag {c!r}")
                continue
            it["th"] = int(m.group(1))
            it["lv"] = 1 if m.group(2) == "a" else 2
    # season completeness report
    made = {}
    for k in allep:
        made.setdefault(int(k[1:3]), []).append(int(k[4:6]))
    report = []
    for s, n in enumerate(COUNTS, 1):
        have = sorted(made.get(s, []))
        missing = [e for e in range(1, n + 1) if e not in have]
        report.append(f"S{s:02d}: {len(have)}/{n}" + (f" missing {missing[:6]}{'...' if len(missing) > 6 else ''}" if missing and have else ""))
    print("\n".join(report))
    print(f"episodes={len(allep)} phrases={len(seen)}")
    if errors:
        print("ERRORS:")
        print("\n".join(errors[:80]))
        if "--force" not in sys.argv:
            sys.exit(1)
    tpl = open(os.path.join(HERE, "template.html"), encoding="utf-8").read()
    out = tpl.replace("__EPISODES__", json.dumps(dict(sorted(allep.items())), ensure_ascii=False, separators=(",", ":")))
    dist = os.path.join(HERE, "dist")
    os.makedirs(dist, exist_ok=True)
    # artifact.html: body-only version for publishing as a claude.ai Artifact (the host adds <html>/<head>)
    open(os.path.join(dist, "artifact.html"), "w", encoding="utf-8").write(out)
    # index.html: full standalone page for opening locally or hosting anywhere
    page = ('<!doctype html>\n<html lang="zh-Hant">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width,initial-scale=1">\n</head>\n<body>\n'
            + out + '\n</body>\n</html>\n')
    open(os.path.join(dist, "index.html"), "w", encoding="utf-8").write(page)
    print(f"wrote dist/index.html and dist/artifact.html: {len(out.encode('utf-8'))//1024} KB")


if __name__ == "__main__":
    main()
