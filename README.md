# Data2Decision Hackathon

Team workspace for the Data2Decision Hackathon (November 2026).

## Where we are

| Phase | Status |
|---|---|
| M1 – Decide (problem canvas) | Done |
| M2 | **Waiting for the problem statement** |

## Problem statement (M2)

_To be added once it is released._

## Repo layout

```
data/raw/          original datasets (NOT committed: see below)
data/processed/    cleaned / feature-engineered data (NOT committed)
notebooks/         exploration and modelling notebooks, prefix with your initials (e.g. yv_01_eda.ipynb)
src/               reusable Python code (cleaning, features, model, evaluation)
outputs/figures/   charts for the deck
docs/              problem statement, canvas, slides, notes
```

## Data

Datasets are **not** pushed to GitHub (the repo is public and some datasets carry licences that
forbid redistribution). Put files in `data/raw/` on your own machine; `.gitignore` keeps them out.
Record each dataset's source link here:

- _dataset name – source link – licence_

## Getting started

```bash
git clone https://github.com/vasdevyash/data2decision-hackathon.git
cd data2decision-hackathon
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Working together

1. `git pull` before you start.
2. Work in your own notebook; don't edit someone else's without telling them.
3. Commit small and often with a clear message, then `git push`.
4. Clear notebook outputs that contain large tables before committing.

## Team

| Name | Role |
|---|---|
| Yash Vasdev | |
| | |
| | |
