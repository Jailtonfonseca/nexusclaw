"""
NexusClaw - Configurações Centrais do Sistema
=============================================

Este módulo carrega e valida todas as configurações do sistema
a partir de variáveis de ambiente.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List, Optional
from functools import lru_cache


class Settings(BaseSettings):
    """Configurações principais do NexusClaw"""
    
    # Gerais
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=True, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    secret_key: str = Field(default="dev-secret-key", env="SECRET_KEY")
    
    # Banco de dados
    database_url: str = Field(
        default="postgresql://nexus:nexus@localhost:5432/nexusai",
        env="DATABASE_URL"
    )
    
    # Cache
    redis_url: str = Field(
        default="redis://localhost:6379",
        env="REDIS_URL"
    )
    
    # LLM - Ollama
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        env="OLLAMA_BASE_URL"
    )
    ollama_model: str = Field(default="llama3", env="OLLAMA_MODEL")
    ollama_temperature: float = Field(default=0.7, env="OLLAMA_TEMPERATURE")
    ollama_max_tokens: int = Field(default=4096, env="OLLAMA_MAX_TOKENS")
    
    # LLM - OpenAI (Fallback)
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4-turbo-preview", env="OPENAI_MODEL")
    openai_base_url: str = Field(
        default="https://api.openai.com/v1",
        env="OPENAI_BASE_URL"
    )
    
    # LLM - Anthropic (Fallback)
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    
    # Memória Vetorial
    qdrant_host: str = Field(default="localhost", env="QDRANT_HOST")
    qdrant_port: int = Field(default=6333, env="QDRANT_PORT")
    qdrant_grpc_port: int = Field(default=6334, env="QDRANT_GRPC_PORT")
    qdrant_collection: str = Field(default="nexus_memories", env="QDRANT_COLLECTION")
    
    # Embeddings
    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        env="EMBEDDING_MODEL"
    )
    embedding_device: str = Field(default="cpu", env="EMBEDDING_DEVICE")
    
    # Canais de Comunicação
    telegram_bot_token: Optional[str] = Field(default=None, env="TELEGRAM_BOT_TOKEN")
    telegram_webhook_url: Optional[str] = Field(default=None, env="TELEGRAM_WEBHOOK_URL")
    
    discord_bot_token: Optional[str] = Field(default=None, env="DISCORD_BOT_TOKEN")
    discord_guild_id: Optional[str] = Field(default=None, env="DISCORD_GUILD_ID")
    discord_channel_ids: str = Field(default="", env="DISCORD_CHANNEL_IDS")
    
    # WhatsApp (Twilio)
    twilio_account_sid: Optional[str] = Field(default=None, env="TWILIO_ACCOUNT_SID")
    twilio_auth_token: Optional[str] = Field(default=None, env="TWILIO_AUTH_TOKEN")
    twilio_phone_number: Optional[str] = Field(default=None, env="TWILIO_PHONE_NUMBER")
    
    # Busca
    searxng_url: str = Field(default="http://localhost:8080", env="SEARXNG_URL")
    
    # Segurança
    allowed_users: str = Field(default="", env="ALLOWED_USERS")
    session_expire_hours: int = Field(default=24, env="SESSION_EXPIRE_HOURS")
    max_requests_per_minute: int = Field(default=60, env="MAX_REQUESTS_PER_MINUTE")
    
    # Avançadas
    memory_context_window: int = Field(default=10, env="MEMORY_CONTEXT_WINDOW")
    memory_summary_threshold: int = Field(default=20, env="MEMORY_SUMMARY_THRESHOLD")
    enable_autonomous_mode: bool = Field(default=True, env="ENABLE_AUTONOMOUS_MODE")
    max_parallel_tasks: int = Field(default=5, env="MAX_PARALLEL_TASKS")
    sandbox_execution_timeout: int = Field(default=30, env="SANDBOX_EXECUTION_TIMEOUT")
    
    @property
    def allowed_users_list(self) -> List[str]:
        """Parse allowed users from comma-separated string"""
        if not self.allowed_users:
            return []
        return [u.strip() for u in self.allowed_users.split(",")]
    
    @property
    def discord_channel_ids_list(self) -> List[str]:
        """Parse Discord channel IDs from comma-separated string"""
        if not self.discord_channel_ids:
            return []
        return [c.strip() for c in self.discord_channel_ids.split(",")]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Retorna configurações em cache (singleton)"""
    return Settings()
