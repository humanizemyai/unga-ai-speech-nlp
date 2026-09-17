"""Clean pdftotext output of gadebate English-only statements into paste-like text.
Removes page furniture ("Check against delivery", page numbers, form feeds), re-joins hard wraps and
hyphenated line breaks, collapses runs of spaces (so the live-detector double-space bug cannot fire),
and writes out/gadebate_texts.jsonl rows {id, year, slug, source, text}."""
import json, re, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
rows = [json.loads(l) for l in open(ROOT / "data/gadebate/pdf_map.jsonl") if l.strip()]
FURN = re.compile(r"^(check against delivery|please check against delivery|\d{1,3}|page \d+( of \d+)?|as delivered)$", re.I)
n = 0
with open(ROOT / "out/gadebate_texts.jsonl", "w") as fo:
    for r in rows:
        t = r.get("txt")
        if not t or not pathlib.Path(t).exists(): continue
        raw = pathlib.Path(t).read_text(encoding="utf-8", errors="replace").replace("\f", "\n")
        paras, cur = [], []
        for line in raw.split("\n"):
            s = re.sub(r"[ \t ]+", " ", line).strip()
            if not s or FURN.match(s):
                if cur and not s: paras.append(" ".join(cur)); cur = []
                continue
            if cur and cur[-1].endswith("-") and not cur[-1].endswith(" -"):
                cur[-1] = cur[-1][:-1] + s
            else:
                cur.append(s)
            if re.search(r"[.!?:;\"”)]$", s) and len(s) < 60:  # short line ending a sentence = paragraph end
                paras.append(" ".join(cur)); cur = []
        if cur: paras.append(" ".join(cur))
        text = "\n\n".join(p for p in paras if len(p.split()) >= 3)
        if len(text.split()) < 300: continue
        fo.write(json.dumps({"id": f"{r['year']}_{r['slug']}", "year": r["year"], "iso": r["slug"], "source": "gadebate-en-pdf", "text": text}) + "\n"); n += 1
print("texts", n)
