"""Fetch gadebate.un.org country pages + English-only statement PDFs, sessions 2015-2018 and 2021-2025.
English-only = the page links a PDF whose language tag is _en and no PDF in another language.
Polite: 4 threads, ~0.2s pause per request. Resumable (skips files on disk)."""
import re, json, time, threading, queue, urllib.request, urllib.error, pathlib, subprocess
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36 (HumanizeMy research; hello@humanizemy.ai)"
ROOT = pathlib.Path(__file__).resolve().parent.parent / "data" / "gadebate"
SESS = {2015: 70, 2016: 71, 2017: 72, 2018: 73, 2021: 76, 2022: 77, 2023: 78, 2024: 79, 2025: 80}
slugs = [s for s in (ROOT / "slugs.txt").read_text().strip().split(",") if s]
LANG = re.compile(r"_(en|fr|es|sp|ar|ru|zh|ch|cn|pt|de|other)(?=[_.])", re.I)
def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=40) as r: return r.status, r.read()
    except urllib.error.HTTPError as e: return e.code, b""
    except Exception: return -1, b""
q = queue.Queue(); [q.put((y, s)) for y in SESS for s in slugs]
out = []; lock = threading.Lock()
def work():
    while True:
        try: y, s = q.get_nowait()
        except queue.Empty: return
        sess = SESS[y]; h = ROOT / "html" / f"{sess}_{s}.html"
        if h.exists(): html = h.read_bytes()
        else:
            code, html = get(f"https://gadebate.un.org/en/{sess}/{s}"); time.sleep(0.2)
            if code != 200: continue
            h.write_bytes(html)
        pdfs = sorted(set(re.findall(r"gastatements/[^\"'\s]+?\.pdf", html.decode("utf-8", "replace"), re.I)))
        langs = {(LANG.search(p.split("/")[-1]).group(1).lower() if LANG.search(p.split("/")[-1]) else "?") for p in pdfs}
        en = [p for p in pdfs if re.search(r"_en(?=[_.])", p.split("/")[-1], re.I)]
        rec = {"year": y, "session": sess, "slug": s, "pdfs": pdfs, "langs": sorted(langs), "en_only": bool(en) and langs == {"en"}}
        if rec["en_only"]:
            pdf = ROOT / "pdf" / f"{y}_{s}.pdf"
            if not pdf.exists():
                code, data = get("https://gadebate.un.org/sites/default/files/" + en[0]); time.sleep(0.2)
                if code == 200 and data[:4] == b"%PDF": pdf.write_bytes(data)
            if pdf.exists():
                txt = ROOT / "txt" / f"{y}_{s}.txt"
                if not txt.exists(): subprocess.run(["pdftotext", "-layout" if False else "-raw", str(pdf), str(txt)], check=False)
                rec["txt"] = str(txt) if txt.exists() else None
        with lock: out.append(rec)
for d in ("html", "pdf", "txt"): (ROOT / d).mkdir(parents=True, exist_ok=True)
ts = [threading.Thread(target=work) for _ in range(4)]; [t.start() for t in ts]; [t.join() for t in ts]
(ROOT / "pdf_map.jsonl").write_text("\n".join(json.dumps(r) for r in sorted(out, key=lambda r: (r["year"], r["slug"]))) + "\n")
by = {}
for r in out:
    if r.get("txt"): by[r["year"]] = by.get(r["year"], 0) + 1
print("pages", len(out), "english-only texts by year", dict(sorted(by.items())))
