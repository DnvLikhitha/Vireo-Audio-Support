# Tech Stack: Vireo Support Insight Tool

## Principles

1. Small and runnable beats large and broken.
2. Zero marginal cost per run: no per-ticket model calls (Finance constraint).
3. One install command and one run command from a clean machine.
4. Everything reproducible from the raw CSVs.

## Chosen stack

| Layer | Choice | Why |
|---|---|---|
| Language | Python 3.11+ | Fastest route for data work; reviewers can read it |
| Data handling | pandas | CSVs are small (about 12k tickets, 15.5k orders); no database needed |
| Stats and adjustment | statsmodels or scikit-learn (linear regression) | Mix-adjusted CSAT and confidence intervals |
| Text classification | Keyword rules first; optional TF-IDF + logistic regression as a comparison | Free to run, explainable, easy to validate |
| Dashboard | Streamlit | One file, runs locally, interactive tables and charts |
| Charts | Plotly (via Streamlit) | Quick interactive charts |
| Tests | pytest | Checks for the timezone fix, join coverage, blank-CSAT handling |
| Packaging | `requirements.txt` plus a README with exact commands | Works on a clean machine |

## Where an LLM is (and is not) used

- **Offline, small sample only:** to propose root-cause themes and draft labels for a few hundred tickets. Estimated cost: a few hundred rupees at most. Log provider, model, tokens and cost in the submission form.
- **Never at runtime.** No API keys needed to run the tool.
- **Coding assistant:** Claude Code for building. Declare it, with approximate usage and what was discarded.

## Project layout

```
vireo-support/
  README.md
  requirements.txt
  data/                # raw CSVs (not committed if client-confidential)
  src/
    load_clean.py      # load, timezone fix, dedupe, joins, data-quality report
    metrics.py         # CSAT, handle time, breaches, costs
    adjust.py          # mix-adjusted CSAT
    lots.py            # lot analysis and early-warning backtest
    classify.py        # rule-based text classifier
  app.py               # Streamlit dashboard
  tests/
  validation/
    labelled_sample.csv
    validation_report.md
  outputs/
    data_quality.md
    assumptions.md
```

## Run commands (to appear in the README)

- Install: `pip install -r requirements.txt`
- Run: `streamlit run app.py`
- Tests: `pytest`

## Alternatives considered and rejected

| Option | Why not |
|---|---|
| Per-ticket LLM classification | About Rs 60,000 per run at Rs 5 per ticket; rejected by Finance |
| Power BI or Tableau | Slower to set up, harder to start from a README on a clean machine |
| Database (SQLite, DuckDB) | Data is small; adds setup for no gain |
| Deep-learning text model | Unnecessary; harder to explain and validate in 5 hours |
| Web framework (Flask, React) | Too much build time for the value |

## Known limits

- Streamlit is for local use only; no auth or multi-user support.
- Rule-based classifiers miss unusual phrasing; the validation sample quantifies this.
- The case-mix model is linear and simple, and cannot separate team from person.
