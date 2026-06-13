from pathlib import Path
import tempfile

import pytest
from scripts.run_gold import build_gold_outputs, run_gold_stage
from src.bronze.writers import read_jsonl_rows, write_jsonl_rows
from src.config.settings import AppSettings


@pytest.fixture
def tmp_path() -> Path:
    root = Path.cwd() / ".pytest_tmp"
    root.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=root) as temp_dir:
        yield Path(temp_dir)


def test_build_gold_outputs_ranks_assets_and_assigns_flags():
    feature_rows = {
        "market": [
            {
                "symbol": "BTC",
                "close_price": 67000.0,
                "quote_volume": 50000000000.0,
                "relative_strength_24h": -5.6,
                "relative_strength_7d": -11.7,
                "relative_strength_30d": -14.2,
            },
            {
                "symbol": "ETH",
                "close_price": 1900.0,
                "quote_volume": 18000000000.0,
                "relative_strength_24h": -3.1,
                "relative_strength_7d": -7.4,
                "relative_strength_30d": -17.5,
            },
        ],
        "derivatives": [
            {
                "symbol": "BTCUSDT",
                "funding_rate": 0.00008,
                "open_interest": 110567.575,
            }
        ],
        "onchain": [
            {
                "symbol": "ETH",
                "tvl_usd": 200000000000.0,
                "dex_volume_usd": 10000000000.0,
                "capital_efficiency": 0.05,
            }
        ],
    }
    outputs = build_gold_outputs(feature_rows)
    assert outputs["attention"][0]["symbol"] == "BTC"
    assert outputs["attention"][0]["attention_score"] >= outputs["attention"][1]["attention_score"]
    assert "top_driver" in outputs["attention"][0]
    assert "regime_tag" in outputs["attention"][0]
    assert outputs["drivers"][0]["breadth_flag"] in {"narrow", "broad"}


def test_build_gold_outputs_filters_excluded_and_unsupported_assets():
    feature_rows = {
        "market": [
            {
                "symbol": "USDT",
                "close_price": 1.0,
                "quote_volume": 1000000000.0,
                "relative_strength_24h": 0.0,
                "relative_strength_7d": 0.0,
                "relative_strength_30d": 0.0,
            },
            {
                "symbol": "LAB",
                "close_price": 21.0,
                "quote_volume": 1000000000.0,
                "relative_strength_24h": 20.0,
                "relative_strength_7d": 200.0,
                "relative_strength_30d": 1000.0,
            },
            {
                "symbol": "SOL",
                "close_price": 80.0,
                "quote_volume": 3000000000.0,
                "relative_strength_24h": -4.0,
                "relative_strength_7d": -8.0,
                "relative_strength_30d": -10.0,
            },
        ],
        "derivatives": [],
        "onchain": [],
    }
    outputs = build_gold_outputs(feature_rows)
    assert [row["symbol"] for row in outputs["attention"]] == ["SOL"]


def test_run_gold_stage_writes_contract_outputs(tmp_path: Path):
    feature_root = tmp_path / "artifacts" / "features"
    settings = AppSettings(
        features_output_dir=str(feature_root),
        gold_output_dir=str(tmp_path / "artifacts" / "gold"),
    )
    write_jsonl_rows(
        feature_root / "market_features.jsonl",
        [
            {
                "symbol": "BTC",
                "close_price": 67000.0,
                "quote_volume": 50000000000.0,
                "relative_strength_24h": -5.6,
                "relative_strength_7d": -11.7,
                "relative_strength_30d": -14.2,
            },
            {
                "symbol": "ETH",
                "close_price": 1900.0,
                "quote_volume": 18000000000.0,
                "relative_strength_24h": -3.1,
                "relative_strength_7d": -7.4,
                "relative_strength_30d": -17.5,
            },
        ],
    )
    write_jsonl_rows(
        feature_root / "derivatives_features.jsonl",
        [{"symbol": "BTCUSDT", "funding_rate": 0.00008, "open_interest": 110567.575}],
    )
    write_jsonl_rows(
        feature_root / "onchain_features.jsonl",
        [
            {
                "symbol": "ETH",
                "tvl_usd": 200000000000.0,
                "dex_volume_usd": 10000000000.0,
                "capital_efficiency": 0.05,
            }
        ],
    )

    paths = run_gold_stage(settings)

    assert paths == {
        "attention": Path(settings.gold_output_dir) / "attention.jsonl",
        "drivers": Path(settings.gold_output_dir) / "drivers.jsonl",
        "narratives": Path(settings.gold_output_dir) / "narratives.jsonl",
    }
    assert all(path.exists() for path in paths.values())
    assert read_jsonl_rows(paths["attention"])[0]["symbol"] == "BTC"
    assert "breadth_flag" in read_jsonl_rows(paths["drivers"])[0]
    assert read_jsonl_rows(paths["narratives"])[0]["narrative"]
