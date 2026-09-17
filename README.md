# Unwavering, Steadfast, Pivotal: AI-favoured speech vocabulary in UN General Assembly statements (2015-2025)

HumanizeMy.ai Computational Linguistics Lab, Fırat Mıhcı, September 2026.

In 956 English-language statements that delegations published for the UN General Assembly's General Debate
(sessions 70-73 and 76-80, 1.85 million words), eleven ceremonial words that language models over-use
(*testament, unwavering, steadfast, resonate, beacon, embark, crossroads, profound, foster, robust, seamless*)
rose from **6.08 per 10,000 words in 2015-2022 to 12.19 in 2024-2025**. Compared with its own earlier statements,
the rate rose in 72 countries and fell in 36 (sign test p = 0.0007). A placebo comparison between two
pre-ChatGPT periods (p = 0.92) and ordinary diplomatic vocabulary (p = 0.18) show no comparable change, and the
rise persists in states where English is an official language (p = 0.027).

The study measures register, not authorship: it does not identify any statement as AI-written.

## Reproduce

```bash
pip install -r requirements.txt          # plus poppler for pdftotext
python src/fetch_gadebate.py             # downloads country pages + English-only statement PDFs from gadebate.un.org
python src/prep_gadebate.py              # cleans PDF text -> out/gadebate_texts.jsonl
python src/markers.py out/gadebate_texts.jsonl
python src/analysis2.py                  # topical exclusion rule, paired, placebo, control, English-official tests
python src/paper_stats.py                # tables/results.json + figures/
```

Run every command from the repository root.

## Contents

| Path | What it is |
|---|---|
| `data/gadebate/slugs.txt` | Country page slugs used on gadebate.un.org |
| `data/gadebate/pdf_map.jsonl` | Every country page fetched: session, linked PDFs, language tags, English-only flag |
| `tables/per_speech_counts.csv` | One row per statement: year, country, source PDF URL, word count, count of every tracked word |
| `tables/results.json` | Yearly rates with 95% bootstrap intervals, per-word table, all paired tests |
| `figures/` | Figures 1-3 of the paper |
| `paper/` | Preprint (Markdown and PDF) |

## Data note

We did not use the 2024 and 2025 releases of the UN General Debate Corpus for the trend analysis: its documentation
states that 2024 non-English statements were translated with GPT-4o and that 2025 was transcribed from interpretation
audio, which would contaminate an AI-vocabulary measurement. The delegations' own texts on gadebate.un.org were used instead.

## Cite

Mıhcı, F. (2026). *Unwavering, Steadfast, Pivotal: AI-Favoured Speech Vocabulary Doubled in UN General Assembly Statements After ChatGPT (2015-2025).* Preprint, ResearchGate. https://doi.org/10.13140/RG.2.2.29604.64645

Read the summary: https://humanizemy.ai/research/un-general-assembly-ai-speech-nlp
