from pathlib import Path
import tempfile

import pytest
from scripts.export_public_artifacts import resolve_export_roots, run_public_export_stage
from src.bronze.writers import write_jsonl_rows
from src.config.settings import AppSettings
from src.publish.export_gold import build_public_attention_record


@pytest.fixture
def tmp_path() -> Path:
    root = Path.cwd() / ".pytest_tmp"
    root.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=root) as temp_dir:
        yield Path(temp_dir)


def test_public_attention_record_hides_internal_noise():
    row = build_public_attention_record(
        symbol="TAO",
        narrative="ai_data",
        attention_score=0.91,
        top_driver="onchain_confirmation",
        regime_tag="bullish_attention",
        confirmation_score=0.72,
    )
    assert row == {
        "symbol": "TAO",
        "narrative": "ai_data",
        "attention_score": 0.91,
        "top_driver": "onchain_confirmation",
        "regime_tag": "bullish_attention",
        "confirmation_score": 0.72,
    }


def test_resolve_export_roots_uses_app_settings_directories(tmp_path: Path):
    settings = AppSettings(
        gold_output_dir="custom/gold",
        features_output_dir="custom/features",
        public_export_dir="custom/public",
        site_output_dir="custom/site",
    )

    roots = resolve_export_roots(settings, project_root=tmp_path)

    assert roots["gold"] == tmp_path / "custom" / "gold"
    assert roots["features"] == tmp_path / "custom" / "features"
    assert roots["public"] == tmp_path / "custom" / "public"
    assert roots["site"] == tmp_path / "custom" / "site"
    assert roots["public"] != tmp_path / "outputs"
    assert roots["site"] != tmp_path / "site"


def test_run_public_export_stage_returns_expected_output_paths(tmp_path: Path):
    settings = AppSettings(
        gold_output_dir=str(tmp_path / "artifacts" / "gold"),
        features_output_dir=str(tmp_path / "artifacts" / "features"),
        public_export_dir=str(tmp_path / "artifacts" / "public"),
        site_output_dir=str(tmp_path / "site"),
    )
    gold_root = Path(settings.gold_output_dir)
    features_root = Path(settings.features_output_dir)
    write_jsonl_rows(
        gold_root / "attention.jsonl",
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
        gold_root / "drivers.jsonl",
        [{"symbol": "BTC", "breadth_flag": "broad", "crowding_flag": "balanced"}],
    )
    write_jsonl_rows(
        gold_root / "narratives.jsonl",
        [{"narrative": "store_of_value", "asset_count": 1, "avg_attention_score": 0.95, "avg_confirmation_score": 1.0}],
    )
    write_jsonl_rows(
        features_root / "market_features.jsonl",
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
        features_root / "derivatives_features.jsonl",
        [{"symbol": "BTCUSDT", "funding_rate": 0.0001, "open_interest": 12345.0}],
    )

    outputs = run_public_export_stage(settings)

    assert outputs == {
        "public_jsonl": Path(settings.public_export_dir) / "crypto_attention_public.jsonl",
        "summary_markdown": Path(settings.public_export_dir) / "crypto-market-intelligence-summary.md",
        "site_snapshot": Path(settings.site_output_dir) / "site_data.js",
    }
    assert all(path.exists() for path in outputs.values())
