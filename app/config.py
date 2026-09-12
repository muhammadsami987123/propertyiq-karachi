"""Application configuration.

Settings are read from environment variables / a local .env file via
pydantic-settings. Never commit real secrets — see .env.example at the repo
root for documented placeholder values.
"""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_ADMIN_TOKEN_PLACEHOLDER = "changeme-admin-token-please-override"

# Repository root (two levels up from this file: app/config.py -> app -> root)
BASE_DIR: Path = Path(__file__).resolve().parent.parent

DATA_DIR: Path = BASE_DIR / "app" / "data"
LOCATIONS_FILE: Path = DATA_DIR / "locations" / "karachi_locations.json"
BOUNDARY_FILE: Path = DATA_DIR / "geo" / "karachi_boundary.geojson"
LOCALITIES_FILE: Path = DATA_DIR / "geo" / "localities.geojson"
MARKET_FILE: Path = DATA_DIR / "market" / "karachi_market_data.json"
TRENDS_FILE: Path = DATA_DIR / "market" / "karachi_market_trends.json"
SOURCES_FILE: Path = DATA_DIR / "sources" / "sources.json"

TEMPLATES_DIR: Path = BASE_DIR / "frontend" / "templates"
STATIC_DIR: Path = BASE_DIR / "frontend" / "static"


class Settings(BaseSettings):
    """Runtime configuration, overridable via environment variables or .env."""

    ADMIN_TOKEN: str = DEFAULT_ADMIN_TOKEN_PLACEHOLDER
    CORS_ORIGINS: str = "http://localhost:8000,http://127.0.0.1:8000"
    DEBUG: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origins_list(self) -> list[str]:
        """CORS_ORIGINS as a list; '*' or empty means allow-all (dev only)."""
        raw = (self.CORS_ORIGINS or "").strip()
        if not raw or raw == "*":
            return ["*"]
        return [origin.strip() for origin in raw.split(",") if origin.strip()]

    @property
    def cors_allow_credentials(self) -> bool:
        """Credentialed CORS is never safe combined with a wildcard origin."""
        return self.cors_origins_list != ["*"]

    def require_production_admin_token(self) -> None:
        """Refuse to run with the placeholder admin token outside debug mode."""
        if not self.DEBUG and self.ADMIN_TOKEN == DEFAULT_ADMIN_TOKEN_PLACEHOLDER:
            raise RuntimeError(
                "ADMIN_TOKEN is still set to the placeholder value. Set a strong, "
                "unique ADMIN_TOKEN via environment variable or .env before running "
                "outside DEBUG mode (see .env.example)."
            )


settings = Settings()
settings.require_production_admin_token()
