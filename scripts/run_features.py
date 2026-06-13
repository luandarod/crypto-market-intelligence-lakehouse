from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.bronze.writers import read_jsonl_rows, write_jsonl_rows
from src.config.settings import AppSettings
from src.features.market_features import compute_relative_strength


def build_feature_outputs(silver_rows: dict[str, list[dict]]) -> dict[str, list[dict]]:
    market_features = []
    for row in silver_rows["market"]:
        market_features.append(
            {
                "symbol": row["symbol"],
                "close_price": row["close_price"],
                "quote_volume": row["quote_volume"],
                "relative_strength_24h": row.get("price_change_pct_24h"),
                "relative_strength_7d": compute_relative_strength(
                    asset_return=row.get("price_change_pct_7d") or 0.0,
                    benchmark_return=0.0,
                ),
                "relative_strength_30d": row.get("price_change_pct_30d"),
            }
        )

    derivatives_features = []
    for row in silver_rows["derivatives"]:
        derivatives_features.append(
            {
                "symbol": row["symbol"],
                "funding_rate": float(row["funding_rate"]) if row.get("funding_rate") is not None else None,
                "open_interest": float(row["open_interest"]) if row.get("open_interest") is not None else None,
            }
        )

    onchain_features = []
    for row in silver_rows["onchain"]:
        tvl = float(row["tvl_usd"]) if row.get("tvl_usd") is not None else 0.0
        dex_volume = float(row["dex_volume_usd"]) if row.get("dex_volume_usd") is not None else 0.0
        capital_efficiency = 0.0 if tvl == 0 else dex_volume / tvl
        onchain_features.append(
            {
                "symbol": row["symbol"],
                "tvl_usd": tvl,
                "dex_volume_usd": dex_volume,
                "capital_efficiency": capital_efficiency,
            }
        )

    return {
        "market": market_features,
        "derivatives": derivatives_features,
        "onchain": onchain_features,
    }


def run_features_stage(settings: AppSettings) -> dict[str, Path]:
    silver_root = PROJECT_ROOT / settings.silver_output_dir
    silver_rows = {
        "market": read_jsonl_rows(silver_root / "market.jsonl"),
        "derivatives": read_jsonl_rows(silver_root / "derivatives.jsonl"),
        "onchain": read_jsonl_rows(silver_root / "onchain.jsonl"),
    }
    outputs = build_feature_outputs(silver_rows)
    feature_root = PROJECT_ROOT / settings.features_output_dir
    paths = {
        "market": feature_root / "market_features.jsonl",
        "derivatives": feature_root / "derivatives_features.jsonl",
        "onchain": feature_root / "onchain_features.jsonl",
    }
    write_jsonl_rows(paths["market"], outputs["market"])
    write_jsonl_rows(paths["derivatives"], outputs["derivatives"])
    write_jsonl_rows(paths["onchain"], outputs["onchain"])
    return paths


def main() -> None:
    settings = AppSettings.from_env()
    run_features_stage(settings)
    print(f"feature outputs saved to {Path(settings.features_output_dir)}")


if __name__ == "__main__":
    main()
