"""Final statistics and figures for the preprint. Inputs: out/gadebate_texts.jsonl. Outputs: tables/*.json, figures/*.png.
Pre = 2015-2018 + 2021-2022 (all before ChatGPT, 30 Nov 2022). Transition = 2023. Post = 2024-2025."""
import json, re, math, random, collections, pathlib
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
ROOT = pathlib.Path(__file__).resolve().parent.parent
exec(open(ROOT / "src/markers.py").read().split("W = re.compile")[0])
W = re.compile(r"[A-Za-z][A-Za-z'\-]+")
TOPICAL = {"bolster", "harness", "landscape", "navigate", "transformative"}   # 2022 rule, see NOTES.md
SPEECH = {k: v for k, v in SECONDARY.items() if k not in TOPICAL}
CONTROL = {"sovereignty": r"sovereignt(?:y|ies)", "cooperation": r"cooperation", "development": r"development", "security": r"security",
           "peace": r"peace", "dialogue": r"dialogue", "support": r"support(?:s|ed|ing)?", "people": r"peoples?"}
PRE, POST = {2015, 2016, 2017, 2018, 2021, 2022}, {2024, 2025}
rows = [json.loads(l) for l in open(ROOT / "out/gadebate_texts.jsonl") if l.strip()]
for r in rows:
    t = r["text"]; r["w"] = len(W.findall(t))
    r["c"] = {k: len(re.findall(r"\b" + v + r"\b", t, re.I)) for k, v in {**SPEECH, **PRIMARY, **CONTROL, **{k: SECONDARY[k] for k in TOPICAL}}.items()}
def s(r, keys): return sum(r["c"][k] for k in keys)
years = sorted({r["year"] for r in rows})
random.seed(20260917)
def boot(rs, keys, n=2000):
    vals = []
    for _ in range(n):
        smp = [rs[random.randrange(len(rs))] for _ in rs]
        w = sum(x["w"] for x in smp); vals.append(sum(s(x, keys) for x in smp) / w * 1e4)
    vals.sort(); return vals[int(.025 * n)], vals[int(.975 * n)]
out = {"n_speeches": len(rows), "words": sum(r["w"] for r in rows), "years": {}}
for y in years:
    rs = [r for r in rows if r["year"] == y]; w = sum(r["w"] for r in rs)
    rate = sum(s(r, SPEECH) for r in rs) / w * 1e4; lo, hi = boot(rs, SPEECH)
    crate = sum(s(r, CONTROL) for r in rs) / w * 1e4
    inc = sum(s(r, SPEECH) > 0 for r in rs) / len(rs) * 100
    unw = sum(r["c"]["unwavering"] > 0 for r in rs) / len(rs) * 100
    out["years"][y] = {"speeches": len(rs), "words": w, "speech_rate": round(rate, 2), "ci95": [round(lo, 2), round(hi, 2)],
                       "control_rate": round(crate, 1), "pct_speeches_any_speech_word": round(inc, 1), "pct_speeches_unwavering": round(unw, 1),
                       "primary_rate": round(sum(s(r, PRIMARY) for r in rs) / w * 1e4, 2)}
def pooled(ys, keys):
    rs = [r for r in rows if r["year"] in ys]; return sum(s(r, keys) for r in rs) / sum(r["w"] for r in rs) * 1e4
out["pre_post"] = {"speech_pre": round(pooled(PRE, SPEECH), 2), "speech_post": round(pooled(POST, SPEECH), 2),
                   "control_pre": round(pooled(PRE, CONTROL), 1), "control_post": round(pooled(POST, CONTROL), 1),
                   "primary_pre": round(pooled(PRE, PRIMARY), 2), "primary_post": round(pooled(POST, PRIMARY), 2)}
per_word = {}
for k in list(SPEECH) + sorted(TOPICAL):
    a, b = pooled(PRE, [k]) * 10, pooled(POST, [k]) * 10   # per 100k words
    per_word[k] = {"pre_per100k": round(a, 1), "y2022_per100k": round(pooled({2022}, [k]) * 10, 1), "post_per100k": round(b, 1),
                   "fold": round(b / a, 2) if a else None, "topical_excluded": k in TOPICAL,
                   "raw_pre": sum(r["c"][k] for r in rows if r["year"] in PRE), "raw_post": sum(r["c"][k] for r in rows if r["year"] in POST)}
out["per_word"] = per_word
EN = set(open(ROOT / "src/analysis2.py").read().split("ENGLISH_OFFICIAL = {")[1].split("}")[0].replace('"', "").replace("\n", "").split(","))
def paired(keys, pre, post, subset=None, minw=500):
    per = collections.defaultdict(lambda: {"pre": [0, 0], "post": [0, 0]})
    for r in rows:
        if subset and r["iso"] not in subset: continue
        g = "pre" if r["year"] in pre else "post" if r["year"] in post else None
        if g: per[r["iso"]][g][0] += r["w"]; per[r["iso"]][g][1] += s(r, keys)
    up = down = tie = 0; diffs = []
    for d in per.values():
        if d["pre"][0] < minw or d["post"][0] < minw: continue
        a = d["pre"][1] / d["pre"][0] * 1e4; b = d["post"][1] / d["post"][0] * 1e4; diffs.append(b - a)
        up += b > a; down += b < a; tie += b == a
    n = up + down; k = max(up, down)
    p = min(1.0, 2 * sum(math.comb(n, j) for j in range(k, n + 1)) / 2 ** n) if n else 1.0
    diffs.sort(); med = diffs[len(diffs) // 2] if diffs else None
    return {"countries": up + down + tie, "up": up, "down": down, "tie": tie, "sign_p": float(f"{p:.3g}"), "median_change_per10k": round(med, 2) if med is not None else None}
out["tests"] = {
    "speech_words_pre_vs_post": paired(SPEECH, PRE, POST),
    "speech_words_placebo_2015_18_vs_2021_22": paired(SPEECH, {2015, 2016, 2017, 2018}, {2021, 2022}),
    "control_words_pre_vs_post": paired(CONTROL, PRE, POST),
    "primary_academic_list_pre_vs_post": paired(PRIMARY, PRE, POST),
    "speech_words_english_official_only": paired(SPEECH, PRE, POST, EN),
    "all_16_speech_words_incl_topical": paired(list(SPEECH) + sorted(TOPICAL), PRE, POST),
}
(ROOT / "tables/results.json").write_text(json.dumps(out, indent=2))
print(json.dumps({k: out[k] for k in ("n_speeches", "words", "pre_post", "tests")}, indent=1))
for y in years: print(y, out["years"][y])
# Figure 1: yearly rate with CI, ChatGPT marker
fig, ax = plt.subplots(figsize=(7.2, 3.8), dpi=200)
xs = years; ys = [out["years"][y]["speech_rate"] for y in xs]
lo = [out["years"][y]["speech_rate"] - out["years"][y]["ci95"][0] for y in xs]; hi = [out["years"][y]["ci95"][1] - out["years"][y]["speech_rate"] for y in xs]
ax.errorbar(xs, ys, yerr=[lo, hi], fmt="o-", color="#EC4899", ecolor="#f4a6c9", capsize=3, lw=2)
ax.axvline(2022.9, color="#888", ls="--", lw=1); ax.text(2022.95, 1.0, "ChatGPT\n(Nov 2022)", fontsize=8, color="#555", va="bottom")
ax.set_xticks(xs); ax.set_ylabel("per 10,000 words"); ax.set_ylim(0, max(h + e for h, e in zip(ys, hi)) * 1.15)
ax.set_title("AI-favoured speech words in UN General Debate statements (English texts)", fontsize=10)
ax.spines[["top", "right"]].set_visible(False); fig.tight_layout(); fig.savefig(ROOT / "figures/fig1_yearly_rate.png"); plt.close(fig)
# Figure 2: per-word fold change
ks = sorted(SPEECH, key=lambda k: per_word[k]["fold"] or 0)
fig, ax = plt.subplots(figsize=(7.2, 3.8), dpi=200)
ax.barh(ks, [per_word[k]["fold"] for k in ks], color=["#EC4899" if per_word[k]["fold"] >= 1 else "#9ca3af" for k in ks])
ax.axvline(1, color="#555", lw=1); ax.set_xlabel("rate 2024-2025 / rate 2015-2022")
ax.set_title("Change per word (words with a topical rise before ChatGPT excluded)", fontsize=10)
ax.spines[["top", "right"]].set_visible(False); fig.tight_layout(); fig.savefig(ROOT / "figures/fig2_per_word_fold.png"); plt.close(fig)
# Figure 3: paired countries, three tests
labels = ["Speech words\n2015-22 vs 2024-25", "Placebo\n2015-18 vs 2021-22", "Control words\n2015-22 vs 2024-25"]
tt = [out["tests"]["speech_words_pre_vs_post"], out["tests"]["speech_words_placebo_2015_18_vs_2021_22"], out["tests"]["control_words_pre_vs_post"]]
fig, ax = plt.subplots(figsize=(7.2, 3.4), dpi=200); x = range(3)
ax.bar([i - 0.18 for i in x], [t["up"] for t in tt], width=0.36, color="#EC4899", label="countries up")
ax.bar([i + 0.18 for i in x], [t["down"] for t in tt], width=0.36, color="#9ca3af", label="countries down")
for i, t in enumerate(tt): ax.text(i, max(t["up"], t["down"]) + 3, f"p = {t['sign_p']:.2g}", ha="center", fontsize=8)
ax.set_xticks(list(x)); ax.set_xticklabels(labels, fontsize=8); ax.set_ylabel("countries"); ax.legend(frameon=False, fontsize=8, loc="upper right", bbox_to_anchor=(1.0, 1.02)); ax.set_ylim(0, 85)
ax.set_title("Each country compared with its own earlier speeches", fontsize=10)
ax.spines[["top", "right"]].set_visible(False); fig.tight_layout(); fig.savefig(ROOT / "figures/fig3_paired_tests.png"); plt.close(fig)
print("figures ok")
