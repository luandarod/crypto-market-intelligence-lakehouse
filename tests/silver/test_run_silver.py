from pathlib import Path
import tempfile

import pytest
from scripts.run_silver import build_silver_outputs, run_silver_stage
from src.bronze.writers import read_jsonl_rows, write_jsonl_rows
from src.config.settings import AppSettings


@pytest.fixture
def tmp_path() -> Path:
    root = Path.cwd() / ".pytest_tmp"
    root.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=root) as temp_dir:
        yield Path(temp_dir)


def test_build_silver_outputs_splits_rows_by_source():
    bronze_rows = [
        {
            "source_name": "coingecko",
            "payload": {"items": [{"symbol": "eth", "current_price": 3800.0, "total_volume": 1000.0}]},
        },
        {
            "source_name": "binance",
            "endpoint_name": "open_interest",
            "payload": {"symbol": "btcusdt", "funding_rate": 0.01, "open_interest": 100.0},
        },
        {
            "source_name": "binance",
            "endpoint_name": "funding_rate",
            "payload": [{"symbol": "BTCUSDT", "fundingRate": "0.02"}],
        },
        {
            "source_name": "defillama",
            "payload": {"items": [{"symbol": "uni", "tvl": 1000.0, "dex_volume_usd": 500.0}]},
        },
    ]
    outputs = build_silver_outputs(bronze_rows)
    assert outputs["market"][0]["symbol"] == "ETH"
    assert outputs["derivatives"][0]["symbol"] == "BTCUSDT"
    assert outputs["derivatives"][0]["funding_rate"] == "0.02"
    assert outputs["onchain"][0]["symbol"] == "UNI"


def test_run_silver_stage_writes_contract_outputs(tmp_path: Path):
    bronze_rows = [
        {
            "source_name": "coingecko",
            "payload": {"items": [{"symbol": "eth", "current_price": 3800.0, "total_volume": 1000.0}]},
        },
        {
            "source_name": "binance",
            "endpoint_name": "open_interest",
            "payload": {"symbol": "btcusdt", "funding_rate": 0.01, "openInterest": "100.0"},
        },
        {
            "source_name": "binance",
            "endpoint_name": "funding_rate",
            "payload": [{"symbol": "BTCUSDT", "fundingRate": "0.02"}],
        },
        {
            "source_name": "defillama",
            "payload": {"items": [{"symbol": "uni", "tvl": 1000.0, "dex_volume_usd": 500.0}]},
        },
    ]
    settings = AppSettings(
        bronze_output_dir=str(tmp_path / "artifacts" / "bronze"),
        silver_output_dir=str(tmp_path / "artifacts" / "silver"),
    )
    bronze_path = Path(settings.bronze_output_dir) / "public_sources.jsonl"
    write_jsonl_rows(bronze_path, bronze_rows)

    paths = run_silver_stage(settings)

    assert paths == {
        "market": Path(settings.silver_output_dir) / "market.jsonl",
        "derivatives": Path(settings.silver_output_dir) / "derivatives.jsonl",
        "onchain": Path(settings.silver_output_dir) / "onchain.jsonl",
    }
    assert all(path.exists() for path in paths.values())
    assert read_jsonl_rows(paths["market"])[0]["symbol"] == "ETH"
    assert read_jsonl_rows(paths["derivatives"])[0]["funding_rate"] == "0.02"
    assert read_jsonl_rows(paths["onchain"])[0]["symbol"] == "UNI"
