from __future__ import annotations

import os
from pathlib import Path
from typing import Any


class SettingsLoader:
    """
    Singleton: хранит и выдаёт конфигурации путей и TTL.
    """

    _instance: "SettingsLoader | None" = None
    _initialized: bool = False

    def __new__(cls) -> "SettingsLoader":
        """
        Выбрал реализацию через new, потому что реализация проще.
        Кода меньше, за счёт этого читаемость и ясность кода значительно выше.
        """
        if SettingsLoader._instance is None:
            SettingsLoader._instance = super().__new__(cls)
            SettingsLoader._instance._init_values()

        return SettingsLoader._instance

    def _resolve_data_dir(self) -> Path:
        """
        Приоритет:
        1) Путь через переменную окружения
        2) data в корне проекта
        """

        if env_dir := os.getenv("VALUTATRADE_DATA_DIR"):
            path = Path(env_dir)
            return path
        return Path("data")

    def _init_values(self) -> None:

        data_dir = self._resolve_data_dir()

        # Создаем директорию если её нет
        if not os.getenv("VALUTATRADE_DATA_DIR"):
            data_dir.mkdir(exist_ok=True)
        else:
            data_dir.mkdir(parents=True, exist_ok=True)

        self._values = {
            "DATA_DIR": str(data_dir),
            "USERS_FILE": str(data_dir / "users.json"),
            "PORTFOLIOS_FILE": str(data_dir / "portfolios.json"),
            "RATES_FILE": str(data_dir / "rates.json"),
            "RATES_TTL_SECONDS": int(os.getenv("VALUTATRADE_RATES_TTL", "600")),
        }

    def get(self, key: str, default: Any | None = None) -> Any:
        return self._values.get(key, default)
