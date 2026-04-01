from functools import lru_cache

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    app_name: str = "Mrinalini ThreatMirror API"
    environment: str = "development"
    database_url: str
    abuseipdb_api_key: str = ""
    virustotal_api_key: str = ""
    gemini_api_key: str = ""
    alert_generation_interval_seconds: int = 60
    request_timeout_seconds: int = 15

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
