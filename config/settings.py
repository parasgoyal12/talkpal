"""
Configuration management for the Study Companion Bot
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""

    # Azure AI Configuration
    azure_openai_api_key: str = Field(..., env="AZURE_OPENAI_API_KEY")
    azure_openai_endpoint: str = Field(..., env="AZURE_OPENAI_ENDPOINT")
    azure_openai_deployment_name: str = Field(default="gpt-4", env="AZURE_OPENAI_DEPLOYMENT_NAME")
    azure_openai_api_version: str = Field(default="2024-02-15-preview", env="AZURE_OPENAI_API_VERSION")

    # Mem0 Configuration
    mem0_api_key: Optional[str] = Field(None, env="MEM0_API_KEY")

    # Database Configuration
    database_url: str = Field(..., env="DATABASE_URL")

    # Telegram Configuration
    telegram_bot_token: Optional[str] = Field(None, env="TELEGRAM_BOT_TOKEN")

    # Twilio Configuration
    twilio_account_sid: Optional[str] = Field(None, env="TWILIO_ACCOUNT_SID")
    twilio_auth_token: Optional[str] = Field(None, env="TWILIO_AUTH_TOKEN")
    twilio_whatsapp_number: Optional[str] = Field(None, env="TWILIO_WHATSAPP_NUMBER")

    # n8n Configuration
    n8n_webhook_url: str = Field(..., env="N8N_WEBHOOK_URL")
    n8n_api_key: Optional[str] = Field(None, env="N8N_API_KEY")

    # Redis Configuration
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")

    # Application Configuration
    app_host: str = Field(default="0.0.0.0", env="APP_HOST")
    app_port: int = Field(default=8000, env="APP_PORT")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
