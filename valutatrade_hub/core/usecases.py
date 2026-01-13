from datetime import datetime
from typing import Optional

from valutatrade_hub.core.utils import load_json, save_json
from valutatrade_hub.core.currencies import get_currency
from valutatrade_hub.core.exceptions import (
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
    Фейковое обновление курса.
    Возвращает dict с новой структурой.
    """
    now = datetime.now().isoformat(timespec="seconds") + "Z"  # добавляем Z для UTC

    fake_rates = {
        "USD_BTC": {"rate": 1 / 59337.21, "updated_at": now, "source": "fake_rates"},
        "BTC_USD": {"rate": 59337.21, "updated_at": now, "source": "fake_rates"},
        "EUR_USD": {"rate": 1.0786, "updated_at": now, "source": "fake_rates"},
        "USD_EUR": {
            "rate": 1 / 1.0786,
            "updated_at": now,
            "source": "fake_rates",
        },
        "RUB_USD": {"rate": 0.01016, "updated_at": now, "source": "fake_rates"},
        "USD_RUB": {"rate": 98.42, "updated_at": now, "source": "fake_rates"},
        "ETH_USD": {"rate": 3720.00, "updated_at": now, "source": "fake_rates"},
        "USD_ETH": {"rate": 1 / 3720.00, "updated_at": now, "source": "fake_rates"},
    }

    if pair_key in fake_rates:
        return fake_rates[pair_key]
    return None


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

    wallets["USD"]["balance"] -= estimated_value

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

    rates_data = load_json(RATES_FILE)

    key = f"{from_code}_{to_code}"
    pairs = rates_data["pairs"]
    rate_info = pairs.get(key)
    ttl_seconds = settings.get("RATES_TTL_SECONDS", 600)

    # Проверка текущего курса
    def is_fresh(info: dict) -> bool:
        try:
            updated_at_str = info["updated_at"].rstrip("Z")
            updated_at = datetime.fromisoformat(updated_at_str)
            return (datetime.now() - updated_at).total_seconds() <= ttl_seconds
        except Exception:
            return False

    # Если курса нет или он устарел
    if not rate_info or not is_fresh(rate_info):
        new_info = _refresh_rate(key)
        if not new_info:
            raise ValueError(f"Курс {from_code}->{to_code} недоступен.")

        # Обновляем структуру
        pairs[key] = new_info
        rates_data["last_refresh"] = datetime.now().isoformat(timespec="seconds") + "Z"
        save_json(RATES_FILE, rates_data)

        return new_info["rate"], new_info["updated_at"]

    # Курс свежий, возвращаем существующий
    return rate_info["rate"], rate_info["updated_at"]


@log_action("SHOW_RATES")
def show_rates(
    currency: Optional[str] = None,
    base: Optional[str] = None,
    top: Optional[int] = None,
    **kwargs,
) -> None:
    """
    Показать курсы валют с фильтрацией
    currency: показывать курсы только для этой валюты
    base: базовая валюта для отображения
    top: показать только N лучших курсов
    """
    rates_data = load_json(RATES_FILE)
    pairs = rates_data.get("pairs", {})

    if not pairs:
        print("Кэш валют пуст. Воспользуйтесь командой 'update-rates'.")
        return

    filtered_pairs = {}

    for pair_key, rate_info in pairs.items():
        from_curr, to_curr = pair_key.split("_")

        if currency and currency.upper() not in (from_curr, to_curr):
            continue

        if base:
            if base.upper() != from_curr:
                continue

        filtered_pairs[pair_key] = rate_info

    if not filtered_pairs:
        print("Нет курсов, соответствующих фильтрам.")
        return

    sorted_pairs = sorted(
        filtered_pairs.items(), key=lambda x: x[1]["rate"], reverse=True
    )

    if top:
        try:
            top = int(top)
            sorted_pairs = sorted_pairs[:top]
        except ValueError:
            print(f"Ошибка: параметр 'top' должен быть числом, получено '{top}'")
            return

    print(f"Курсы валют (всего: {len(sorted_pairs)}):")
    print()

    for pair_key, rate_info in sorted_pairs:
        from_curr, to_curr = pair_key.split("_")
        rate = rate_info["rate"]

        print(f"{from_curr} → {to_curr}: {rate:.7f}")

    print(f"Последнее обновление кэша: {rates_data.get('last_refresh', 'неизвестно')}")
