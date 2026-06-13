# Pipeline Orchestration And Public Analytics Design

## Objective

Upgrade the project from a well-structured collection of pipeline scripts into a more operational analytics product with:

- a single orchestrated execution path for `bronze -> silver -> features -> gold -> export`
- explicit artifact contracts across pipeline stages
- run-level metadata and manifest generation
- a stronger public analytical layer powered by the same canonical pipeline outputs

The goal is to make the repo read more like a real lakehouse-oriented data product and less like a set of strong but loosely coupled portfolio scripts.

## Problem

The current project already has good tests, good domain framing, and a polished public microsite, but two production-readiness gaps remain:

1. The execution flow is distributed across independent scripts with repeated path handling and no unified run-level metadata.
2. The public exports are strong, but they do not yet fully expose execution freshness, artifact lineage, or richer analytical summaries driven from a formal contract.

This means the repo demonstrates good engineering instincts, but not yet the full operational discipline expected from a more mature analytics platform.

## Scope

### In scope

- add a single pipeline runner that coordinates all stages
- centralize artifact paths and stage outputs under settings/contracts
- generate a `run_manifest.json` that captures pipeline execution metadata
- formalize expected artifacts for each stage
- enrich the public export payload and site snapshot with deeper analytical metadata
- add tests for orchestration, manifest generation, and public payload contract behavior

### Out of scope

- changing the core scoring philosophy of the gold layer
- replacing local JSONL artifacts with Delta/Databricks execution in this round
- redesigning the microsite visual identity from scratch
- broadening the live asset universe in the same pass unless needed by the public contract

## Chosen Approach

We will combine the two desired upgrades into one integrated design:

- **orchestration layer** as the system backbone
- **public analytics reinforcement** as a downstream consumer of that backbone

This is better than implementing them separately because the public layer should reflect the same execution truth as the pipeline itself. The site should not look like an independent demo; it should look like a published surface of a real analytical workflow.

## Architecture

### Current shape

```text
scripts/run_bronze.py
scripts/run_silver.py
scripts/run_features.py
scripts/run_gold.py
scripts/export_public_artifacts.py
```

Each script can run independently, but the project has no canonical orchestration state.

### Target shape

```text
run_pipeline
  -> stage runner
  -> artifact contract validation
  -> run manifest generation
  -> public export build
  -> site snapshot refresh
```

The new flow keeps the existing stage boundaries but adds an operational layer around them.

## Design Details

### 1. Orchestration Layer

Create a dedicated orchestration module that:

- executes the five existing stages in order
- reuses the existing stage logic instead of duplicating it
- collects per-stage metadata such as start time, end time, duration, status, and produced files
- optionally supports partial execution later, but does not need to expose complex CLI options in the first pass

The runner should be callable from:

- a new top-level script such as `scripts/run_pipeline.py`
- reusable Python code so tests can invoke it directly

### 2. Artifact Contract

Define a central artifact contract that declares:

- expected output files for each stage
- canonical directories for `bronze`, `silver`, `features`, `gold`, `public outputs`, and `site snapshot`
- validation helpers for existence and minimal shape

This contract should be the source of truth for both:

- the orchestration runner
- the public export stage

This avoids path drift and makes the repo easier to move into Databricks jobs later.

### 3. Run Manifest

Generate a `run_manifest.json` after orchestration finishes.

Minimum fields:

- `run_id`
- `generated_at`
- `pipeline_version`
- `stage_results`
- `artifact_summary`
- `overall_status`

Each stage entry should include:

- stage name
- status
- output files
- row counts where practical
- any warnings or notes

This manifest should be machine-readable and lightweight enough to be used in tests and publication logic.

### 4. Public Analytical Layer

Strengthen the public layer so the microsite reflects more than rankings.

The payload should gain:

- `run_id`
- `generated_at`
- `artifact_version` or equivalent version marker
- freshness metadata
- stronger summary metrics derived from the gold outputs
- richer narrative explorer context
- more explicit “why now” analytical framing through grouped driver/regime summaries

The site should continue using `site/site_data.js`, but that file should now be generated from a more explicit public payload contract.

### 5. Public Export Consistency

The following outputs should be built from the same run context:

- `outputs/crypto_attention_public.jsonl`
- `outputs/crypto-market-intelligence-summary.md`
- `site/site_data.js`
- `run_manifest.json`

This ensures the public and local portfolio surfaces reflect the same snapshot and do not silently drift.

## File-Level Plan

### New files

- `src/orchestration/__init__.py`
- `src/orchestration/contracts.py`
- `src/orchestration/pipeline_runner.py`
- `scripts/run_pipeline.py`
- tests covering runner and manifest behavior

### Modified files

- `src/config/settings.py`
  Add centralized directories and runner-facing config.
- `scripts/run_bronze.py`
- `scripts/run_silver.py`
- `scripts/run_features.py`
- `scripts/run_gold.py`
- `scripts/export_public_artifacts.py`
  Refactor so stage logic is callable from orchestration instead of only from `main()`.
- public payload tests and site payload tests

## Data Flow

### Orchestration

1. Load settings
2. Resolve artifact contract paths
3. Run bronze
4. Validate bronze outputs
5. Run silver
6. Validate silver outputs
7. Run features
8. Validate feature outputs
9. Run gold
10. Validate gold outputs
11. Run public export
12. Build final manifest

### Public export

1. Read gold outputs
2. Read supporting feature outputs
3. Read manifest metadata
4. Build public JSONL
5. Build Markdown summary
6. Build site payload
7. Write `site/site_data.js`

## Error Handling

The runner should fail fast when a stage does not produce required artifacts.

Expected behavior:

- stage status is recorded as failed in memory
- final exception is raised for non-successful runs
- manifest writing should still be attempted when possible so failed runs leave evidence

We do not need full retry logic in this round.

## Testing Strategy

### New tests

- runner executes all stages in order against fixture-like local artifacts
- manifest includes expected keys and stage summaries
- artifact contract validation catches missing outputs
- public payload includes freshness/run metadata
- public export files remain internally consistent

### Existing tests to preserve

- gold scoring tests
- site payload tests
- secret hygiene tests
- settings tests

The final suite should still remain fast and local.

## Risks And Mitigations

### Risk: over-coupling the runner to current scripts

Mitigation:
- extract small reusable functions from scripts rather than embedding shell-like logic in the runner

### Risk: making the public payload too large or noisy

Mitigation:
- add metadata and summary depth, but keep the payload editorially curated

### Risk: changing too many paths at once

Mitigation:
- introduce contracts/settings first and reuse them incrementally in each stage

## Success Criteria

This round is successful if:

- the project has one canonical local pipeline entrypoint
- artifact locations are centrally defined
- each run produces a machine-readable manifest
- public exports and site snapshot come from the same orchestrated run context
- the microsite payload becomes analytically deeper and more trustworthy
- tests cover the new operational layer without weakening the current suite

## Why This Improves Portfolio Strength

After this change, the project will demonstrate:

- analytics engineering discipline
- pipeline observability and reproducibility
- cleaner separation between stage logic and execution orchestration
- stronger Databricks/lakehouse migration readiness
- a public-facing analytical surface that looks like a published product, not just a demo
