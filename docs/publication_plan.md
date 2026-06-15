# Publication Plan

## Publication Strategy

This project should be published in layers so it reads like a real platform:

1. GitHub repository for code, architecture, tests, and reproducibility
2. Databricks-facing deployment scaffold for platform credibility
3. Public portfolio artifacts for fast consumption by recruiters and hiring managers

## What Already Exists

- A repo scaffold with pipeline code, tests, and Databricks bundle placeholders
- Public exports in `artifacts/public/`
- Editorial summary generation via `scripts/export_public_artifacts.py`
- A canonical local runner in `scripts/run_pipeline.py`
- A run manifest in `artifacts/public/run_manifest.json`

## Recommended Public Surface

### Repository

The repo should lead with:

- the problem statement
- why the project matters
- architecture
- current feature families
- sample gold output
- roadmap to a fuller Databricks implementation

### Portfolio Case Study

Use the exported summary in `artifacts/public/crypto-market-intelligence-summary.md` as the seed for:

- a portfolio page
- a Notion case study
- a Vercel microsite

The page should emphasize:

- lakehouse framing
- current market concepts
- explainability of the gold layer
- distinction between market intelligence and naive price prediction

### Public Data Sample

Publish `artifacts/public/crypto_attention_public.jsonl` as a lightweight sample of the gold layer.

### Operational Credibility Layer

The public surface should also point to the execution layer:

- `scripts/run_pipeline.py` as the canonical local entrypoint
- `artifacts/public/run_manifest.json` as proof of stage-level orchestration
- `site/site_data.js` as the exported payload used by both the case-study page and the embedded app

## Suggested Sequence

1. Run `python scripts/run_pipeline.py` to refresh the full local execution chain
2. Finalize repository docs around the canonical run flow and exported artifacts
3. Add visual architecture and sample output excerpts
4. Publish repo
5. Promote the public page and embedded app built on top of `site/site_data.js`
6. Later, replace local artifacts with fuller Databricks execution screenshots or Delta-backed runs
