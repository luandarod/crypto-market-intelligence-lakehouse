from pathlib import Path

from scripts.export_public_artifacts import build_site_data_script, build_site_payload


def test_build_site_payload_summarizes_attention_and_regimes():
    payload = build_site_payload(
        attention_rows=[
            {
                "symbol": "BTC",
                "narrative": "bitcoin_ecosystem",
                "attention_score": 8.35,
                "confirmation_score": 0.6667,
                "top_driver": "derivatives_positioning",
                "regime_tag": "bearish_attention",
            },
            {
                "symbol": "SOL",
                "narrative": "layer1",
                "attention_score": 6.46,
                "confirmation_score": 0.3333,
                "top_driver": "volume_strength",
                "regime_tag": "mixed_attention",
            },
        ],
        narrative_rows=[
            {
                "narrative": "bitcoin_ecosystem",
                "asset_count": 1,
                "avg_attention_score": 8.35,
                "avg_confirmation_score": 0.6667,
            }
        ],
        driver_rows=[
            {
                "symbol": "BTC",
                "crowding_flag": False,
                "breadth_flag": "broad",
                "regime_tag": "bearish_attention",
            },
            {
                "symbol": "SOL",
                "crowding_flag": True,
                "breadth_flag": "narrow",
                "regime_tag": "mixed_attention",
            },
        ],
        market_feature_rows=[
            {
                "symbol": "BTC",
                "close_price": 67432,
                "quote_volume": 59318066245,
                "relative_strength_24h": -5.6506,
                "relative_strength_7d": -11.7803,
                "relative_strength_30d": -14.2869,
            },
            {
                "symbol": "SOL",
                "close_price": 76.8,
                "quote_volume": 3174308631,
                "relative_strength_24h": -4.7793,
                "relative_strength_7d": -8.682,
                "relative_strength_30d": -8.7717,
            },
        ],
        derivatives_feature_rows=[
            {
                "symbol": "BTCUSDT",
                "funding_rate": 8.345e-05,
                "open_interest": 110567.575,
            }
        ],
        run_id="run-demo",
        artifact_version="v2",
        manifest_path=Path("artifacts/public/run_manifest.json"),
    )
    assert payload["run_metadata"]["run_id"] == "run-demo"
    assert payload["run_metadata"]["artifact_version"] == "v2"
    assert payload["run_metadata"]["manifest_path"].endswith("run_manifest.json")
    assert payload["overview"]["asset_count"] == 2
    assert payload["overview"]["narrative_count"] == 2
    assert payload["overview"]["bearish_count"] == 1
    assert payload["overview"]["mixed_count"] == 1
    assert payload["overview"]["driver_mix"]["counts"]["derivatives_positioning"] == 1
    assert payload["overview"]["driver_mix"]["counts"]["volume_strength"] == 1
    assert payload["overview"]["driver_mix"]["counts"]["onchain_confirmation"] == 0
    assert payload["overview"]["driver_mix"]["leading_driver"]["count"] == 1
    assert payload["top_assets"][0]["symbol"] == "BTC"
    assert payload["asset_explorer_rows"][0]["symbol"] == "BTC"
    assert payload["asset_explorer_rows"][0]["breadth_flag"] == "broad"
    assert payload["asset_explorer_rows"][0]["funding_rate"] == 8.345e-05
    assert payload["asset_explorer_rows"][1]["crowding_flag"] is True
    assert payload["asset_explorer_rows"][1]["funding_rate"] is None
    assert payload["databricks_blueprint"][0]["title"] == "Asset Bundles scaffold"
    assert payload["narrative_explorer_rows"][0]["narrative"] == "bitcoin_ecosystem"
    assert payload["narrative_explorer_rows"][1]["leader_symbol"] == "SOL"
    assert payload["narrative_explorer_rows"][1]["asset_symbols"] == ["SOL"]
    assert payload["narrative_health"][0]["leader_symbol"] == "BTC"
    assert payload["narrative_health"][0]["leader_driver"] == "derivatives_positioning"
    assert payload["narrative_health"][1]["leader_regime"] == "mixed_attention"
    assert payload["refresh_policy"]["cadence_label"] == "Every 12 hours"
    assert payload["refresh_policy"]["trigger"] == "github_actions"


def test_build_site_data_script_creates_browser_global():
    script = build_site_data_script({"headline": {"title": "Demo"}})
    assert script.startswith("window.CMIL_SITE_DATA = ")
    assert '"title": "Demo"' in script
