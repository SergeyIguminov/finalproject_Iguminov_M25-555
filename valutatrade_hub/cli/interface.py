import hashlib
import json
import random
import shlex
import string
from datetime import datetime
from pathlib import Path


from valutatrade_hub.core.exceptions import (
    ApiRequestError,
    CurrencyNotFoundError,
)
from valutatrade_hub.core.usecases import buy, get_rate, sell
from valutatrade_hub.infra.settings import SettingsLoader


settings = SettingsLoader()

USERS_FILE = settings.get("USERS_FILE")
PORTFOLIOS_FILE = settings.get("PORTFOLIOS_FILE")

CURRENT_USER: dict | None = None


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


def register(args: list[str]) -> None:
    """
    Метод регистрации нового пользователя.
    Принимает аргумент формата: register --username <str> --password <str>
    """

    try:
        args_dict = {}
        for i in range(0, len(args), 2):
            key, value = args[i], args[i + 1]
            args_dict[key] = value
    except (IndexError, ValueError):
        print(
            "Ошибка: неправильный формат. "
            "Пример: register --username alice --password 1234"
        )
        return

    username = args_dict.get("--username")
    password = args_dict.get("--password")

    # Проверка на ошибки
    if not username:
        print("Ошибка: имя пользователя не указано.")
        return
    if not password or len(password) <= 3:
        print("Ошибка: пароль должен быть не короче 4 символов.")
        return

    users = load_json(USERS_FILE)

    # Проверка на уникальность
    if any(u["username"] == username for u in users):
        print(f"Имя пользователя '{username}' уже занято.")
        return

    # Генерация id и соли
    new_id = max((u["user_id"] for u in users), default=0) + 1
    salt = "".join(random.choices(string.ascii_letters + string.digits, k=8))
    hashed_password = hashlib.sha256((password + salt).encode()).hexdigest()

    # Создание пользователя
    user = {
        "user_id": new_id,
        "username": username,
        "hashed_password": hashed_password,
        "salt": salt,
        "registration_date": datetime.now().isoformat(),
    }
    users.append(user)
    save_json(USERS_FILE, users)

    # Создание портфеля с начальным USD балансом
    portfolios = load_json(PORTFOLIOS_FILE)
    portfolios.append(
        {
            "user_id": new_id,
            "wallets": {
                "USD": {"currency_code": "USD", "balance": 1000.0}  # начальный баланс
            },
        }
    )
    save_json(PORTFOLIOS_FILE, portfolios)

    # Сообщение об успешной регистрации
    print(
        f"Регистрация проведена успешно. Аккаунт {username} создан."
        f"Войдите: login --username {username} --password ****"
    )


def login(args: list[str]) -> None:
    """
    Авторизация пользователя.
    Принимает аргумент формата: login --username <str> --password <str>
    """

    try:
        args_dict = {}
        for i in range(0, len(args), 2):
            key, value = args[i], args[i + 1]
            args_dict[key] = value
    except (IndexError, ValueError):
        print(
            "Ошибка: неправильный формат."
            "Пример: login --username alice --password 1234"
        )
        return

    username = args_dict.get("--username")
    password = args_dict.get("--password")

    if not username or not password:
        print("Ошибка: укажите и имя пользователя, и пароль.")
        return

    # Загрузка пользователей ---
    users = load_json(USERS_FILE)
    user = next((u for u in users if u["username"] == username), None)

    if not user:
        print(f"Пользователь '{username}' не найден.")
        return

    # Проверка пароля
    hashed_input = hashlib.sha256((password + user["salt"]).encode()).hexdigest()
    if hashed_input != user["hashed_password"]:
        print("Неверный пароль.")
        return

    # Сообщение об успехе
    print(f"Вы вошли как '{username}'")

    global CURRENT_USER
    CURRENT_USER = user


def show_portfolio(args: list[str]) -> None:
    """
    Показывает портфель пользователя.
    Пример: show-portfolio --base USD
    """
    global CURRENT_USER

    # Проверка входа
    if not CURRENT_USER:
        print("Сначала выполните login.")
        return

    base_currency = "USD"
    if "--base" in args:
        try:
            base_currency = args[args.index("--base") + 1].upper()
        except IndexError:
            print("Ошибка: не указана базовая валюта после --base.")
            return

    # Проверка известной валюты
    known_currencies = ["USD", "EUR", "BTC", "ETH", "RUB"]
    if base_currency not in known_currencies:
        print(f"Неизвестная базовая валюта '{base_currency}'.")
        return

    # Загрузка портфеля
    portfolios = load_json(PORTFOLIOS_FILE)

    portfolio = next(
        (p for p in portfolios if p["user_id"] == CURRENT_USER["user_id"]),
        None,
    )

    if not portfolio or not portfolio["wallets"]:
        print("У вас пока нет кошельков.")
        return

    exchange_rates = {
        "USD": 1.0,
        "EUR": 1.07,
        "BTC": 59337.21,
        "ETH": 3720.00,
        "RUB": 0.01016,
    }

    total_value = 0.0

    print(
        f"Портфель пользователя '{CURRENT_USER['username']}' "
        f"(база: {base_currency}):"
    )

    for code, data in portfolio["wallets"].items():
        balance = data.get("balance", 0.0)
        rate = exchange_rates.get(code, 0)
        base_rate = exchange_rates.get(base_currency, 1)
        value_in_base = (balance * rate) / base_rate if base_rate != 0 else 0

        print(f"- {code}: {balance:.4f}  ->  {value_in_base:.2f} {base_currency}")
        total_value += value_in_base

    print("-" * 50)
    print(f"ИТОГО: {total_value:,.2f} {base_currency}")


def show_help():
    print(
        "Вызов команд:\n"
        "<command> <--argument1> <input> <--argument2> <input> ...\n"
        "\n"
        "Поддерживаемые коды валют: USD, EUR, GBP, RUB, BTC, ETH, SOL.\n"
        "\n"
        "Список команд:\n"
        "\n"
        "- register <--argument> <input> - регистрация в системе.\n"
        "Обязательные аргументы:\n"
        "--username <name> - имя пользователя. Не может быть пустым.\n"
        "--password <pass> - пароль. Должен содержать минимум 4 символа.\n"
        "\n"
        "- login <--argument> <input> - авторизация в системе.\n"
        "Обязательные аргументы:\n"
        "--username <name> - имя пользователя.\n"
        "--password <pass> - пароль.\n"
        "\n"
        "- show-portfolio <--argument> <input> - информация о ваших кошельках. "
        "Требует авторизации.\n"
        "Необязательные аргументы:\n"
        "--base <currency> - код валюты (например: USD), по которой учитывать "
        "общий баланс кошельков.\n"
        "\n"
        "- buy <--argument> <input> - купить валюту. Требует авторизации.\n"
        "Обязательные аргументы:\n"
        "--currency <currency> - код валюты (например: USD), которую хотите купить.\n"
        "--amount <currency> - объем покупки в штуках (например: 123.45). "
        "Неотрицательное число.\n"
        "\n"
        "- sell <--argument> <input> - продать валюту. Требует авторизации.\n"
        "Обязательные аргументы:\n"
        "--currency <currency> - код валюты (например: USD), которую хотите продать.\n"
        "--amount <currency> - объем продажи в штуках (например: 123.45). "
        "Неотрицательное число, нужно иметь необходимые средства в кошельке.\n"
        "\n"
        "- get-rate <--argument> <input> - получить курс одной валюты к другой.\n"
        "Обязательные аргументы:\n"
        "--from <currency> - код исходный валюты (например: EUR).\n"
        "--to <currency> - код целевой валюты (например: USD).\n"
        "\n"
        "- show-rates <--argument> <input> - получить курсы валют по фильтру.\n"
        "Необязательные аргументы:\n"
        "--currency <currency> - код исходной валюты (например: EUR).\n"
        "--base <currency> - код базовой валюты (например: USD).\n"
        "--top <value> - число (например: 5) верхних строк, которые хотите "
        "вывести на экран.\n"
        "\n"
        "- update-rates <--argument> <input> - обновить обменные курсы валют.\n"
        "Необязательные аргументы:\n"
        "--source <api> - один из сервисов API (coingecko или exchangerate). "
        "Если не указывать, будут задействованы оба сервиса.\n"
        "\n"
        "- exit - выход."
    )


def run_cli() -> None:
    """Главный цикл CLI."""
    print("ValutaTrade CLI — введите команду (help для справки).")

    while True:
        try:
            command_line = input("> ").strip()
            if not command_line:
                continue

            parts = shlex.split(command_line)
            command, args = parts[0], parts[1:]

            if command == "exit":
                print("Выход из программы...")
                break

            elif command == "help":
                show_help()

            elif command == "register":
                register(args)

            elif command == "login":
                login(args)

            elif command == "show-portfolio":
                show_portfolio(args)

            elif command == "buy":

                try:
                    args_dict = {}
                    i = 0
                    while i < len(args):
                        if args[i].startswith("--"):
                            key = args[i]
                            if i + 1 < len(args) and not args[i + 1].startswith("--"):
                                args_dict[key] = args[i + 1]
                                i += 2
                            else:
                                args_dict[key] = True
                                i += 1
                        else:
                            i += 1

                    currency = args_dict.get("--currency")
                    amount_str = args_dict.get("--amount")

                    if not currency:
                        print("Ошибка: укажите валюту через --currency")
                        continue

                    if not amount_str:
                        print("Ошибка: укажите количество через --amount")
                        continue

                    try:
                        amount = float(amount_str)
                    except ValueError:
                        print(
                            f"Ошибка: количество должно быть числом, получено '{amount_str}'"
                        )
                        continue

                    # Проверка логина
                    if not CURRENT_USER:
                        print("Сначала выполните login.")
                        continue

                    # Проверка валюты
                    known_currencies = ["USD", "EUR", "BTC", "ETH", "RUB"]
                    if currency.upper() not in known_currencies:
                        print(f"Неизвестная базовая валюта '{currency}'.")
                        continue

                    rate = None

                    if rate is None:
                        rate, _ = get_rate(
                            from_code=currency.upper(),
                            to_code="USD",
                            user_id=CURRENT_USER["user_id"],
                            currency_code=currency.upper(),
                            amount=amount,
                            username=CURRENT_USER["username"],
                            currency=currency.upper(),
                            rate=rate,
                        )

                    buy(
                        user_id=CURRENT_USER["user_id"],
                        currency_code=currency.upper(),
                        amount=amount,
                        username=CURRENT_USER["username"],
                        currency=currency.upper(),
                        rate=rate,
                    )

                    print(f"Покупка {amount:.2f} {currency} успешно выполнена.")

                except ValueError as e:
                    print(f"Ошибка ввода: {e}")
                except CurrencyNotFoundError as e:
                    print(str(e))
                except ApiRequestError as e:
                    print(f"Не удалось получить курс: {e}")
                except Exception as e:
                    print(f"Неожиданная ошибка: {e}")

            elif command == "sell":
                try:
                    args_dict = {args[i]: args[i + 1] for i in range(0, len(args), 2)}
                    currency = args_dict.get("--currency")
                    amount = float(args_dict.get("--amount", 0))

                    # Проверка логина
                    if not CURRENT_USER:
                        print("Сначала выполните login.")
                        continue

                    # Проверка валюты
                    known_currencies = ["USD", "EUR", "BTC", "ETH", "RUB"]
                    if currency not in known_currencies:
                        print(f"Неизвестная базовая валюта '{currency}'.")
                        continue

                    rate = None

                    if rate is None:
                        rate, _ = get_rate(
                            from_code=currency.upper(),
                            to_code="USD",
                            user_id=CURRENT_USER["user_id"],
                            currency_code=currency.upper(),
                            amount=amount,
                            username=CURRENT_USER["username"],
                            currency=currency.upper(),
                            rate=rate,
                        )

                    # Проверка кошелька реализована внутри метода sell
                    sell(
                        user_id=CURRENT_USER["user_id"],
                        currency_code=currency.upper(),
                        amount=amount,
                        username=CURRENT_USER["username"],
                        currency=currency.upper(),
                        rate=rate,
                    )
                    print(f"Продажа {amount:.4f} {currency} успешно выполнена.")

                except ValueError as e:
                    print(f"Ошибка ввода: {e}")
                except CurrencyNotFoundError as e:
                    print(str(e))
                except ApiRequestError as e:
                    print(f"Не удалось получить курс: {e}")
                except Exception as e:
                    print(f"Неожиданная ошибка: {e}")

            elif command == "get-rate":
                try:
                    args_dict = {args[i]: args[i + 1] for i in range(0, len(args), 2)}
                    from_curr = args_dict.get("--from")
                    to_curr = args_dict.get("--to")

                    if not from_curr or not to_curr:
                        print("Ошибка: укажите валюты через --from и --to.")
                        continue

                    rate, updated_at = get_rate(from_code=from_curr, to_code=to_curr)
                    print(
                        f"Курс {from_curr}→{to_curr}: {rate:.8f} "
                        f"(обновлено: {updated_at})"
                    )

                except ApiRequestError as e:
                    print(f"Ошибка API: {e}. Повторите попытку позже.")
                except Exception as e:
                    print(f"Неожиданная ошибка: {e}")

            else:
                print(f"Неизвестная команда: {command}")

        except (KeyboardInterrupt, EOFError):
            print("\nВыход из программы.")
            break


if __name__ == "__main__":
    run_cli()
