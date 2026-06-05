from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


REPO_ROOT = Path(__file__).resolve().parents[3]
BACKEND_ROOT = REPO_ROOT / "backend"


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="MOTIVS_",
        env_file=(".env", "backend/.env"),
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    app_name: str = "electricity-factura.motivs.ai"
    environment: Literal["development", "test", "staging", "production"] = "development"
    log_level: str = "INFO"

    api_prefix: str = "/api"
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
    )
    trusted_hosts: list[str] = Field(default_factory=lambda: ["*"])

    artifact_dir: Path = BACKEND_ROOT / "artifacts"
    upload_dir: Path = BACKEND_ROOT / ".uploads"

    tenant_slug: str = Field(default="factura-es", alias="MOTIVS_TENANT_SLUG")
    hmac_key: str = Field(default="dev-only-replace-in-prod", alias="MOTIVS_HMAC_KEY")

    factura_contract_path: Path = Field(
        default=BACKEND_ROOT / "contracts" / "factura_electricidad.yaml",
        alias="MOTIVS_FACTURA_CONTRACT_PATH",
    )
    ofertas_contract_path: Path = Field(
        default=BACKEND_ROOT / "contracts" / "oferta_electricidad.yaml",
        alias="MOTIVS_OFERTAS_CONTRACT_PATH",
    )

    regions: list[str] = Field(
        default_factory=lambda: ["barcelona", "girona", "lleida", "tarragona"],
        alias="MOTIVS_REGIONS",
    )

    redis_url: str | None = Field(default=None, alias="MOTIVS_REDIS_URL")
    profile_redis_ttl: int = Field(default=1800, alias="MOTIVS_PROFILE_REDIS_TTL")
    upload_disk_ttl: int = Field(default=300, alias="MOTIVS_UPLOAD_DISK_TTL")

    offers_bucket: str = Field(default="motivs-factura-offers", alias="MOTIVS_OFFERS_BUCKET")
    lancedb_uri: Path = Field(
        default=BACKEND_ROOT / "artifacts" / "lancedb",
        alias="MOTIVS_LANCEDB_URI",
    )
    offers_table: str = Field(default="offers", alias="MOTIVS_OFFERS_TABLE")

    cnmc_scrape_interval: int = Field(default=86400, alias="MOTIVS_CNMC_SCRAPE_INTERVAL")

    blurb_enabled: bool = Field(default=False, alias="MOTIVS_BLURB_ENABLED")

    admin_token: str = Field(default="", alias="MOTIVS_ADMIN_TOKEN")

    @field_validator("cors_origins", "trusted_hosts", "regions", mode="before")
    @classmethod
    def _split_csv(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator(
        "artifact_dir",
        "upload_dir",
        "factura_contract_path",
        "ofertas_contract_path",
        "lancedb_uri",
        mode="before",
    )
    @classmethod
    def _expand_paths(cls, value: object) -> object:
        if isinstance(value, str):
            return Path(value).expanduser()
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
