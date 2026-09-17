"""Robustness checks on gadebate English-only statements (written 2026-09-16 BEFORE seeing these outputs).
Rule for topical exclusion (objective, decided before running): drop any SECONDARY word whose 2022 rate
(pre-ChatGPT, Sept 2022) was already >= 1.5x its 2015-2021 rate. Those rose for topical reasons.
Checks:
 A. paired per-country sign test pre (2015-2022) vs post (2024-2025) for: PRIMARY, SECONDARY, SECONDARY-minus-topical
 B. placebo: same test 2015-2018 vs 2021-2022 (both pre-ChatGPT) must show no rise
 C. control words with no LLM association must not rise
 D. English-official-language countries only (rules out AI translation of non-English speeches)"""
import json, re, math, collections
exec(open("src/markers.py").read().split("W = re.compile")[0])
W = re.compile(r"[A-Za-z][A-Za-z'\-]+")
CONTROL = {"sovereignty": r"sovereignt(?:y|ies)", "cooperation": r"cooperation", "development": r"development", "security": r"security",
           "peace": r"peace", "dialogue": r"dialogue", "support": r"support(?:s|ed|ing)?", "people": r"peoples?"}
rows = [json.loads(l) for l in open("out/gadebate_texts.jsonl") if l.strip()]
def count(t, pats): return sum(len(re.findall(r"\b" + v + r"\b", t, re.I)) for v in pats.values())
def rate_group(ys, pats):
    w = sum(len(W.findall(r["text"])) for r in rows if r["year"] in ys); c = sum(count(r["text"], pats) for r in rows if r["year"] in ys)
    return c / w * 1e4
base = {2015, 2016, 2017, 2018, 2021}
topical = {k: v for k, v in SECONDARY.items() if rate_group({2022}, {k: v}) >= 1.5 * max(rate_group(base, {k: v}), 1e-9)}
SEC_CLEAN = {k: v for k, v in SECONDARY.items() if k not in topical}
print("topical words excluded by the 2022 rule:", sorted(topical))
ENGLISH_OFFICIAL = {"antigua-and-barbuda","australia","bahamas","barbados","belize","botswana","cameroon","canada","dominica","eswatini","fiji","gambia-republic","ghana","grenada","guyana","india","ireland","jamaica","kenya","kiribati","lesotho","liberia","malawi","malta","marshall-islands","mauritius","micronesia-federated-states","namibia","nauru","new-zealand","nigeria","pakistan","palau","papua-new-guinea","philippines","rwanda","saint-kitts-and-nevis","saint-lucia","saint-vincent-and-grenadines","samoa","seychelles","sierra-leone","singapore","solomon-islands","south-africa","south-sudan","sudan","tonga","trinidad-and-tobago","tuvalu","uganda","united-kingdom-great-britain-and-northern-ireland","united-republic-tanzania","united-states-america","vanuatu","zambia","zimbabwe"}
def sign_test(pats, pre, post, subset=None):
    per = collections.defaultdict(lambda: collections.defaultdict(lambda: [0, 0]))
    for r in rows:
        if subset and r["iso"] not in subset: continue
        g = "pre" if r["year"] in pre else "post" if r["year"] in post else None
        if not g: continue
        per[r["iso"]][g][0] += len(W.findall(r["text"])); per[r["iso"]][g][1] += count(r["text"], pats)
    up = down = tie = 0; ratios = []
    for iso, d in per.items():
        if d["pre"][0] < 500 or d["post"][0] < 500: continue
        a = d["pre"][1] / d["pre"][0]; b = d["post"][1] / d["post"][0]
        up += b > a; down += b < a; tie += b == a
    n = up + down; k = max(up, down)
    p = min(1.0, 2 * sum(math.comb(n, j) for j in range(k, n + 1)) / 2 ** n) if n else 1.0
    return up, down, tie, p
PRE, POST = {2015, 2016, 2017, 2018, 2021, 2022}, {2024, 2025}
print("\nA. pre 2015-2022 vs post 2024-2025 (countries with >=500 words in both)")
for name, pats in (("primary(13, published list)", PRIMARY), ("secondary(16, speech LLM words)", SECONDARY), ("secondary minus topical", SEC_CLEAN)):
    u, d, t, p = sign_test(pats, PRE, POST); print(f"  {name:34s} rate {rate_group(PRE, pats):.2f} -> {rate_group(POST, pats):.2f} per10k | up {u} down {d} tie {t} p={p:.3g}")
print("\nB. placebo, both pre-ChatGPT: 2015-2018 vs 2021-2022")
for name, pats in (("primary", PRIMARY), ("secondary minus topical", SEC_CLEAN)):
    u, d, t, p = sign_test(pats, {2015, 2016, 2017, 2018}, {2021, 2022}); print(f"  {name:34s} rate {rate_group({2015,2016,2017,2018}, pats):.2f} -> {rate_group({2021,2022}, pats):.2f} | up {u} down {d} p={p:.3g}")
print("\nC. control words (no LLM association)")
u, d, t, p = sign_test(CONTROL, PRE, POST); print(f"  control rate {rate_group(PRE, CONTROL):.1f} -> {rate_group(POST, CONTROL):.1f} per10k | up {u} down {d} p={p:.3g}")
print("\nD. English-official-language countries only")
for name, pats in (("primary", PRIMARY), ("secondary minus topical", SEC_CLEAN)):
    u, d, t, p = sign_test(pats, PRE, POST, ENGLISH_OFFICIAL); print(f"  {name:34s} up {u} down {d} p={p:.3g}")
print("\nper-year secondary-minus-topical rate:", {y: round(rate_group({y}, SEC_CLEAN), 2) for y in sorted({r['year'] for r in rows})})
