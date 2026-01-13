import os
from dataclasses import dataclass, field


@dataclass
class ParserConfig:
    """
    - EXCHANGERATE_API_KEY - переменная среды, открывает
    доступ к API ExchangeRate.
    - COINGECKO_URL - общая часть ссылки на CoinGecko API.
    - EXCHANGERATE_API_URL - общая часть ссылки на ExchangeRate API.
    - BASE_CURRENCY - базовая валюта.
    - FIAT_CURRENCIES - коды поддерживаемых фиатных валют.
    - FIAT_ID_MAP - имена поддерживаемых фиатных валют.
    - CRYPTO_CURRENCIES - коды поддерживаемых криптовалют.
    - CRYPTO_ID_MAP - имена поддерживаемых криптовалют.
    - RATES_FILE_PATH - путь к файлу с кэшами обменных курсов.
    - HISTORY_FILE_PATH - путь к файлу с историей записей в кэш курсов.
    - REQUEST_TIMEOUT - время в секундах, после которого ожидание
    запроса к API принудительно прекращается.
    """

    EXCHANGERATE_API_KEY: str = os.getenv(
        "EXCHANGERATE_API_KEY", "5c6a631d3269b4bf4543f53b"
    )
    COINGECKO_URL: str = "https://api.coingecko.com/api/v3/simple/price"
    EXCHANGERATE_API_URL: str = "https://v6.exchangerate-api.com/v6"
    BASE_CURRENCY: str = "USD"
    FIAT_CURRENCIES: tuple = ("EUR", "RUB")
    FIAT_ID_MAP: dict = field(
        default_factory=lambda: {
            "EUR": "euro",
            "RUB": "ruble",
        }
    )
    CRYPTO_CURRENCIES: tuple = ("BTC", "ETH")
    CRYPTO_ID_MAP: dict = field(
        default_factory=lambda: {
            "BTC": "bitcoin",
            "ETH": "ethereum",
        }
    )
    RATES_FILE_PATH: str = "data/rates.json"
    HISTORY_FILE_PATH: str = "data/exchange_rates.json"
    REQUEST_TIMEOUT: int = 10
