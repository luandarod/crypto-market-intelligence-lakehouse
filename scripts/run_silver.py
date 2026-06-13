from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.bronze.writers import read_jsonl_rows, write_jsonl_rows
from src.config.settings import AppSettings
from src.silver.derivatives_tables import normalize_derivatives_row
from src.silver.market_tables import normalize_market_row
from src.silver.onchain_tables import normalize_onchain_row


def build_silver_outputs(bronze_rows: list[dict]) -> dict[str, list[dict]]:
    outputs = {"market": [], "derivatives": [], "onchain": []}
    derivatives_by_symbol: dict[str, dict] = {}
    for row in bronze_rows:
        if row["source_name"] == "coingecko":
            outputs["market"].extend(
                normalize_market_row(item) for item in row["payload"].get("items", [])
            )
        elif row["source_name"] == "binance":
            if row.get("endpoint_name") == "open_interest":
                normalized = normalize_derivatives_row(row["payload"])
                derivatives_by_symbol[normalized["symbol"]] = normalized
            elif row.get("endpoint_name") == "funding_rate":
                for item in row["payload"]:
                    symbol = item["symbol"].upper()
                    current = derivatives_by_symbol.get(
                        symbol,
                        {"symbol": symbol, "funding_rate": None, "open_interest": None},
                    )
                    current["funding_rate"] = item.get("fundingRate")
                    derivatives_by_symbol[symbol] = current
        elif row["source_name"] == "defillama":
            outputs["onchain"].extend(
                normalize_onchain_row(item) for item in row["payload"].get("items", [])
            )
    outputs["derivatives"] = list(derivatives_by_symbol.values())
    return outputs


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


def main() -> None:
    settings = AppSettings.from_env()
    paths = run_silver_stage(settings)
    print(f"silver outputs saved to {Path(settings.silver_output_dir)}")


if __name__ == "__main__":
    main()
