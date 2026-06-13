from pathlib import Path

from scripts.export_public_artifacts import resolve_export_roots
from src.config.settings import AppSettings
from src.publish.export_gold import build_public_attention_record


def test_public_attention_record_hides_internal_noise():
    row = build_public_attention_record(
        symbol="TAO",
        narrative="ai_data",
        attention_score=0.91,
        top_driver="onchain_confirmation",
        regime_tag="bullish_attention",
        confirmation_score=0.72,
    )
    assert row == {
        "symbol": "TAO",
        "narrative": "ai_data",
        "attention_score": 0.91,
        "top_driver": "onchain_confirmation",
        "regime_tag": "bullish_attention",
        "confirmation_score": 0.72,
    }


def test_resolve_export_roots_uses_app_settings_directories(tmp_path: Path):
    settings = AppSettings(
        gold_output_dir="custom/gold",
        features_output_dir="custom/features",
        public_export_dir="custom/public",
        site_output_dir="custom/site",
    )

    roots = resolve_export_roots(settings, project_root=tmp_path)

    assert roots["gold"] == tmp_path / "custom" / "gold"
    assert roots["features"] == tmp_path / "custom" / "features"
    assert roots["public"] == tmp_path / "custom" / "public"
    assert roots["site"] == tmp_path / "custom" / "site"
    assert roots["public"] != tmp_path / "outputs"
    assert roots["site"] != tmp_path / "site"
