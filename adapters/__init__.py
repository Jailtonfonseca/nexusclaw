"""NexusClaw - Módulo de Adaptadores"""

from adapters.base import (
    BaseAdapter,
    TelegramAdapter,
    DiscordAdapter,
    CLIAdapter,
    WebAdapter,
    ADAPTERS
)

__all__ = [
    "BaseAdapter",
    "TelegramAdapter", 
    "DiscordAdapter",
    "CLIAdapter",
    "WebAdapter",
    "ADAPTERS"
]
