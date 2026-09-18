from pathlib import Path
import os
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Locate workspace root and directories
CORE_DIR = Path(__file__).resolve().parent
APP_DIR = CORE_DIR.parent
BACKEND_DIR = APP_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent if (BACKEND_DIR.parent / "response").exists() else BACKEND_DIR


def _resolve_dir(env_var: str, candidates: list[Path]) -> Path:
    env_val = os.getenv(env_var)
    if env_val:
        p = Path(env_val).resolve()
        if p.exists():
            return p

    for c in candidates:
        if c.exists():
            return c.resolve()

    return candidates[0].resolve()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(
            str(PROJECT_ROOT / ".env"),
            str(BACKEND_DIR / ".env"),
        ),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    PROJECT_NAME: str = "Proposal Scoring API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # API Keys & Model
    GOOGLE_API_KEY: str = Field(
        default_factory=lambda: os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY") or ""
    )
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL")

    # Directories
    BACKEND_DIR: Path = BACKEND_DIR
    PROJECT_ROOT: Path = PROJECT_ROOT
    PROPOSALS_DIR: Path = Field(
        default_factory=lambda: _resolve_dir(
            "PROPOSALS_DIR",
            [
                BACKEND_DIR / "data" / "response",
                PROJECT_ROOT / "response",
            ],
        )
    )
    RFPS_DIR: Path = Field(
        default_factory=lambda: _resolve_dir(
            "RFPS_DIR",
            [
                BACKEND_DIR / "data" / "rfp",
                PROJECT_ROOT / "rfp",
            ],
        )
    )

    # CORS
    CORS_ORIGINS: list[str] = ["*"]


settings = Settings()
