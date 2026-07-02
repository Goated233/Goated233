from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the personal relationship bot."""

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    environment: str = 'development'
    log_level: str = 'INFO'
    discord_token: str = ''
    mongo_uri: str = 'mongodb://localhost:27017'
    mongo_database: str = 'relationship_bot'
    openai_api_key: str = ''
    openai_model: str = 'gpt-4.1-mini'
    owner_ids: list[int] = Field(default_factory=lambda: [1417262684990083142, 1516247373716787363])
    command_prefix: str = ','
    backup_channel_id: int | None = None
    reminder_poll_seconds: int = 60
    counselor_max_history: int = 12


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
