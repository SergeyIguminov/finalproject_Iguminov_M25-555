"""
Модуль вспомогательных функций (utils).
Содержит общие инструменты, используемые в разных частях проекта.
"""

from datetime import datetime


def format_timestamp() -> str:
    """Возвращает текущее время в ISO-формате (UTC)."""
    return datetime.utcnow().isoformat()


def split_pair(pair: str) -> tuple[str, str]:
    """Разделяет валютную пару 'BTC_USD' на ('BTC', 'USD')."""
    return tuple(pair.split("_"))
