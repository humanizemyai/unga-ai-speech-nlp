"""AI-register vocabulary rates per year and paired per-country change.
PRIMARY list = the 13 pure-stylistic words of our published human-convergence study (unchanged).
SECONDARY list = words LLM output over-uses in speeches; reported per word, never as the headline alone."""
import json, re, sys, collections, math
PRIMARY = {"delve": r"delv(?:e|es|ing|ed)", "intricate": r"intricat(?:e|ely|ies|acy|acies)", "underscore": r"underscor(?:e|es|ing|ed)",
           "showcase": r"showcas(?:e|es|ing|ed)", "nuanced": r"nuanc(?:e|ed|es)", "multifaceted": r"multifaceted", "tapestry": r"tapestr(?:y|ies)",
           "realm": r"realms?", "meticulous": r"meticulous(?:ly)?", "delineate": r"delineat(?:e|es|ing|ed)", "paramount": r"paramount",
           "myriad": r"myriad", "pivotal": r"pivotal"}
SECONDARY = {"testament": r"testament", "unwavering": r"unwavering(?:ly)?", "steadfast": r"steadfast(?:ly)?", "resonate": r"resonat(?:e|es|ing|ed)",
             "navigate": r"navigat(?:e|es|ing|ed)", "foster": r"foster(?:s|ing|ed)?", "harness": r"harness(?:es|ing|ed)?", "beacon": r"beacons?",
             "embark": r"embark(?:s|ing|ed)?", "landscape": r"landscapes?", "transformative": r"transformative", "crossroads": r"crossroads",
             "profound": r"profound(?:ly)?", "robust": r"robust(?:ly|ness)?", "seamless": r"seamless(?:ly)?", "bolster": r"bolster(?:s|ing|ed)?"}
W = re.compile(r"[A-Za-z][A-Za-z'\-]+")
def rates(text, pats):
    return {k: len(re.findall(r"\b" + v + r"\b", text, re.I)) for k, v in pats.items()}
rows = [json.loads(l) for l in open(sys.argv[1]) if l.strip()]
by = collections.defaultdict(lambda: [0, collections.Counter(), collections.Counter(), 0])
per = {}
for r in rows:
    w = len(W.findall(r["text"])); p = rates(r["text"], PRIMARY); s = rates(r["text"], SECONDARY)
    b = by[r["year"]]; b[0] += w; b[1].update(p); b[2].update(s); b[3] += 1
    per[(r["iso"], r["year"])] = (w, sum(p.values()), sum(s.values()))
print("year speeches words primary/10k secondary/10k top-primary")
for y in sorted(by):
    w, p, s, n = by[y]
    print(y, n, w, f"{sum(p.values())/w*1e4:.2f}", f"{sum(s.values())/w*1e4:.2f}", dict(p.most_common(3)))
pre = {2015, 2016, 2017, 2018, 2021, 2022}; post = {2024, 2025}
def pooled(iso, years, idx):
    w = sum(per[(iso, y)][0] for y in years if (iso, y) in per); c = sum(per[(iso, y)][idx] for y in years if (iso, y) in per)
    return (c / w * 1e4) if w else None
isos = sorted({i for i, _ in per})
for idx, name in ((1, "primary"), (2, "secondary")):
    up = down = same = 0
    for i in isos:
        a, b = pooled(i, pre, idx), pooled(i, post, idx)
        if a is None or b is None: continue
        if b > a: up += 1
        elif b < a: down += 1
        else: same += 1
    n = up + down
    k = max(up, down)
    pval = min(1.0, 2 * sum(math.comb(n, j) for j in range(k, n + 1)) / 2 ** n) if n else 1.0
    print(f"paired countries ({name}): up {up}, down {down}, tie {same}, two-sided sign test p={pval:.4g}")
