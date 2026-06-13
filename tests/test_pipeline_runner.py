from pathlib import Path
import tempfile

import pytest

from src.bronze.writers import write_jsonl_rows
from src.config.settings import AppSettings
from src.orchestration.pipeline_runner import run_pipeline, validate_stage_outputs


def _build_settings(tmp_path: Path) -> AppSettings:
    return AppSettings(
        bronze_output_dir=str(tmp_path / "artifacts" / "bronze"),
        silver_output_dir=str(tmp_path / "artifacts" / "silver"),
        features_output_dir=str(tmp_path / "artifacts" / "features"),
        gold_output_dir=str(tmp_path / "artifacts" / "gold"),
        public_export_dir=str(tmp_path / "artifacts" / "public"),
        site_output_dir=str(tmp_path / "site"),
    )


@pytest.fixture
def tmp_path() -> Path:
    root = Path.cwd() / ".pytest_tmp"
    root.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=root) as temp_dir:
        yield Path(temp_dir)


def _install_stage_stubs(monkeypatch: pytest.MonkeyPatch) -> None:
    def stub_run_bronze_stage(*, settings: AppSettings) -> Path:
        output_path = Path(settings.bronze_output_dir) / "public_sources.jsonl"
        write_jsonl_rows(output_path, [{"source_name": "stub"}])
        return output_path

    def stub_run_silver_stage(settings: AppSettings) -> dict[str, Path]:
        root = Path(settings.silver_output_dir)
        outputs = {
            "market": root / "market.jsonl",
            "derivatives": root / "derivatives.jsonl",
            "onchain": root / "onchain.jsonl",
        }
        write_jsonl_rows(outputs["market"], [{"symbol": "BTC"}])
        write_jsonl_rows(outputs["derivatives"], [{"symbol": "BTCUSDT"}])
        write_jsonl_rows(outputs["onchain"], [{"symbol": "BTC"}])
        return outputs

    def stub_run_features_stage(settings: AppSettings) -> dict[str, Path]:
        root = Path(settings.features_output_dir)
        outputs = {
            "market": root / "market_features.jsonl",
            "derivatives": root / "derivatives_features.jsonl",
            "onchain": root / "onchain_features.jsonl",
        }
        write_jsonl_rows(
            outputs["market"],
            [
                {
                    "symbol": "BTC",
                    "close_price": 67000.0,
                    "quote_volume": 50000000000.0,
                    "relative_strength_24h": 2.5,
                    "relative_strength_7d": 4.0,
                    "relative_strength_30d": 8.0,
                }
            ],
        )
        write_jsonl_rows(
            outputs["derivatives"],
            [{"symbol": "BTCUSDT", "funding_rate": 0.0001, "open_interest": 12345.0}],
        )
        write_jsonl_rows(
            outputs["onchain"],
            [{"symbol": "BTC", "tvl_usd": 1.0, "dex_volume_usd": 1.0, "capital_efficiency": 1.0}],
        )
        return outputs

    def stub_run_gold_stage(settings: AppSettings) -> dict[str, Path]:
        root = Path(settings.gold_output_dir)
        outputs = {
            "attention": root / "attention.jsonl",
            "drivers": root / "drivers.jsonl",
            "narratives": root / "narratives.jsonl",
        }
        write_jsonl_rows(
            outputs["attention"],
            [
                {
                    "symbol": "BTC",
                    "narrative": "store_of_value",
                    "attention_score": 0.95,
                    "confirmation_score": 1.0,
                    "top_driver": "volume_strength",
                    "regime_tag": "bullish_attention",
                }
            ],
        )
        write_jsonl_rows(
            outputs["drivers"],
            [{"symbol": "BTC", "breadth_flag": "broad", "crowding_flag": "balanced", "regime_tag": "bullish_attention"}],
        )
        write_jsonl_rows(
            outputs["narratives"],
            [{"narrative": "store_of_value", "asset_count": 1, "avg_attention_score": 0.95, "avg_confirmation_score": 1.0}],
        )
        return outputs

    monkeypatch.setattr("src.orchestration.pipeline_runner.run_bronze_stage", stub_run_bronze_stage)
    monkeypatch.setattr("src.orchestration.pipeline_runner.run_silver_stage", stub_run_silver_stage)
    monkeypatch.setattr("src.orchestration.pipeline_runner.run_features_stage", stub_run_features_stage)
    monkeypatch.setattr("src.orchestration.pipeline_runner.run_gold_stage", stub_run_gold_stage)


def test_run_pipeline_writes_run_manifest(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    settings = _build_settings(tmp_path)
    _install_stage_stubs(monkeypatch)

    manifest_path = run_pipeline(settings=settings)

    assert manifest_path == Path(settings.public_export_dir) / "run_manifest.json"
    assert manifest_path.exists()


def test_validate_stage_outputs_raises_for_missing_files(tmp_path: Path):
    existing_path = tmp_path / "exists.jsonl"
    write_jsonl_rows(existing_path, [{"symbol": "BTC"}])
    missing_path = tmp_path / "missing.jsonl"

    with pytest.raises(FileNotFoundError, match="silver"):
        validate_stage_outputs("silver", [existing_path, missing_path])


def test_run_pipeline_smoke_writes_manifest_and_site_data(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    settings = _build_settings(tmp_path)
    _install_stage_stubs(monkeypatch)

    manifest_path = run_pipeline(settings=settings)

    assert manifest_path.exists()
    assert (Path(settings.site_output_dir) / "site_data.js").exists()
