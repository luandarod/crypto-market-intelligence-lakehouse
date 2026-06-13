import json
from datetime import datetime, timezone
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.bronze.writers import read_jsonl_rows, write_jsonl_rows
from src.config.settings import AppSettings
from src.publish.export_gold import build_public_attention_record


def build_latest_symbol_map(rows: list[dict], *, symbol_key: str = "symbol") -> dict[str, dict]:
    latest_rows: dict[str, dict] = {}
    for row in rows:
        symbol = row.get(symbol_key)
        if symbol:
            latest_rows[symbol] = row
    return latest_rows


def normalize_derivatives_symbol(value: str) -> str:
    for suffix in ("USDT", "USDC", "BUSD", "USD"):
        if value.endswith(suffix):
            return value[: -len(suffix)]
    return value


def build_asset_explorer_rows(
    attention_rows: list[dict],
    driver_rows: list[dict] | None = None,
    market_feature_rows: list[dict] | None = None,
    derivatives_feature_rows: list[dict] | None = None,
) -> list[dict]:
    driver_map = build_latest_symbol_map(driver_rows or [])
    market_map = build_latest_symbol_map(market_feature_rows or [])
    derivatives_map = {
        normalize_derivatives_symbol(symbol): row
        for symbol, row in build_latest_symbol_map(derivatives_feature_rows or []).items()
    }

    explorer_rows: list[dict] = []
    for row in attention_rows:
        symbol = row["symbol"]
        driver = driver_map.get(symbol, {})
        market = market_map.get(symbol, {})
        derivatives = derivatives_map.get(symbol, {})
        explorer_rows.append(
            {
                **row,
                "close_price": market.get("close_price"),
                "quote_volume": market.get("quote_volume"),
                "relative_strength_24h": market.get("relative_strength_24h"),
                "relative_strength_7d": market.get("relative_strength_7d"),
                "relative_strength_30d": market.get("relative_strength_30d"),
                "breadth_flag": driver.get("breadth_flag"),
                "crowding_flag": driver.get("crowding_flag"),
                "funding_rate": derivatives.get("funding_rate"),
                "open_interest": derivatives.get("open_interest"),
            }
        )
    return explorer_rows


def build_narrative_explorer_rows(
    asset_explorer_rows: list[dict],
    narrative_rows: list[dict],
) -> list[dict]:
    assets_by_narrative: dict[str, list[dict]] = {}
    for row in asset_explorer_rows:
        assets_by_narrative.setdefault(row["narrative"], []).append(row)

    narrative_row_map = {row["narrative"]: row for row in narrative_rows}
    explorer_rows: list[dict] = []
    for narrative in narrative_row_map.keys() | assets_by_narrative.keys():
        assets = sorted(
            assets_by_narrative.get(narrative, []),
            key=lambda row: row["attention_score"],
            reverse=True,
        )
        if not assets:
            continue
        narrative_row = narrative_row_map.get(
            narrative,
            {
                "narrative": narrative,
                "asset_count": len(assets),
                "avg_attention_score": sum(asset["attention_score"] for asset in assets) / len(assets),
                "avg_confirmation_score": sum(asset["confirmation_score"] for asset in assets) / len(assets),
            },
        )
        explorer_rows.append(
            {
                **narrative_row,
                "leader_symbol": assets[0]["symbol"],
                "asset_symbols": [asset["symbol"] for asset in assets],
                "regime_mix": [asset["regime_tag"] for asset in assets],
            }
        )
    return sorted(explorer_rows, key=lambda row: row["avg_attention_score"], reverse=True)


def build_portfolio_summary_rows(attention_rows: list[dict], narrative_rows: list[dict]) -> dict[str, str]:
    asset_lines = [
        "| Symbol | Narrative | Attention | Confirmation | Driver | Regime |",
        "|---|---|---:|---:|---|---|",
    ]
    for row in attention_rows:
        asset_lines.append(
            f"| {row['symbol']} | {row['narrative']} | {row['attention_score']:.3f} | {row['confirmation_score']:.4f} | {row['top_driver']} | {row['regime_tag']} |"
        )

    narrative_lines = [
        "| Narrative | Assets | Avg Attention | Avg Confirmation |",
        "|---|---:|---:|---:|",
    ]
    for row in narrative_rows:
        narrative_lines.append(
            f"| {row['narrative']} | {row['asset_count']} | {row['avg_attention_score']:.3f} | {row['avg_confirmation_score']:.4f} |"
        )

    return {
        "asset_markdown": "\n".join(asset_lines),
        "narrative_markdown": "\n".join(narrative_lines),
    }


def build_portfolio_report(attention_rows: list[dict], narrative_rows: list[dict]) -> str:
    summary = build_portfolio_summary_rows(
        attention_rows=attention_rows[:8],
        narrative_rows=narrative_rows[:8],
    )
    return "\n".join(
        [
            "# Crypto Market Intelligence Report",
            "",
            "## What This Project Shows",
            "",
            "- A public crypto market intelligence pipeline built from bronze to gold.",
            "- Integration of spot market, derivatives, and on-chain style signals.",
            "- A portfolio-facing output that ranks assets and narratives by attention, not price prediction alone.",
            "",
            "## Current Snapshot",
            "",
            summary["asset_markdown"],
            "",
            "## Narrative View",
            "",
            summary["narrative_markdown"],
            "",
            "## Architecture",
            "",
            "- Bronze: raw public API snapshots from CoinGecko, Binance, and DefiLlama.",
            "- Silver: normalized market, derivatives, and on-chain records.",
            "- Features: relative strength, volume context, open interest, funding, and capital efficiency.",
            "- Gold: asset attention, driver flags, and narrative aggregation.",
            "",
            "## Why This Is Strong For Portfolio Positioning",
            "",
            "- It demonstrates modern data-product structure instead of notebook-only analysis.",
            "- It shows how to combine analytics engineering with market reasoning.",
            "- It creates an output that is interpretable enough for a hiring manager and concrete enough for a technical reviewer.",
            "",
            "Generated from the local bronze -> silver -> features -> gold pipeline.",
        ]
    )


def build_site_payload(
    attention_rows: list[dict],
    narrative_rows: list[dict],
    driver_rows: list[dict] | None = None,
    market_feature_rows: list[dict] | None = None,
    derivatives_feature_rows: list[dict] | None = None,
) -> dict:
    top_assets = attention_rows[:8]
    top_narratives = narrative_rows[:6]
    asset_explorer_rows = build_asset_explorer_rows(
        attention_rows=attention_rows[:12],
        driver_rows=driver_rows,
        market_feature_rows=market_feature_rows,
        derivatives_feature_rows=derivatives_feature_rows,
    )
    narrative_explorer_rows = build_narrative_explorer_rows(asset_explorer_rows, narrative_rows)
    asset_count = len(attention_rows)
    narrative_count = len({row["narrative"] for row in attention_rows})
    bullish_count = sum(1 for row in attention_rows if row["regime_tag"] == "bullish_attention")
    bearish_count = sum(1 for row in attention_rows if row["regime_tag"] == "bearish_attention")
    mixed_count = sum(1 for row in attention_rows if row["regime_tag"] == "mixed_attention")

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "headline": {
            "title": "Crypto Market Intelligence Lakehouse",
            "subtitle": "A Databricks-oriented market intelligence platform for spotting which crypto assets and narratives deserve attention, and why.",
        },
        "overview": {
            "asset_count": asset_count,
            "narrative_count": narrative_count,
            "bullish_count": bullish_count,
            "bearish_count": bearish_count,
            "mixed_count": mixed_count,
        },
        "top_assets": top_assets,
        "top_narratives": top_narratives,
        "asset_explorer_rows": asset_explorer_rows,
        "narrative_explorer_rows": narrative_explorer_rows,
        "refresh_policy": {
            "trigger": "github_actions",
            "cadence_label": "Every 12 hours",
            "cadence_detail": "Automated snapshot refresh runs on a 12-hour cadence, with manual dispatch available from GitHub Actions.",
        },
        "architecture": [
            "Bronze: raw public API snapshots from CoinGecko, Binance, and DefiLlama.",
            "Silver: normalized market, derivatives, and on-chain records.",
            "Features: relative strength, volume context, open interest, funding, and capital efficiency.",
            "Gold: asset attention, driver flags, and narrative aggregation.",
        ],
        "databricks_blueprint": [
            {
                "title": "Asset Bundles scaffold",
                "artifact": "databricks.yml",
                "description": "The repo already carries a Databricks bundle entrypoint so deployment can evolve from local scripts into a reproducible workspace asset model.",
            },
            {
                "title": "Job definition path",
                "artifact": "resources/jobs/pipeline_job.yml",
                "description": "The project has a dedicated job resource placeholder for orchestrating the bronze to gold pipeline as a scheduled Databricks workload.",
            },
            {
                "title": "Lakehouse pipeline resource",
                "artifact": "resources/pipelines/lakehouse_pipeline.yml",
                "description": "Pipeline resources are separated from app presentation so Delta-backed medallion layers can later replace the current local JSONL artifacts cleanly.",
            },
        ],
        "signals": [
            {"name": "Relative Strength", "description": "Short-horizon price context for spotting assets already moving with intent."},
            {"name": "Open Interest", "description": "Derivatives positioning used as a proxy for participation and leverage."},
            {"name": "Funding Rate", "description": "Crowding-style signal that helps separate healthy momentum from stretched positioning."},
            {"name": "Capital Efficiency", "description": "DEX activity relative to TVL, used as an on-chain confirmation signal."},
        ],
        "next_steps": [
            "Expand the live asset universe beyond the current first curated set and widen narrative coverage.",
            "Replace local development artifacts with Delta-backed Databricks tables and scheduled jobs.",
            "Add a deeper interactive product layer with richer explorer views, filters, and explanatory panels.",
            "Introduce stronger market concepts such as open-interest momentum, narrative breadth, and cross-asset rotation.",
        ],
    }


def build_site_data_script(payload: dict) -> str:
    return "window.CMIL_SITE_DATA = " + json.dumps(payload, indent=2) + ";\n"


def resolve_export_roots(settings: AppSettings, *, project_root: Path = PROJECT_ROOT) -> dict[str, Path]:
    def resolve_root(value: str) -> Path:
        root = Path(value)
        if root.is_absolute():
            return root
        return project_root / root

    return {
        "gold": resolve_root(settings.gold_output_dir),
        "features": resolve_root(settings.features_output_dir),
        "public": resolve_root(settings.public_export_dir),
        "site": resolve_root(settings.site_output_dir),
    }


def run_public_export_stage(settings: AppSettings) -> dict[str, Path]:
    roots = resolve_export_roots(settings, project_root=PROJECT_ROOT)
    gold_root = roots["gold"]
    features_root = roots["features"]
    attention_rows = read_jsonl_rows(gold_root / "attention.jsonl")
    driver_rows = read_jsonl_rows(gold_root / "drivers.jsonl")
    narrative_rows = read_jsonl_rows(gold_root / "narratives.jsonl")
    market_feature_rows = read_jsonl_rows(features_root / "market_features.jsonl")
    derivatives_feature_rows = read_jsonl_rows(features_root / "derivatives_features.jsonl")

    public_rows = [
        build_public_attention_record(
            symbol=row["symbol"],
            narrative=row["narrative"],
            attention_score=row["attention_score"],
            top_driver=row["top_driver"],
            regime_tag=row["regime_tag"],
            confirmation_score=row["confirmation_score"],
        )
        for row in attention_rows
    ]

    outputs_root = roots["public"]
    public_attention_path = outputs_root / "crypto_attention_public.jsonl"
    write_jsonl_rows(public_attention_path, public_rows)

    summary_path = outputs_root / "crypto-market-intelligence-summary.md"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(build_portfolio_report(attention_rows, narrative_rows), encoding="utf-8")

    site_root = roots["site"]
    site_root.mkdir(parents=True, exist_ok=True)
    site_data_path = site_root / "site_data.js"
    site_data_path.write_text(
        build_site_data_script(
            build_site_payload(
                attention_rows,
                narrative_rows,
                driver_rows=driver_rows,
                market_feature_rows=market_feature_rows,
                derivatives_feature_rows=derivatives_feature_rows,
            )
        ),
        encoding="utf-8",
    )
    return {
        "public_attention": public_attention_path,
        "summary": summary_path,
        "site_data": site_data_path,
    }


def main() -> None:
    settings = AppSettings.from_env()
    outputs = run_public_export_stage(settings)
    print(f"public artifacts exported to {outputs['summary'].parent}")


if __name__ == "__main__":
    main()
