from pathlib import Path
from datetime import datetime, timezone
import sys

import requests


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.bronze.writers import build_bronze_row, write_jsonl_rows
from src.config.settings import AppSettings
from src.domain.asset_universe import get_supported_derivatives_symbols
from src.ingest.binance import BinanceClient
from src.ingest.coingecko import CoinGeckoClient
from src.ingest.defillama import DefiLlamaClient


MARKET_SNAPSHOT_PAGE_SIZE = 150
DERIVATIVES_SYMBOLS = get_supported_derivatives_symbols()


def append_source_row(rows: list[dict], *, source_name: str, endpoint_name: str, payload, extracted_at: str) -> None:
    rows.append(
        build_bronze_row(
            source_name=source_name,
            endpoint_name=endpoint_name,
            payload=payload,
            extracted_at=extracted_at,
        )
    )


def collect_public_bronze_rows(
    coingecko: CoinGeckoClient,
    binance: BinanceClient,
    defillama: DefiLlamaClient,
) -> list[dict]:
    extracted_at = datetime.now(timezone.utc).isoformat()
    rows: list[dict] = []

    append_source_row(
        rows,
        source_name="coingecko",
        endpoint_name="coins_markets",
        payload={"items": coingecko.fetch_markets(vs_currency="usd", page=1, per_page=MARKET_SNAPSHOT_PAGE_SIZE)},
        extracted_at=extracted_at,
    )

    for symbol in DERIVATIVES_SYMBOLS:
        try:
            append_source_row(
                rows,
                source_name="binance",
                endpoint_name="open_interest",
                payload=binance.fetch_open_interest(symbol=symbol),
                extracted_at=extracted_at,
            )
        except requests.RequestException as exc:
            print(f"warning: skipping binance open_interest snapshot for {symbol}: {exc}")

        try:
            append_source_row(
                rows,
                source_name="binance",
                endpoint_name="funding_rate",
                payload=binance.fetch_funding_rate(symbol=symbol, limit=1),
                extracted_at=extracted_at,
            )
        except requests.RequestException as exc:
            print(f"warning: skipping binance funding_rate snapshot for {symbol}: {exc}")

    append_source_row(
        rows,
        source_name="defillama",
        endpoint_name="protocols",
        payload={"items": defillama.fetch_protocols()},
        extracted_at=extracted_at,
    )

    return rows


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


def main() -> None:
    settings = AppSettings.from_env()
    output_path = run_bronze_stage(settings=settings)
    print(f"bronze snapshot saved to {output_path}")


if __name__ == "__main__":
    main()
