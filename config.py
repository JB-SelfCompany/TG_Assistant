"""Configuration management using Pydantic Settings"""
from pathlib import Path
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Bot configuration settings"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    # Bot settings
    bot_token: str = Field(..., description="Telegram Bot Token")
    admin_user_id: int = Field(..., description="Admin user ID")
    
    # Weather settings
    weather_api_key: str = Field(..., description="OpenWeatherMap API key")
    default_city: str = Field(default="Volzhskiy", description="Default city for weather")
    
    # Location settings
    default_country: str = Field(default="Россия", description="Default country")
    default_region: str = Field(default="Волгоградская область", description="Default region")
    default_timezone: str = Field(default="Europe/Moscow", description="Default timezone")
    
    # Database settings
    database_path: Path = Field(default=Path("./bot_database.db"), description="SQLite database path")
    
    # Logging
    log_level: str = Field(default="INFO", description="Logging level")


# Create global settings instance
settings = Settings()