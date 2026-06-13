import os

from pydantic import BaseModel


class AppSettings(BaseModel):
    coingecko_base_url: str = "https://api.coingecko.com/api/v3"
    binance_base_url: str = "https://fapi.binance.com"
    defillama_base_url: str = "https://api.llama.fi"
    public_export_dir: str = "artifacts/public"
    bronze_output_dir: str = "artifacts/bronze"
    silver_output_dir: str = "artifacts/silver"
    features_output_dir: str = "artifacts/features"
    gold_output_dir: str = "artifacts/gold"
    site_output_dir: str = "site"
    public_ssl_verify: bool = True

    @classmethod
    def from_env(cls) -> "AppSettings":
        raw_ssl = os.getenv("PUBLIC_SSL_VERIFY")
        ssl_verify = True if raw_ssl is None else raw_ssl.lower() not in {"0", "false", "no"}
        return cls(
            coingecko_base_url=os.getenv("COINGECKO_BASE_URL", "https://api.coingecko.com/api/v3"),
            binance_base_url=os.getenv("BINANCE_BASE_URL", "https://fapi.binance.com"),
            defillama_base_url=os.getenv("DEFILLAMA_BASE_URL", "https://api.llama.fi"),
            public_export_dir=os.getenv("PUBLIC_EXPORT_DIR", "artifacts/public"),
            bronze_output_dir=os.getenv("BRONZE_OUTPUT_DIR", "artifacts/bronze"),
            silver_output_dir=os.getenv("SILVER_OUTPUT_DIR", "artifacts/silver"),
            features_output_dir=os.getenv("FEATURES_OUTPUT_DIR", "artifacts/features"),
            gold_output_dir=os.getenv("GOLD_OUTPUT_DIR", "artifacts/gold"),
            site_output_dir=os.getenv("SITE_OUTPUT_DIR", "site"),
            public_ssl_verify=ssl_verify,
        )
