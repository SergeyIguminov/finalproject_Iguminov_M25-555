from abc import ABC, abstractmethod
from valutatrade_hub.core.exceptions import CurrencyNotFoundError


class Currency(ABC):
    """
    Абстрактный базовый класс валюты.
    """

    name: str
    code: str

    def __init__(self, name: str, code: str):
        super().__init__()
        self.name = name
        self.code = code

    @abstractmethod
    def get_display_info(self) -> str:
        """
        Cтроковое представление валюты (для UI и логов).
        """
        pass


class FiatCurrency(Currency):
    """
    Фиатная валюта
    """

    def __init__(self, name: str, code: str, issuing_country: str):
        super().__init__(name, code)
        self.issuing_country = issuing_country

    def get_display_info(self) -> str:
        return f"[FIAT] {self.code} — {self.name} (Issuing: {self.issuing_country})"


class CryptoCurrency(Currency):
    """
    Криптовалюта
    """

    def __init__(self, name: str, code: str, algorithm: str, market_cap: float):
        super().__init__(name, code)
        self.algorithm = algorithm
        self.market_cap = market_cap

    def get_display_info(self) -> str:
        return (
            f"[CRYPTO] {self.code} — {self.name} "
            f"(Algo: {self.algorithm}, MCAP: {self.market_cap:.2e})"
        )


# Реестр валют
def get_currency(code: str) -> Currency:
    """
    Возвращает экземпляр валюты по коду.
    """

    code = code.upper()
    registry = {
        "USD": FiatCurrency("US Dollar", "USD", "United States"),
        "EUR": FiatCurrency("Euro", "EUR", "Eurozone"),
        "RUB": FiatCurrency("Russian Ruble", "RUB", "Russia"),
        "BTC": CryptoCurrency("Bitcoin", "BTC", "SHA-256", 1.12e12),
        "ETH": CryptoCurrency("Ethereum", "ETH", "Ethash", 4.45e11),
    }

    if code not in registry:
        raise CurrencyNotFoundError(f"Неизвестная валюта: {code}")

    return registry[code]
