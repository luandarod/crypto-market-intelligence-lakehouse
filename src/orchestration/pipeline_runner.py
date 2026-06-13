import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from scripts.export_public_artifacts import run_public_export_stage
from scripts.run_bronze import run_bronze_stage
from scripts.run_features import run_features_stage
from scripts.run_gold import run_gold_stage
from scripts.run_silver import run_silver_stage
from src.config.settings import AppSettings
from src.orchestration.contracts import build_artifact_contracts


@dataclass(frozen=True)
class StageRunRecord:
    stage: str
    status: str
    started_at: str
    finished_at: str
    outputs: list[str]
    row_counts: dict[str, int | None]


@dataclass(frozen=True)
class RunManifest:
    run_id: str
    generated_at: str
    stages: list[StageRunRecord]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def validate_stage_outputs(stage_name: str, outputs: list[Path]) -> None:
    missing_outputs = [str(path) for path in outputs if not path.exists()]
    if missing_outputs:
        raise FileNotFoundError(f"{stage_name} stage missing required outputs: {', '.join(missing_outputs)}")


def _count_jsonl_rows(path: Path) -> int | None:
    if path.suffix != ".jsonl" or not path.exists():
        return None
    with path.open("r", encoding="utf-8") as handle:
        return sum(1 for line in handle if line.strip())


def _stage_record(stage_name: str, outputs: list[Path], *, started_at: str, finished_at: str) -> StageRunRecord:
    return StageRunRecord(
        stage=stage_name,
        status="completed",
        started_at=started_at,
        finished_at=finished_at,
        outputs=[str(path) for path in outputs],
        row_counts={str(path): _count_jsonl_rows(path) for path in outputs},
    )


def _run_stage(stage_name: str, outputs: list[Path], *, runner) -> StageRunRecord:
    started_at = _utc_now_iso()
    runner()
    validate_stage_outputs(stage_name, outputs)
    finished_at = _utc_now_iso()
    return _stage_record(stage_name, outputs, started_at=started_at, finished_at=finished_at)


def run_pipeline(settings: AppSettings | None = None) -> Path:
    resolved_settings = settings or AppSettings.from_env()
    contracts = build_artifact_contracts(resolved_settings)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")

    stage_records = [
        _run_stage(
            "bronze",
            contracts["bronze"].resolve_outputs(),
            runner=lambda: run_bronze_stage(settings=resolved_settings),
        ),
        _run_stage(
            "silver",
            contracts["silver"].resolve_outputs(),
            runner=lambda: run_silver_stage(resolved_settings),
        ),
        _run_stage(
            "features",
            contracts["features"].resolve_outputs(),
            runner=lambda: run_features_stage(resolved_settings),
        ),
        _run_stage(
            "gold",
            contracts["gold"].resolve_outputs(),
            runner=lambda: run_gold_stage(resolved_settings),
        ),
    ]

    manifest_path = contracts["public"].root / "run_manifest.json"
    public_stage_outputs = [
        contracts["public"].root / "crypto_attention_public.jsonl",
        contracts["public"].root / "crypto-market-intelligence-summary.md",
        manifest_path,
        contracts["site"].root / "site_data.js",
    ]
    public_started_at = _utc_now_iso()
    run_public_export_stage(resolved_settings)
    validate_stage_outputs("public", [path for path in public_stage_outputs if path != manifest_path])
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    public_finished_at = _utc_now_iso()
    public_record = _stage_record(
        "public",
        public_stage_outputs,
        started_at=public_started_at,
        finished_at=public_finished_at,
    )
    manifest = RunManifest(
        run_id=run_id,
        generated_at=_utc_now_iso(),
        stages=[*stage_records, public_record],
    )
    manifest_path.write_text(json.dumps(asdict(manifest), indent=2) + "\n", encoding="utf-8")

    validate_stage_outputs("public", contracts["public"].resolve_outputs())
    return manifest_path
