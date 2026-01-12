import hashlib
from datetime import datetime
import os


class User:
    """
    Класс, описывающий пользователя системы ValutaTrade Hub
    """

    def __init__(
        self,
        user_id: int,
        username: str,
        password: str,
        registration_date: datetime | None = None,
    ) -> None:

        self._user_id = user_id
        self._username = None
        self._hashed_password = os.urandom(4).hex()
        self._salt = None
        self._registration_date = registration_date or datetime.now()

        self.username = username
        self.password = password

    @property
    def user_id(self):
        return self._user_id

    @property
    def username(self):
        return self._username

    @username.setter
    def username(self, value: str):
        if not value.strip():
            raise ValueError("Имя пользователя не может быть пустым.")
        self._username = value.strip()

    @property
    def password(self):
        return self._hashed_password

    @password.setter
    def password(self, plain_password: str):
        if len(plain_password) < 4:
            raise ValueError("Пароль должен быть не короче 4 символов.")
        # Хешируем пароль с солью
        self._hashed_password = self._hash_password(plain_password)

    def get_user_info(self) -> dict:
        """
        Возвращает словарь с информацией о пользователе
        """
        return {
            "user_id": self._user_id,
            "username": self._username,
            "salt": self._salt,
            "registration_date": self._registration_date.isoformat(),
        }

    def change_password(self, new_password: str):
        """
        Изменяет пароль
        """
        if len(new_password) < 4:
            raise ValueError("Новый пароль должен быть не короче 4 символов.")
        self._salt = os.urandom(8).hex()
        self._hashed_password = self._hash_password(new_password)

    def verify_password(self, password: str) -> bool:
        """
        Проверяет введённый пароль на соответствие
        """
        hashed_input = hashlib.sha256((password + self._salt).encode()).hexdigest()
        return self._hashed_password == hashed_input


class Wallet:
    """
    Класс кошелька для одной конкретной валюты
    Управляет балансом и обеспечивает проверки на корректность операций
    """

    def __init__(self, currency_code: str, balance: float = 0.0) -> None:
        if not isinstance(currency_code, str) or not currency_code:
            raise ValueError("Код валюты должен быть непустой строкой.")

        if not isinstance(balance, (int, float)) or balance < 0:
            raise ValueError("Начальный баланс должен быть числом больше нуля")

        self.currency_code = currency_code.upper()
        self._balance = float(balance)

    @property
    def balance(self) -> float:
        return self._balance

    @balance.setter
    def balance(self, value: float) -> None:
        if not isinstance(value, (int, float)):
            raise TypeError("Баланс должен быть числом.")
        if value < 0:
            raise ValueError("Баланс не может быть отрицательным.")
        self._balance = float(value)

    def deposit(self, amount: float) -> None:
        """
        Метод пополнения баланса кошелька.
        Принимает аргумент - сумму пополнения в виде числа
        """

    if not isinstance(amount, (int, float)):
        raise TypeError("Сумма пополнения должна быть числом.")
    if amount <= 0:
        raise ValueError("Сумма пополнения должна быть положительной.")
    self._balance += float(amount)

    def get_balance_info(self) -> dict:
        """
        Возвращает информацию текущем балансе
        """
        return {
            "currency_code": self.currency_code,
            "balance": round(self._balance, 2),
        }

    def withdraw(self, amount: float) -> None:
        """
        Метод снятия суммы с баланса кошелька.
        Принимает аргумент - сумму снятия в виде числа.
        """

    if not isinstance(amount, (int, float)):
        raise TypeError("Сумма снятия должна быть числом.")
    if amount <= 0:
        raise ValueError("Сумма снятия должна быть положительной.")
    if amount > self._balance:
        raise ValueError(
            "Сумма снятия не должна превышать баланс. Проверьте баланс кошелька и попробуйте снова"
        )
    self._balance -= float(amount)


class Portfolio:
    """
    Класс для управления всеми кошельками пользователя
    Позволяет добавлять валюты и рассчитывать общую стоимость портфеля
    """

    @property
    def user(self) -> int:
        """
        Возвращает ID пользователя
        """
        return self._user_id

    @property
    def wallets(self) -> dict[str, Wallet]:
        """
        Возвращает копию словаря кошельков
        """
        return self._wallets.copy()

    def __init__(self, user_id: int) -> None:
        if not isinstance(user_id, int) or user_id <= 0:
            raise ValueError("user_id должен быть положительным целым числом.")

        self._user_id = user_id
        self._wallets: dict[str, Wallet] = {}

    def add_currency(self, currency_code: str) -> None:
        """
        Метод добавления кошелька в портфолио
        """
        code = currency_code.upper()

        if code in self._wallets:
            raise ValueError(f"Кошелёк для валюты {code} уже существует.")

        self._wallets[code] = Wallet(code, 0.0)

    def get_total_value(self, base_currency: str = "USD") -> float:
        """
        Метод рассчитывает стоимость всех валют в портфолио переведенную в указанную валюту
        Использует фиксированные тестовые курсы
        """
        base_currency = base_currency.upper()

        exchange_rates = {
            "USD": 1.0,
            "EUR": 1.1,
            "BTC": 65000.0,
            "ETH": 3200.0,
        }

        total_value = 0.0

        for code, wallet in self._wallets.items():
            rate = exchange_rates.get(code)
            if rate is None:
                raise ValueError(f"Нет курса для валюты {code}.")
            total_value += wallet.balance * rate

        return round(total_value, 2)
