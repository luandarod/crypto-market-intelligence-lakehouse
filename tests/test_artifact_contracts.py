from pathlib import Path

from src.config.settings import AppSettings
from src.orchestration.contracts import build_artifact_contracts


def test_build_artifact_contracts_exposes_stage_outputs(tmp_path: Path) -> None:
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
    assert contracts["silver"].required_files == [
        "market.jsonl",
        "derivatives.jsonl",
        "onchain.jsonl",
    ]
    assert contracts["features"].required_files == [
        "market_features.jsonl",
        "derivatives_features.jsonl",
        "onchain_features.jsonl",
    ]
    assert contracts["gold"].required_files == [
        "attention.jsonl",
        "drivers.jsonl",
        "narratives.jsonl",
    ]
    assert contracts["public"].required_files == [
        "crypto_attention_public.jsonl",
        "crypto-market-intelligence-summary.md",
        "run_manifest.json",
    ]
    assert contracts["site"].required_files == ["site_data.js"]
    assert contracts["features"].resolve_outputs() == [
        tmp_path / "artifacts" / "features" / "market_features.jsonl",
        tmp_path / "artifacts" / "features" / "derivatives_features.jsonl",
        tmp_path / "artifacts" / "features" / "onchain_features.jsonl",
    ]
    assert contracts["site"].resolve_outputs() == [tmp_path / "site" / "site_data.js"]
