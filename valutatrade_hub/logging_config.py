import logging
import os

from valutatrade_hub.infra.settings import SettingsLoader


def setup_logger():
    """Единый логгер приложения."""
    settings = SettingsLoader()
    logs_dir = settings.get("LOGS_DIR") or "logs"
    os.makedirs(logs_dir, exist_ok=True)

    log_file = os.path.join(logs_dir, "app.log")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )

    return logging.getLogger("ValutaTrade")