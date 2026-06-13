# Pipeline Orchestration And Public Analytics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a canonical pipeline runner with artifact contracts and run manifests, then wire the public export and microsite payload to the same execution truth so the repo behaves like a more operational analytics product.

**Architecture:** Keep the current `bronze -> silver -> features -> gold -> export` stage boundaries, but move shared path logic into config, formalize stage output contracts, and add an orchestration layer that records stage metadata in a run manifest. Refactor the public export to consume manifest-aware artifacts and expose richer analytical/freshness metadata to `outputs/` and `site/site_data.js`.

**Tech Stack:** Python 3.11, requests, Pydantic, pytest, JSONL artifacts, static JavaScript microsite, Databricks bundle scaffold

---

### Task 1: Centralize Artifact Paths And Contracts

**Files:**
- Create: `src/orchestration/__init__.py`
- Create: `src/orchestration/contracts.py`
- Modify: `src/config/settings.py`
- Test: `tests/test_artifact_contracts.py`

- [ ] **Step 1: Write the failing contract test**

```python
from pathlib import Path

from src.config.settings import AppSettings
from src.orchestration.contracts import build_artifact_contracts


def test_build_artifact_contracts_exposes_stage_outputs(tmp_path: Path):
    settings = AppSettings(
        bronze_output_dir=str(tmp_path / "artifacts" / "bronze"),
        silver_output_dir=str(tmp_path / "artifacts" / "silver"),
        features_output_dir=str(tmp_path / "artifacts" / "features"),
        gold_output_dir=str(tmp_path / "artifacts" / "gold"),
        public_export_dir=str(tmp_path / "artifacts" / "public"),
        site_output_dir=str(tmp_path / "site"),
    )

    contracts = build_artifact_contracts(settings)

    assert contracts["bronze"].required_files == ["public_sources.jsonl"]
    assert contracts["silver"].required_files == ["market.jsonl", "derivatives.jsonl", "onchain.jsonl"]
    assert contracts["gold"].required_files == ["attention.jsonl", "drivers.jsonl", "narratives.jsonl"]
    assert contracts["public"].required_files == [
        "crypto_attention_public.jsonl",
        "crypto-market-intelligence-summary.md",
        "run_manifest.json",
    ]
```

- [ ] **Step 2: Run the test to verify the expected failure**

Run:

```powershell
python -m pytest tests/test_artifact_contracts.py -v
```

Expected:

```text
FAIL ... ModuleNotFoundError or ImportError for src.orchestration.contracts
```

- [ ] **Step 3: Add missing settings fields for stage directories**

```python
import os

from pydantic import BaseModel


class AppSettings(BaseModel):
    coingecko_base_url: str = "https://api.coingecko.com/api/v3"
    binance_base_url: str = "https://fapi.binance.com"
    defillama_base_url: str = "https://api.llama.fi"
    bronze_output_dir: str = "artifacts/bronze"
    silver_output_dir: str = "artifacts/silver"
    features_output_dir: str = "artifacts/features"
    gold_output_dir: str = "artifacts/gold"
    public_export_dir: str = "artifacts/public"
    site_output_dir: str = "site"
    public_ssl_verify: bool = True

    @classmethod
    def from_env(cls) -> "AppSettings":
        raw_ssl = os.getenv("PUBLIC_SSL_VERIFY")
        ssl_verify = True if raw_ssl is None else raw_ssl.lower() not in {"0", "false", "no"}
        return cls(
            coingecko_base_url=os.getenv("COINGECKO_BASE_URL", "https://api.coingecko.com/api/v3"),
            binance_base_url=os.getenv("BINANCE_BASE_URL", "https://fapi.binance.com"),
            defillama_base_url=os.getenv("DEFILLAMA_BASE_URL", "https://api.llama.fi"),
            bronze_output_dir=os.getenv("BRONZE_OUTPUT_DIR", "artifacts/bronze"),
            silver_output_dir=os.getenv("SILVER_OUTPUT_DIR", "artifacts/silver"),
            features_output_dir=os.getenv("FEATURES_OUTPUT_DIR", "artifacts/features"),
            gold_output_dir=os.getenv("GOLD_OUTPUT_DIR", "artifacts/gold"),
            public_export_dir=os.getenv("PUBLIC_EXPORT_DIR", "artifacts/public"),
            site_output_dir=os.getenv("SITE_OUTPUT_DIR", "site"),
            public_ssl_verify=ssl_verify,
        )
```

- [ ] **Step 4: Implement artifact contract definitions**

```python
from dataclasses import dataclass
from pathlib import Path

from src.config.settings import AppSettings


@dataclass(frozen=True)
class ArtifactContract:
    stage_name: str
    root: Path
    required_files: list[str]

    def resolve_outputs(self) -> list[Path]:
        return [self.root / name for name in self.required_files]


def build_artifact_contracts(settings: AppSettings) -> dict[str, ArtifactContract]:
    return {
        "bronze": ArtifactContract("bronze", Path(settings.bronze_output_dir), ["public_sources.jsonl"]),
        "silver": ArtifactContract("silver", Path(settings.silver_output_dir), ["market.jsonl", "derivatives.jsonl", "onchain.jsonl"]),
        "features": ArtifactContract("features", Path(settings.features_output_dir), ["market_features.jsonl", "derivatives_features.jsonl", "onchain_features.jsonl"]),
        "gold": ArtifactContract("gold", Path(settings.gold_output_dir), ["attention.jsonl", "drivers.jsonl", "narratives.jsonl"]),
        "public": ArtifactContract("public", Path(settings.public_export_dir), ["crypto_attention_public.jsonl", "crypto-market-intelligence-summary.md", "run_manifest.json"]),
        "site": ArtifactContract("site", Path(settings.site_output_dir), ["site_data.js"]),
    }
```

- [ ] **Step 5: Run the contract test to verify it passes**

Run:

```powershell
python -m pytest tests/test_artifact_contracts.py -v
```

Expected:

```text
PASSED tests/test_artifact_contracts.py::test_build_artifact_contracts_exposes_stage_outputs
```

- [ ] **Step 6: Commit**

```powershell
git add src/config/settings.py src/orchestration/__init__.py src/orchestration/contracts.py tests/test_artifact_contracts.py
git commit -m "feat: add pipeline artifact contracts"
```

### Task 2: Refactor Stage Scripts Into Reusable Stage Functions

**Files:**
- Modify: `scripts/run_bronze.py`
- Modify: `scripts/run_silver.py`
- Modify: `scripts/run_features.py`
- Modify: `scripts/run_gold.py`
- Test: `tests/ingest/test_run_bronze.py`
- Test: `tests/silver/test_run_silver.py`
- Test: `tests/features/test_run_features.py`
- Test: `tests/gold/test_run_gold.py`

- [ ] **Step 1: Write a failing test for a reusable bronze stage function**

```python
from pathlib import Path

from src.config.settings import AppSettings
from scripts.run_bronze import run_bronze_stage


class StubCoinGeckoClient:
    def fetch_markets(self, vs_currency: str, page: int, per_page: int) -> list[dict]:
        return [{"id": "bitcoin", "symbol": "btc"}]


class StubBinanceClient:
    def fetch_open_interest(self, symbol: str) -> dict:
        return {"symbol": symbol, "openInterest": "123.45"}

    def fetch_funding_rate(self, symbol: str, limit: int = 1) -> list[dict]:
        return [{"symbol": symbol, "fundingRate": "0.01"}]


class StubDefiLlamaClient:
    def fetch_protocols(self) -> list[dict]:
        return [{"name": "Aave", "symbol": "aave"}]


def test_run_bronze_stage_writes_contract_output(tmp_path: Path):
    settings = AppSettings(bronze_output_dir=str(tmp_path / "artifacts" / "bronze"))

    output_path = run_bronze_stage(
        settings=settings,
        coingecko=StubCoinGeckoClient(),
        binance=StubBinanceClient(),
        defillama=StubDefiLlamaClient(),
    )

    assert output_path == Path(settings.bronze_output_dir) / "public_sources.jsonl"
    assert output_path.exists()
```

- [ ] **Step 2: Run the single test to verify it fails first**

Run:

```powershell
python -m pytest tests/ingest/test_run_bronze.py::test_run_bronze_stage_writes_contract_output -v
```

Expected:

```text
FAIL ... cannot import name 'run_bronze_stage'
```

- [ ] **Step 3: Extract callable stage functions from each script**

```python
def run_bronze_stage(
    *,
    settings: AppSettings,
    coingecko: CoinGeckoClient | None = None,
    binance: BinanceClient | None = None,
    defillama: DefiLlamaClient | None = None,
) -> Path:
    rows = collect_public_bronze_rows(
        coingecko=coingecko or CoinGeckoClient(base_url=settings.coingecko_base_url, verify_ssl=settings.public_ssl_verify),
        binance=binance or BinanceClient(base_url=settings.binance_base_url, verify_ssl=settings.public_ssl_verify),
        defillama=defillama or DefiLlamaClient(base_url=settings.defillama_base_url, verify_ssl=settings.public_ssl_verify),
    )
    output_path = PROJECT_ROOT / settings.bronze_output_dir / "public_sources.jsonl"
    write_jsonl_rows(output_path, rows)
    return output_path
```

```python
def run_silver_stage(settings: AppSettings) -> dict[str, Path]:
    bronze_path = PROJECT_ROOT / settings.bronze_output_dir / "public_sources.jsonl"
    bronze_rows = read_jsonl_rows(bronze_path)
    outputs = build_silver_outputs(bronze_rows)
    silver_root = PROJECT_ROOT / settings.silver_output_dir
    paths = {
        "market": silver_root / "market.jsonl",
        "derivatives": silver_root / "derivatives.jsonl",
        "onchain": silver_root / "onchain.jsonl",
    }
    write_jsonl_rows(paths["market"], outputs["market"])
    write_jsonl_rows(paths["derivatives"], outputs["derivatives"])
    write_jsonl_rows(paths["onchain"], outputs["onchain"])
    return paths
```

- [ ] **Step 4: Mirror the same extraction pattern for features and gold**

```python
def run_features_stage(settings: AppSettings) -> dict[str, Path]:
    silver_root = PROJECT_ROOT / settings.silver_output_dir
    feature_root = PROJECT_ROOT / settings.features_output_dir
    ...
    return {
        "market": feature_root / "market_features.jsonl",
        "derivatives": feature_root / "derivatives_features.jsonl",
        "onchain": feature_root / "onchain_features.jsonl",
    }


def run_gold_stage(settings: AppSettings) -> dict[str, Path]:
    feature_root = PROJECT_ROOT / settings.features_output_dir
    gold_root = PROJECT_ROOT / settings.gold_output_dir
    ...
    return {
        "attention": gold_root / "attention.jsonl",
        "drivers": gold_root / "drivers.jsonl",
        "narratives": gold_root / "narratives.jsonl",
    }
```

- [ ] **Step 5: Update existing script `main()` functions to call the extracted stage functions**

```python
def main() -> None:
    settings = AppSettings.from_env()
    output_path = run_bronze_stage(settings=settings)
    print(f"bronze snapshot saved to {output_path}")
```

- [ ] **Step 6: Run the focused stage tests**

Run:

```powershell
python -m pytest tests/ingest/test_run_bronze.py tests/silver/test_run_silver.py tests/features/test_run_features.py tests/gold/test_run_gold.py -v
```

Expected:

```text
PASSED ... existing stage tests
PASSED ... new reusable stage function test
```

- [ ] **Step 7: Commit**

```powershell
git add scripts/run_bronze.py scripts/run_silver.py scripts/run_features.py scripts/run_gold.py tests/ingest/test_run_bronze.py tests/silver/test_run_silver.py tests/features/test_run_features.py tests/gold/test_run_gold.py
git commit -m "refactor: expose reusable pipeline stage functions"
```

### Task 3: Add Manifest Models And Pipeline Runner

**Files:**
- Create: `src/orchestration/pipeline_runner.py`
- Test: `tests/test_pipeline_runner.py`

- [ ] **Step 1: Write the failing runner test**

```python
from pathlib import Path

from src.config.settings import AppSettings
from src.orchestration.pipeline_runner import run_pipeline


def test_run_pipeline_writes_run_manifest(tmp_path: Path, monkeypatch):
    settings = AppSettings(
        bronze_output_dir=str(tmp_path / "artifacts" / "bronze"),
        silver_output_dir=str(tmp_path / "artifacts" / "silver"),
        features_output_dir=str(tmp_path / "artifacts" / "features"),
        gold_output_dir=str(tmp_path / "artifacts" / "gold"),
        public_export_dir=str(tmp_path / "artifacts" / "public"),
        site_output_dir=str(tmp_path / "site"),
    )

    manifest_path = run_pipeline(settings=settings)

    assert manifest_path == Path(settings.public_export_dir) / "run_manifest.json"
    assert manifest_path.exists()
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```powershell
python -m pytest tests/test_pipeline_runner.py -v
```

Expected:

```text
FAIL ... ModuleNotFoundError or ImportError for src.orchestration.pipeline_runner
```

- [ ] **Step 3: Implement manifest helpers and stage result collection**

```python
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from src.config.settings import AppSettings
from src.orchestration.contracts import build_artifact_contracts
from scripts.export_public_artifacts import run_public_export_stage
from scripts.run_bronze import run_bronze_stage
from scripts.run_features import run_features_stage
from scripts.run_gold import run_gold_stage
from scripts.run_silver import run_silver_stage


def _count_jsonl_rows(path: Path) -> int | None:
    if path.suffix != ".jsonl" or not path.exists():
        return None
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
```

```python
def run_pipeline(settings: AppSettings | None = None) -> Path:
    settings = settings or AppSettings.from_env()
    contracts = build_artifact_contracts(settings)
    run_id = uuid4().hex
    stage_results = []

    stage_functions = [
        ("bronze", lambda: run_bronze_stage(settings=settings)),
        ("silver", lambda: run_silver_stage(settings=settings)),
        ("features", lambda: run_features_stage(settings=settings)),
        ("gold", lambda: run_gold_stage(settings=settings)),
        ("public", lambda: run_public_export_stage(settings=settings, run_id=run_id)),
    ]

    for stage_name, stage_fn in stage_functions:
        started_at = datetime.now(timezone.utc)
        stage_fn()
        contract = contracts[stage_name]
        outputs = contract.resolve_outputs()
        stage_results.append(
            {
                "stage": stage_name,
                "status": "success",
                "started_at": started_at.isoformat(),
                "finished_at": datetime.now(timezone.utc).isoformat(),
                "outputs": [str(path) for path in outputs],
                "row_counts": {path.name: _count_jsonl_rows(path) for path in outputs},
            }
        )

    manifest = {
        "run_id": run_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "pipeline_version": "0.1.0",
        "overall_status": "success",
        "stage_results": stage_results,
        "artifact_summary": {name: [str(path) for path in contract.resolve_outputs()] for name, contract in contracts.items()},
    }
    manifest_path = Path(settings.public_export_dir) / "run_manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest_path
```

- [ ] **Step 4: Add a failure-path test for missing artifacts**

```python
import pytest

from src.orchestration.pipeline_runner import validate_stage_outputs


def test_validate_stage_outputs_raises_when_required_output_is_missing(tmp_path):
    missing_path = tmp_path / "missing.jsonl"

    with pytest.raises(FileNotFoundError):
        validate_stage_outputs("bronze", [missing_path])
```

- [ ] **Step 5: Run the orchestration tests**

Run:

```powershell
python -m pytest tests/test_pipeline_runner.py tests/test_artifact_contracts.py -v
```

Expected:

```text
PASSED tests/test_pipeline_runner.py::test_run_pipeline_writes_run_manifest
PASSED tests/test_pipeline_runner.py::test_validate_stage_outputs_raises_when_required_output_is_missing
PASSED tests/test_artifact_contracts.py::test_build_artifact_contracts_exposes_stage_outputs
```

- [ ] **Step 6: Commit**

```powershell
git add src/orchestration/pipeline_runner.py tests/test_pipeline_runner.py
git commit -m "feat: add pipeline runner and run manifest"
```

### Task 4: Add A Canonical Run Script And Public Export Stage Wrapper

**Files:**
- Modify: `scripts/export_public_artifacts.py`
- Create: `scripts/run_pipeline.py`
- Test: `tests/gold/test_public_export.py`
- Test: `tests/test_publish_files.py`

- [ ] **Step 1: Write the failing test for a reusable public export stage**

```python
from pathlib import Path

from src.config.settings import AppSettings
from scripts.export_public_artifacts import run_public_export_stage


def test_run_public_export_stage_writes_site_payload_and_manifest_fields(tmp_path: Path):
    settings = AppSettings(
        gold_output_dir=str(tmp_path / "artifacts" / "gold"),
        features_output_dir=str(tmp_path / "artifacts" / "features"),
        public_export_dir=str(tmp_path / "artifacts" / "public"),
        site_output_dir=str(tmp_path / "site"),
    )

    outputs = run_public_export_stage(settings=settings, run_id="run-demo")

    assert outputs["public_jsonl"] == Path(settings.public_export_dir) / "crypto_attention_public.jsonl"
    assert outputs["site_snapshot"] == Path(settings.site_output_dir) / "site_data.js"
```

- [ ] **Step 2: Run the test to verify the expected failure**

Run:

```powershell
python -m pytest tests/gold/test_public_export.py::test_run_public_export_stage_writes_site_payload_and_manifest_fields -v
```

Expected:

```text
FAIL ... cannot import name 'run_public_export_stage'
```

- [ ] **Step 3: Extract a reusable export stage function**

```python
def run_public_export_stage(settings: AppSettings, run_id: str, manifest_path: Path | None = None) -> dict[str, Path]:
    gold_root = PROJECT_ROOT / settings.gold_output_dir
    features_root = PROJECT_ROOT / settings.features_output_dir
    ...
    payload = build_site_payload(
        attention_rows,
        narrative_rows,
        driver_rows=driver_rows,
        market_feature_rows=market_feature_rows,
        derivatives_feature_rows=derivatives_feature_rows,
        run_id=run_id,
        manifest_path=manifest_path,
    )
    ...
    return {
        "public_jsonl": public_jsonl_path,
        "summary_markdown": summary_path,
        "site_snapshot": site_data_path,
    }
```

- [ ] **Step 4: Add the single-entry script wrapper**

```python
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config.settings import AppSettings
from src.orchestration.pipeline_runner import run_pipeline


def main() -> None:
    settings = AppSettings.from_env()
    manifest_path = run_pipeline(settings=settings)
    print(f"pipeline run completed: {manifest_path}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run focused export and publish tests**

Run:

```powershell
python -m pytest tests/gold/test_public_export.py tests/test_publish_files.py -v
```

Expected:

```text
PASSED ... public export tests
PASSED ... publish file contract tests
```

- [ ] **Step 6: Commit**

```powershell
git add scripts/export_public_artifacts.py scripts/run_pipeline.py tests/gold/test_public_export.py tests/test_publish_files.py
git commit -m "feat: add canonical run script and export stage wrapper"
```

### Task 5: Strengthen The Public Site Payload

**Files:**
- Modify: `scripts/export_public_artifacts.py`
- Modify: `site/app.js`
- Test: `tests/gold/test_site_payload.py`
- Test: `tests/test_site_files.py`

- [ ] **Step 1: Write the failing payload metadata test**

```python
from scripts.export_public_artifacts import build_site_payload


def test_build_site_payload_includes_run_metadata_and_driver_summary():
    payload = build_site_payload(
        attention_rows=[
            {
                "symbol": "BTC",
                "narrative": "bitcoin_ecosystem",
                "attention_score": 8.35,
                "confirmation_score": 0.6667,
                "top_driver": "derivatives_positioning",
                "regime_tag": "bearish_attention",
            }
        ],
        narrative_rows=[
            {
                "narrative": "bitcoin_ecosystem",
                "asset_count": 1,
                "avg_attention_score": 8.35,
                "avg_confirmation_score": 0.6667,
            }
        ],
        run_id="run-demo",
        artifact_version="v1",
    )

    assert payload["run_metadata"]["run_id"] == "run-demo"
    assert payload["run_metadata"]["artifact_version"] == "v1"
    assert "driver_mix" in payload["overview"]
```

- [ ] **Step 2: Run the payload test to verify it fails**

Run:

```powershell
python -m pytest tests/gold/test_site_payload.py::test_build_site_payload_includes_run_metadata_and_driver_summary -v
```

Expected:

```text
FAIL ... missing run_metadata or unexpected keyword argument
```

- [ ] **Step 3: Extend `build_site_payload` with metadata and summary sections**

```python
def build_site_payload(
    attention_rows: list[dict],
    narrative_rows: list[dict],
    driver_rows: list[dict] | None = None,
    market_feature_rows: list[dict] | None = None,
    derivatives_feature_rows: list[dict] | None = None,
    run_id: str | None = None,
    artifact_version: str = "v1",
    manifest_path: Path | None = None,
) -> dict:
    driver_map = build_latest_symbol_map(driver_rows or [])
    driver_mix = {
        "derivatives_positioning": sum(1 for row in attention_rows if row["top_driver"] == "derivatives_positioning"),
        "onchain_confirmation": sum(1 for row in attention_rows if row["top_driver"] == "onchain_confirmation"),
        "volume_strength": sum(1 for row in attention_rows if row["top_driver"] == "volume_strength"),
    }
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "run_metadata": {
            "run_id": run_id,
            "artifact_version": artifact_version,
            "manifest_path": str(manifest_path) if manifest_path else None,
        },
        "overview": {
            ...,
            "driver_mix": driver_mix,
        },
        "narrative_health": [
            {
                "narrative": row["narrative"],
                "leader_symbol": next((asset["symbol"] for asset in attention_rows if asset["narrative"] == row["narrative"]), None),
                "avg_attention_score": row["avg_attention_score"],
                "avg_confirmation_score": row["avg_confirmation_score"],
            }
            for row in narrative_rows[:8]
        ],
        ...
    }
```

- [ ] **Step 4: Surface the new metadata in the site client**

```javascript
function renderRunMetadata(data) {
  const meta = data.run_metadata || {};
  const runId = meta.run_id || "local-run";
  const artifactVersion = meta.artifact_version || "v1";
  setText("snapshot-run-id", runId);
  setText("snapshot-artifact-version", artifactVersion);
}
```

```javascript
function renderOverview(data) {
  ...
  const driverMix = data.overview?.driver_mix || {};
  setText("driver-mix-volume", String(driverMix.volume_strength ?? 0));
  setText("driver-mix-derivatives", String(driverMix.derivatives_positioning ?? 0));
  setText("driver-mix-onchain", String(driverMix.onchain_confirmation ?? 0));
}
```

- [ ] **Step 5: Run site payload and file tests**

Run:

```powershell
python -m pytest tests/gold/test_site_payload.py tests/test_site_files.py -v
```

Expected:

```text
PASSED ... site payload tests
PASSED ... site file tests
```

- [ ] **Step 6: Commit**

```powershell
git add scripts/export_public_artifacts.py site/app.js tests/gold/test_site_payload.py tests/test_site_files.py
git commit -m "feat: enrich public analytics payload"
```

### Task 6: End-To-End Runner Coverage And Docs Refresh

**Files:**
- Modify: `README.md`
- Modify: `docs/publication_plan.md`
- Test: `tests/test_docs_exist.py`
- Test: `tests/test_publish_files.py`
- Test: `tests/test_bundle_files.py`

- [ ] **Step 1: Add an end-to-end runner smoke test**

```python
from pathlib import Path

from src.config.settings import AppSettings
from src.orchestration.pipeline_runner import run_pipeline


def test_run_pipeline_smoke_with_local_fixture_outputs(tmp_path: Path, monkeypatch):
    settings = AppSettings(
        bronze_output_dir=str(tmp_path / "artifacts" / "bronze"),
        silver_output_dir=str(tmp_path / "artifacts" / "silver"),
        features_output_dir=str(tmp_path / "artifacts" / "features"),
        gold_output_dir=str(tmp_path / "artifacts" / "gold"),
        public_export_dir=str(tmp_path / "artifacts" / "public"),
        site_output_dir=str(tmp_path / "site"),
    )

    manifest_path = run_pipeline(settings=settings)

    assert manifest_path.exists()
    assert (Path(settings.site_output_dir) / "site_data.js").exists()
```

- [ ] **Step 2: Run the smoke test to verify the whole orchestration path**

Run:

```powershell
python -m pytest tests/test_pipeline_runner.py::test_run_pipeline_smoke_with_local_fixture_outputs -v
```

Expected:

```text
PASSED tests/test_pipeline_runner.py::test_run_pipeline_smoke_with_local_fixture_outputs
```

- [ ] **Step 3: Update docs to expose the new execution model**

```markdown
## Canonical Local Run

Use the new runner to execute the full pipeline:

```powershell
python scripts/run_pipeline.py
```

This generates:

- stage artifacts under `artifacts/`
- public portfolio outputs
- `site/site_data.js`
- `artifacts/public/run_manifest.json`
```

- [ ] **Step 4: Run the docs and publication safety tests**

Run:

```powershell
python -m pytest tests/test_docs_exist.py tests/test_publish_files.py tests/test_bundle_files.py -v
```

Expected:

```text
PASSED ... docs and publish contract tests
```

- [ ] **Step 5: Run the complete suite**

Run:

```powershell
python -m pytest -q
```

Expected:

```text
all tests pass
```

- [ ] **Step 6: Commit**

```powershell
git add README.md docs/publication_plan.md tests/test_pipeline_runner.py tests/test_docs_exist.py tests/test_publish_files.py tests/test_bundle_files.py
git commit -m "docs: document orchestrated pipeline and public contract"
```
