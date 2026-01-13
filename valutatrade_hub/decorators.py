import datetime
import functools
from typing import Any, Callable

from valutatrade_hub.logging_config import setup_logger

logger = setup_logger()


def log_action(action_name: str, verbose: bool = False):
    """
    Декоратор для логирования операций.
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:

            func_name = func.__name__

            # Для get_rate - особый случай
            if func_name == "get_rate":
                params = {
                    "username": "rate_service",
                    "currency": f"{args[0] if len(args) > 0 else 'N/A'}_to_{args[1] if len(args) > 1 else 'N/A'}",
                    "amount": "N/A",
                    "rate": "N/A",
                    "base": "N/A",
                }
            else:
                params = _extract_params(args, kwargs)

            timestamp = datetime.datetime.now().isoformat()

            try:
                result = func(*args, **kwargs)

                message = _format_message(action_name.upper(), params, "OK")
                if verbose:
                    message += f" context={kwargs}"

                logger.info(f"{timestamp} {message}")
                return result

            except Exception as e:
                message = _format_message(action_name.upper(), params, "ERROR", e)
                logger.error(f"{timestamp} {message}")
                raise

        return wrapper

    return decorator


# decorators.py
def _extract_params(args: tuple, kwargs: dict) -> dict:
    """
    Извлекает параметры для логирования из аргументов.
    """
    username = kwargs.get("username")
    user_id = kwargs.get("user_id")

    if username is None and user_id is None and args:
        first_arg = args[0]
        if hasattr(first_arg, "username"):
            username = getattr(first_arg, "username", None)
        elif hasattr(first_arg, "user_id"):
            user_id = getattr(first_arg, "user_id", None)
        elif isinstance(first_arg, (int, str)):
            user_id = str(first_arg)

    return {
        "username": username or f"user_id:{user_id}" if user_id else "N/A",
        "currency": kwargs.get("currency") or kwargs.get("currency_code"),
        "amount": kwargs.get("amount"),
        "rate": kwargs.get("rate"),
        "base": kwargs.get("base", "USD"),
    }


def _format_message(
    action: str, params: dict, result: str, error: Exception = None
) -> str:
    """
    Форматирует сообщение для лога.
    """
    message = (
        f"{action} user='{params['username']}' "
        f"currency='{params['currency'] or 'N/A'}' "
        f"amount={params['amount'] or 'N/A'} "
        f"rate={params['rate'] or 'N/A'} "
        f"base='{params['base']}' "
        f"result={result}"
    )

    if error:
        message += f" error_type='{type(error).__name__}' error_message='{str(error)}'"

    return message
