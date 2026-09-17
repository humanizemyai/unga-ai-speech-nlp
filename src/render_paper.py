import markdown, pathlib, re
root = pathlib.Path(__file__).resolve().parent.parent
md = (root / "paper/paper.md").read_text()
css = (pathlib.Path.home() / "research/surprisal-arc-nlp/paper/paper.rendered.html").read_text().split("<style>")[1].split("</style>")[0]
css += "\nfigure{margin:10px 0} .caption{font-size:9pt;color:#444;text-align:center;margin:2px 0 12px}\n"
html = markdown.markdown(md, extensions=["tables"])
html = html.replace('src="../figures/', f'src="file://{root}/figures/')
html = re.sub(r'<p><img alt="([^"]+)" src="([^"]+)" /></p>', r'<figure><img alt="\1" src="\2" /><div class="caption">\1</div></figure>', html)
out = root / "paper/paper.rendered.html"
out.write_text(f"<!doctype html><html><head><meta charset='utf-8'><style>{css}</style></head><body>{html}</body></html>")
print(out)
