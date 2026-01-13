"""
Модуль вспомогательных функций (utils).
Содержит общие инструменты, используемые в разных частях проекта.
"""

from datetime import datetime
from pathlib import Path
import json


def format_timestamp() -> str:
    """Возвращает текущее время в ISO-формате (UTC)."""
    return datetime.utcnow().isoformat()


def split_pair(pair: str) -> tuple[str, str]:
    """Разделяет валютную пару 'BTC_USD' на ('BTC', 'USD')."""
    return tuple(pair.split("_"))


def load_json(file_path) -> list | dict:
    file_path = Path(file_path)
    if not file_path.exists():
        if file_path.name in ("users.json", "portfolios.json"):
            return []
        return {}
    with file_path.open("r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            if file_path.name in ("users.json", "portfolios.json"):
                return []
            return {}


def save_json(file_path, data) -> None:
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with file_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
