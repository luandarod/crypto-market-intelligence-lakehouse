from pathlib import Path
import tempfile

import pytest
from scripts.run_features import build_feature_outputs, run_features_stage
from src.bronze.writers import read_jsonl_rows, write_jsonl_rows
from src.config.settings import AppSettings


@pytest.fixture
def tmp_path() -> Path:
    root = Path.cwd() / ".pytest_tmp"
    root.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=root) as temp_dir:
        yield Path(temp_dir)


def test_build_feature_outputs_creates_market_derivatives_and_onchain_rows():
    silver_rows = {
        "market": [
            {
                "symbol": "ETH",
                "close_price": 3800.0,
                "quote_volume": 1000000.0,
                "price_change_pct_24h": -3.1,
                "price_change_pct_7d": -7.4,
                "price_change_pct_30d": -17.5,
            }
        ],
        "derivatives": [
            {
                "symbol": "BTCUSDT",
                "funding_rate": "0.01",
                "open_interest": "123.45",
            }
        ],
        "onchain": [
            {
                "symbol": "UNI",
                "tvl_usd": 1000.0,
                "dex_volume_usd": 500.0,
            }
        ],
    }
    outputs = build_feature_outputs(silver_rows)
    assert outputs["market"][0]["symbol"] == "ETH"
    assert outputs["market"][0]["relative_strength_7d"] == -7.4
    assert outputs["derivatives"][0]["open_interest"] == 123.45
    assert outputs["onchain"][0]["capital_efficiency"] == 0.5


def test_run_features_stage_writes_contract_outputs(tmp_path: Path):
    silver_root = tmp_path / "artifacts" / "silver"
    settings = AppSettings(
        silver_output_dir=str(silver_root),
        features_output_dir=str(tmp_path / "artifacts" / "features"),
    )
    write_jsonl_rows(
        silver_root / "market.jsonl",
        [
            {
                "symbol": "ETH",
                "close_price": 3800.0,
                "quote_volume": 1000000.0,
                "price_change_pct_24h": -3.1,
                "price_change_pct_7d": -7.4,
                "price_change_pct_30d": -17.5,
            }
        ],
    )
    write_jsonl_rows(
        silver_root / "derivatives.jsonl",
        [{"symbol": "BTCUSDT", "funding_rate": "0.01", "open_interest": "123.45"}],
    )
    write_jsonl_rows(
        silver_root / "onchain.jsonl",
        [{"symbol": "UNI", "tvl_usd": 1000.0, "dex_volume_usd": 500.0}],
    )

    paths = run_features_stage(settings)

    assert paths == {
        "market": Path(settings.features_output_dir) / "market_features.jsonl",
        "derivatives": Path(settings.features_output_dir) / "derivatives_features.jsonl",
        "onchain": Path(settings.features_output_dir) / "onchain_features.jsonl",
    }
    assert all(path.exists() for path in paths.values())
    assert read_jsonl_rows(paths["market"])[0]["relative_strength_7d"] == -7.4
    assert read_jsonl_rows(paths["derivatives"])[0]["open_interest"] == 123.45
    assert read_jsonl_rows(paths["onchain"])[0]["capital_efficiency"] == 0.5
