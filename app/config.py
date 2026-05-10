from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    environment: str = "development"
    log_level: str = "INFO"
    discord_token: str = Field(default="", min_length=0)
    discord_client_id: str = ""
    owner_user_id: int = 1_417_262_684_990_083_142
    owner_display: str = "ntmhaha"
    database_url: str = "postgresql+asyncpg://alpha:omega@localhost:5432/alpha_omega_arcade"
    redis_url: str = "redis://localhost:6379/0"
    home_panel_custom_id: str = "aoa:home"
    admin_panel_custom_id: str = "aoa:admin"
    session_ttl_seconds: int = 3600
    leaderboard_cache_seconds: int = 120
    notification_antispam_seconds: int = 900
    dangerous_action_cooldown_seconds: int = 30
    dungeon_session_timeout_seconds: int = 1800


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
