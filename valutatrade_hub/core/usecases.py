import json
import os
from datetime import datetime

from valutatrade_hub.core.currencies import get_currency
from valutatrade_hub.core.exceptions import (
    ApiRequestError,
    CurrencyNotFoundError,
    InsufficientFundsError,
)

from valutatrade_hub.infra.settings import SettingsLoader
from valutatrade_hub.decorators import log_action
from valutatrade_hub.logging_config import setup_logger


settings = SettingsLoader()
logger = setup_logger()
USERS_FILE = settings.get("USERS_FILE")
PORTFOLIOS_FILE = settings.get("PORTFOLIOS_FILE")
RATES_FILE = settings.get("RATES_FILE")


def _refresh_rate(pair_key: str) -> dict | None:
    """
    Фейтовое обновление курса (вместо Parser Service).
    Возвращает dict или None.
    """
    now = datetime.now().isoformat(timespec="seconds")
    fake_rates = {
        "USD_BTC": {"rate": 1 / 59337.21, "updated_at": now},
        "BTC_USD": {"rate": 59337.21, "updated_at": now},
        "EUR_USD": {"rate": 1.0786, "updated_at": now},
        "USD_EUR": {"rate": 1 / 1.0786, "updated_at": now},
        "RUB_USD": {"rate": 0.01016, "updated_at": now},
        "USD_RUB": {"rate": 98.42, "updated_at": now},
        "ETH_USD": {"rate": 3720.00, "updated_at": now},
        "USD_ETH": {"rate": 1 / 3720.00, "updated_at": now},
    }

    return fake_rates.get(pair_key)


def load_json(file_path: str) -> list | dict:
    if not os.path.exists(file_path):
        name = os.path.basename(file_path)
        if name in ("users.json", "portfolios.json"):
            return []
        if name == "rates.json":
            return {}
        return {}
    with open(file_path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            name = os.path.basename(file_path)
            if name in ("users.json", "portfolios.json"):
                return []
            if name == "rates.json":
                return {}
            return {}


def save_json(file_path: str, data) -> None:
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def get_user_portfolio(user_id: int) -> dict | None:
    portfolios = load_json(PORTFOLIOS_FILE)
    return next((p for p in portfolios if p["user_id"] == user_id), None)


@log_action("BUY")
def buy(user_id: int, currency_code: str, amount: float, rate: float, **kwargs) -> None:
    """
    Покупка валюты с логированием и валидацией
    """
    if amount <= 0:
        raise ValueError("'amount' должен быть положительным числом")

    try:
        get_currency(currency_code)
    except CurrencyNotFoundError as e:
        logger.error(str(e))
        raise

    if currency_code.upper() == "USD":
        raise "USD - базовая валюта кошелька. Для получения USD продайте другую валюту (sell)"

    # Загружаем весь список портфелей
    portfolios = load_json(PORTFOLIOS_FILE)

    # Ищем нужный портфель пользователя
    portfolio = next((p for p in portfolios if p["user_id"] == user_id), None)
    if not portfolio:
        portfolio = {"user_id": user_id, "wallets": {}}

    # Проверка наличия кошелька в портфеле
    wallets = portfolio["wallets"]
    if currency_code not in wallets:
        wallets[currency_code] = {"currency_code": currency_code, "balance": 0.0}

    old_balance = wallets[currency_code]["balance"]
    new_balance = old_balance + amount
    wallets[currency_code]["balance"] = new_balance

    estimated_value = amount * rate

    wallets["USD"] -= estimated_value

    portfolios = load_json(PORTFOLIOS_FILE)
    if not isinstance(portfolios, list):
        portfolios = []
    existing = next((p for p in portfolios if p["user_id"] == user_id), None)
    if existing:
        existing.update(portfolio)
    else:
        portfolios.append(portfolio)
    save_json(PORTFOLIOS_FILE, portfolios)

    logger.info(
        f"Покупка {currency_code}: {amount} @ {rate} → {estimated_value:.2f} USD "
        f"(user_id={user_id})"
    )


@log_action("SELL")
def sell(
    user_id: int, currency_code: str, amount: float, rate: float, **kwargs
) -> None:
    """
    Продажа валюты с валидацией и логированием
    """
    if amount <= 0:
        raise ValueError("'amount' должен быть положительным числом")

    try:
        get_currency(currency_code)
    except CurrencyNotFoundError as e:
        logger.error(str(e))
        raise

    portfolios = load_json(PORTFOLIOS_FILE)
    portfolio = next((p for p in portfolios if p["user_id"] == user_id), None)
    if not portfolio:
        raise ValueError(f"Портфель для user_id={user_id} не найден")

    wallets = portfolio["wallets"]
    if currency_code not in wallets:
        raise CurrencyNotFoundError(f"У вас нет кошелька '{currency_code}'")

    balance = wallets[currency_code]["balance"]
    if balance < amount:
        raise InsufficientFundsError(balance, amount, currency_code)

    estimated_revenue = amount * rate

    wallets[currency_code]["balance"] -= amount
    wallets["USD"]["balance"] += estimated_revenue

    save_json(PORTFOLIOS_FILE, portfolios)

    logger.info(
        f"Продажа {currency_code}: {amount} @ {rate} → {estimated_revenue:.2f} USD "
        f"(user_id={user_id})"
    )


@log_action("GET_RATE")
def get_rate(from_code: str, to_code: str, **kwargs) -> tuple[float, str]:
    """
    Получение и обновление курса валют с логированием
    """
    rates = load_json(RATES_FILE)
    key = f"{from_code}_{to_code}"
    rate_info = rates.get(key)
    ttl_seconds = settings.get("RATES_TTL_SECONDS")

    # Проверка текущего курса
    def is_fresh(info: dict) -> bool:
        try:
            updated_at = datetime.fromisoformat(info["updated_at"])
            return (datetime.now() - updated_at).total_seconds() <= ttl_seconds
        except Exception:
            return False

    if not rate_info:
        new_info = _refresh_rate(key)
        if not new_info:
            raise ValueError(f"Курс {from_code}->{to_code} недоступен.")
        rates[key] = new_info
        save_json(RATES_FILE, rates)
        return new_info["rate"], new_info["updated_at"]

    if not is_fresh(rate_info):
        new_info = _refresh_rate(key)
        if not new_info:
            raise ApiRequestError("Данные курсов устарели. Повторите попытку позже.")
        rates[key] = new_info
        save_json(RATES_FILE, rates)
        return new_info["rate"], new_info["updated_at"]

    return rate_info["rate"], rate_info["updated_at"]
