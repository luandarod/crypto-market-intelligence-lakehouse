# Crypto Market Intelligence Lakehouse

A Databricks-oriented crypto market intelligence platform built to answer a practical research question:

Which crypto assets and narratives deserve attention right now, and why?

This project is intentionally framed as an analytics engineering and market intelligence product, not as a price-prediction toy. The pipeline ingests public crypto data, organizes it into medallion-style layers, computes feature families across multiple market surfaces, and produces a gold layer with asset-level attention, narrative-level attention, and interpretable drivers.

## Why This Is A Strong Portfolio Project

- It shows lakehouse-style thinking instead of notebook-only analysis.
- It combines data engineering, feature design, and market reasoning in one project.
- It uses current crypto concepts such as funding, open interest, relative strength, and capital efficiency.
- It produces outputs that a hiring manager can understand quickly and a technical reviewer can inspect deeply.

## Current Stack

- Databricks bundle scaffold in [`databricks.yml`](databricks.yml)
- Python 3.11, PySpark, requests, Pydantic, PyYAML, and pytest in [`pyproject.toml`](pyproject.toml)
- Public data sources: CoinGecko, Binance, DefiLlama
- Local JSONL artifacts standing in for Delta-style pipeline stages during development

## Pipeline

The project currently runs as a local `bronze -> silver -> features -> gold` pipeline and is structured to translate cleanly into Databricks jobs and medallion tables later.

```text
Public APIs
  -> bronze snapshots
  -> silver normalized tables
  -> feature tables
  -> gold attention outputs
  -> public portfolio exports
  -> static microsite snapshot
```

Main scripts:

- `scripts/run_bronze.py`
- `scripts/run_silver.py`
- `scripts/run_features.py`
- `scripts/run_gold.py`
- `scripts/export_public_artifacts.py`
- `scripts/run_pipeline.py`

## Repository Structure

```text
src/         pipeline and domain logic
scripts/     runnable pipeline stages
site/        static portfolio microsite
docs/        architecture and publishing docs
resources/   Databricks bundle scaffolding
tests/       focused unit and pipeline tests
```

## What The Gold Layer Produces

- `attention.jsonl`: ranked asset attention output
- `drivers.jsonl`: interpretable regime and crowding-style flags
- `narratives.jsonl`: aggregated narrative-level attention

The current gold logic combines:

- quote volume
- 24h and 7d relative strength
- derivatives positioning via open interest
- on-chain confirmation via capital efficiency
- regime tagging from recent directional consistency

Key code:

- `src/gold/attention_engine.py`
- `src/gold/explanations.py`

## Covered Narratives And Universe

The initial universe is curated on purpose so the output feels like a research product rather than an indiscriminate API dump.

- Narratives include bitcoin ecosystem, ethereum ecosystem, layer 1, layer 2, DeFi, restaking/modular, AI/data, meme/social beta, RWA, and DePIN/infrastructure
- The current supported asset universe and exclusions live in `src/domain/asset_universe.py`
- Narrative seeds live in `src/domain/narratives.py`

## Quickstart

1. Create and activate a Python 3.11 environment.
2. Install dependencies with `pip install -e .`
3. Run tests with `pytest tests -v`
4. Run the canonical local pipeline:

```powershell
python scripts/run_pipeline.py
```

This canonical entrypoint executes the full `bronze -> silver -> features -> gold -> public` flow and writes:

- stage artifacts under `artifacts/`
- public exports under `artifacts/public/`
- a microsite snapshot at `site/site_data.js`
- a run manifest at `artifacts/public/run_manifest.json`

If you want to run individual stages instead, use:

```powershell
python scripts/run_bronze.py
python scripts/run_silver.py
python scripts/run_features.py
python scripts/run_gold.py
python scripts/export_public_artifacts.py
```

If your machine has local SSL trust issues for public APIs, set `PUBLIC_SSL_VERIFY=false` in the environment before running the bronze step.

## Microsite

The repository includes a premium static case-study microsite in [`site/`](site/).

Important files:

- [`site/index.html`](site/index.html)
- [`site/styles.css`](site/styles.css)
- [`site/app.js`](site/app.js)
- [`site/site_data.js`](site/site_data.js)
- [`site/README.md`](site/README.md)

Whenever you rerun `python scripts/run_pipeline.py` or `python scripts/export_public_artifacts.py`, the embedded microsite snapshot is refreshed together with the local public exports.

For Vercel deployment, the repo includes [`vercel.json`](vercel.json).

The repository also includes an automated GitHub Actions refresh workflow in [`.github/workflows/refresh_snapshot.yml`](.github/workflows/refresh_snapshot.yml). It supports both manual runs and a scheduled refresh cadence, updating the committed `site/site_data.js` snapshot that powers the public app.

## Local Public Exports

The canonical runner writes public-facing artifacts into `artifacts/public/`, including:

- `crypto_attention_public.jsonl`
- `crypto-market-intelligence-summary.md`
- `run_manifest.json`

The committed public artifact inside the repo remains `site/site_data.js`, which powers the microsite and app surfaces.

## Databricks Direction

The current repo already includes the first deployment-oriented placeholders:

- [`databricks.yml`](databricks.yml)
- [`resources/jobs/pipeline_job.yml`](resources/jobs/pipeline_job.yml)
- [`resources/pipelines/lakehouse_pipeline.yml`](resources/pipelines/lakehouse_pipeline.yml)

The local JSONL workflow is the development path. The intended next evolution is to materialize these stages as Databricks jobs and Delta-backed medallion tables.

## Documentation

- [`docs/architecture.md`](docs/architecture.md)
- [`docs/data_model.md`](docs/data_model.md)
- [`docs/feature_catalog.md`](docs/feature_catalog.md)
- [`docs/source_inventory.md`](docs/source_inventory.md)
- [`docs/publication_plan.md`](docs/publication_plan.md)

## Testing

Focused tests cover:

- ingestion clients and persistence
- silver normalization
- feature generation
- gold scoring and explanations
- public export formatting
- microsite publishing files

Run:

```powershell
pytest tests -v
```

## License

This project is released under the [MIT License](LICENSE).
