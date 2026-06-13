from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.bronze.writers import read_jsonl_rows, write_jsonl_rows
from src.config.settings import AppSettings
from src.domain.asset_universe import is_supported_asset, should_exclude_asset
from src.gold.attention_engine import build_attention_row, compute_attention_score
from src.gold.explanations import build_driver_flags
from src.domain.narratives import NARRATIVE_UNIVERSE

NARRATIVE_OVERRIDES = {
    "ADA": "layer1",
    "AVAX": "layer1",
    "APT": "layer1",
    "BNB": "layer1",
    "HBAR": "layer1",
    "INJ": "layer1",
    "SEI": "layer1",
    "SUI": "layer1",
    "TON": "layer1",
    "XRP": "layer1",
    "LINK": "defi",
    "MKR": "defi",
    "PENDLE": "defi",
    "UNI": "defi",
    "DOGE": "meme_social_beta",
    "PEPE": "meme_social_beta",
    "WIF": "meme_social_beta",
    "ONDO": "rwa",
    "RENDER": "depin_infra",
    "AKT": "depin_infra",
    "TAO": "ai_data",
    "FET": "ai_data",
    "ENA": "restaking_modular",
    "EIGEN": "restaking_modular",
    "ATOM": "cosmos_interop",
    "TRX": "cosmos_interop",
    "JUP": "solana_ecosystem",
}


def assign_narrative(symbol: str) -> str:
    if symbol in NARRATIVE_OVERRIDES:
        return NARRATIVE_OVERRIDES[symbol]
    for key, definition in NARRATIVE_UNIVERSE.items():
        if symbol in definition.seed_assets:
            return key
    return "unassigned"


def aggregate_narratives(attention_rows: list[dict]) -> list[dict]:
    grouped: dict[str, dict] = {}
    for row in attention_rows:
        narrative = row["narrative"]
        current = grouped.get(
            narrative,
            {
                "narrative": narrative,
                "asset_count": 0,
                "total_attention_score": 0.0,
                "total_confirmation_score": 0.0,
            },
        )
        current["asset_count"] += 1
        current["total_attention_score"] += row["attention_score"]
        current["total_confirmation_score"] += row["confirmation_score"]
        grouped[narrative] = current

    rows = []
    for narrative, current in grouped.items():
        asset_count = current["asset_count"]
        rows.append(
            {
                "narrative": narrative,
                "asset_count": asset_count,
                "avg_attention_score": round(current["total_attention_score"] / asset_count, 6),
                "avg_confirmation_score": round(current["total_confirmation_score"] / asset_count, 4),
            }
        )
    rows.sort(key=lambda row: row["avg_attention_score"], reverse=True)
    return rows


def build_gold_outputs(feature_rows: dict[str, list[dict]]) -> dict[str, list[dict]]:
    derivatives_index = {
        row["symbol"].replace("USDT", ""): row for row in feature_rows["derivatives"]
    }
    onchain_index = {row["symbol"]: row for row in feature_rows["onchain"]}

    attention_rows: list[dict] = []
    driver_rows: list[dict] = []

    for market_row in feature_rows["market"]:
        symbol = market_row["symbol"]
        if should_exclude_asset(symbol) or not is_supported_asset(symbol):
            continue
        derivative_row = derivatives_index.get(symbol, {})
        onchain_row = onchain_index.get(symbol, {})

        attention_score = compute_attention_score(
            quote_volume=market_row.get("quote_volume") or 0.0,
            relative_strength_24h=market_row.get("relative_strength_24h") or 0.0,
            relative_strength_7d=market_row.get("relative_strength_7d") or 0.0,
            capital_efficiency=onchain_row.get("capital_efficiency") or 0.0,
            open_interest=derivative_row.get("open_interest") or 0.0,
        )
        confirmation_score = round(
            sum(
                [
                    1 if market_row.get("relative_strength_24h") is not None else 0,
                    1 if derivative_row.get("funding_rate") is not None else 0,
                    1 if onchain_row.get("capital_efficiency") not in (None, 0.0) else 0,
                ]
            )
            / 3,
            4,
        )
        top_driver = "volume_strength"
        if (onchain_row.get("capital_efficiency") or 0.0) > 0:
            top_driver = "onchain_confirmation"
        elif derivative_row.get("open_interest") is not None:
            top_driver = "derivatives_positioning"

        attention_rows.append(
            {
                **build_attention_row(
                    symbol=symbol,
                    narrative=assign_narrative(symbol),
                    attention_score=attention_score,
                    confirmation_score=confirmation_score,
                ),
                "top_driver": top_driver,
            }
        )

        flags = build_driver_flags(
            funding_zscore=(derivative_row.get("funding_rate") or 0.0) * 10000,
            breadth_ratio=1.0 if confirmation_score >= 0.66 else 0.33,
            relative_strength_24h=market_row.get("relative_strength_24h") or 0.0,
            relative_strength_7d=market_row.get("relative_strength_7d") or 0.0,
        )
        attention_rows[-1]["regime_tag"] = flags["regime_tag"]
        driver_rows.append({"symbol": symbol, **flags})

    best_attention_by_symbol: dict[str, dict] = {}
    for row in attention_rows:
        current = best_attention_by_symbol.get(row["symbol"])
        if current is None or row["attention_score"] > current["attention_score"]:
            best_attention_by_symbol[row["symbol"]] = row

    attention_rows = sorted(
        best_attention_by_symbol.values(),
        key=lambda row: row["attention_score"],
        reverse=True,
    )

    driver_by_symbol = {}
    for row in driver_rows:
        driver_by_symbol[row["symbol"]] = row

    narrative_rows = aggregate_narratives(attention_rows)

    return {
        "attention": attention_rows,
        "drivers": list(driver_by_symbol.values()),
        "narratives": narrative_rows,
    }


def run_gold_stage(settings: AppSettings) -> dict[str, Path]:
    feature_root = PROJECT_ROOT / settings.features_output_dir
    feature_rows = {
        "market": read_jsonl_rows(feature_root / "market_features.jsonl"),
        "derivatives": read_jsonl_rows(feature_root / "derivatives_features.jsonl"),
        "onchain": read_jsonl_rows(feature_root / "onchain_features.jsonl"),
    }
    outputs = build_gold_outputs(feature_rows)
    gold_root = PROJECT_ROOT / settings.gold_output_dir
    paths = {
        "attention": gold_root / "attention.jsonl",
        "drivers": gold_root / "drivers.jsonl",
        "narratives": gold_root / "narratives.jsonl",
    }
    write_jsonl_rows(paths["attention"], outputs["attention"])
    write_jsonl_rows(paths["drivers"], outputs["drivers"])
    write_jsonl_rows(paths["narratives"], outputs["narratives"])
    return paths


def main() -> None:
    settings = AppSettings.from_env()
    run_gold_stage(settings)
    print(f"gold outputs saved to {Path(settings.gold_output_dir)}")


if __name__ == "__main__":
    main()
