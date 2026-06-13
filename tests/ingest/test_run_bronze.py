from pathlib import Path
import tempfile

import pytest
import requests

from scripts.run_bronze import (
    DERIVATIVES_SYMBOLS,
    MARKET_SNAPSHOT_PAGE_SIZE,
    collect_public_bronze_rows,
    run_bronze_stage,
)
from src.config.settings import AppSettings


@pytest.fixture
def tmp_path() -> Path:
    root = Path.cwd() / ".pytest_tmp"
    root.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=root) as temp_dir:
        yield Path(temp_dir)


class StubCoinGeckoClient:
    def __init__(self) -> None:
        self.calls = []

    def fetch_markets(self, vs_currency: str, page: int, per_page: int) -> list[dict]:
        self.calls.append({"vs_currency": vs_currency, "page": page, "per_page": per_page})
        return [{"id": "bitcoin", "symbol": "btc"}]


class StubDefiLlamaClient:
    def fetch_protocols(self) -> list[dict]:
        return [{"name": "Aave", "symbol": "aave"}]


class StubBinanceClient:
    def __init__(self) -> None:
        self.open_interest_calls = []
        self.funding_rate_calls = []

    def fetch_open_interest(self, symbol: str) -> dict:
        self.open_interest_calls.append(symbol)
        return {"symbol": symbol, "openInterest": "123.45"}

    def fetch_funding_rate(self, symbol: str, limit: int = 1) -> list[dict]:
        self.funding_rate_calls.append({"symbol": symbol, "limit": limit})
        return [{"symbol": symbol, "fundingRate": "0.01"}]


class FailingBinanceClient:
    def fetch_open_interest(self, symbol: str) -> dict:
        raise requests.HTTPError("451 Client Error")

    def fetch_funding_rate(self, symbol: str, limit: int = 1) -> list[dict]:
        raise requests.HTTPError("451 Client Error")


class PartialBinanceClient:
    def fetch_open_interest(self, symbol: str) -> dict:
        return {"symbol": symbol, "openInterest": "123.45"}

    def fetch_funding_rate(self, symbol: str, limit: int = 1) -> list[dict]:
        raise requests.HTTPError("451 Client Error")


def test_collect_public_bronze_rows_expands_market_and_derivatives_coverage():
    coingecko = StubCoinGeckoClient()
    binance = StubBinanceClient()
    defillama = StubDefiLlamaClient()

    rows = collect_public_bronze_rows(coingecko=coingecko, binance=binance, defillama=defillama)

    assert coingecko.calls == [{"vs_currency": "usd", "page": 1, "per_page": MARKET_SNAPSHOT_PAGE_SIZE}]
    assert len(binance.open_interest_calls) == len(DERIVATIVES_SYMBOLS)
    assert len(binance.funding_rate_calls) == len(DERIVATIVES_SYMBOLS)
    assert rows[0]["source_name"] == "coingecko"
    assert rows[-1]["source_name"] == "defillama"
    assert any(row["endpoint_name"] == "funding_rate" for row in rows)


def test_collect_public_bronze_rows_continues_when_binance_is_unavailable():
    rows = collect_public_bronze_rows(
        coingecko=StubCoinGeckoClient(),
        binance=FailingBinanceClient(),
        defillama=StubDefiLlamaClient(),
    )

    assert [row["source_name"] for row in rows] == ["coingecko", "defillama"]


def test_collect_public_bronze_rows_keeps_partial_binance_success():
    rows = collect_public_bronze_rows(
        coingecko=StubCoinGeckoClient(),
        binance=PartialBinanceClient(),
        defillama=StubDefiLlamaClient(),
    )

    open_interest_rows = [row for row in rows if row["endpoint_name"] == "open_interest"]
    funding_rows = [row for row in rows if row["endpoint_name"] == "funding_rate"]
    assert len(open_interest_rows) == len(DERIVATIVES_SYMBOLS)
    assert funding_rows == []


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
