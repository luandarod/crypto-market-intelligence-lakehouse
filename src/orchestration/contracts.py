from dataclasses import dataclass
from pathlib import Path

from src.config.settings import AppSettings


@dataclass(frozen=True)
class ArtifactContract:
    stage_name: str
    root: Path
    required_files: list[str]

    def resolve_outputs(self) -> list[Path]:
        return [self.root / name for name in self.required_files]


def build_artifact_contracts(settings: AppSettings) -> dict[str, ArtifactContract]:
    return {
        "bronze": ArtifactContract(
            "bronze",
            Path(settings.bronze_output_dir),
            ["public_sources.jsonl"],
        ),
        "silver": ArtifactContract(
            "silver",
            Path(settings.silver_output_dir),
            ["market.jsonl", "derivatives.jsonl", "onchain.jsonl"],
        ),
        "features": ArtifactContract(
            "features",
            Path(settings.features_output_dir),
            [
                "market_features.jsonl",
                "derivatives_features.jsonl",
                "onchain_features.jsonl",
            ],
        ),
        "gold": ArtifactContract(
            "gold",
            Path(settings.gold_output_dir),
            ["attention.jsonl", "drivers.jsonl", "narratives.jsonl"],
        ),
        "public": ArtifactContract(
            "public",
            Path(settings.public_export_dir),
            [
                "crypto_attention_public.jsonl",
                "crypto-market-intelligence-summary.md",
                "run_manifest.json",
            ],
        ),
        "site": ArtifactContract(
            "site",
            Path(settings.site_output_dir),
            ["site_data.js"],
        ),
    }
