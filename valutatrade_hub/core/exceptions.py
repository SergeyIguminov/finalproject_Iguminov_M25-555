class CurrencyNotFoundError(Exception):
    """
    Ошибка, если код валюты не найден в реестре.
    """

    def __init__(self, code: str):
        super().__init__(f"Неизвестная валюта '{code}'")
        self.code = code


class InsufficientFundsError(Exception):
    """
    Ошибка при попытке снять средства, если их недостаточно на счёте.
    """

    def __init__(self, available: float, required: float, code: str):
        message = (
            f"Недостаточно средств: доступно {available:.4f} {code}, "
            f"требуется {required:.4f} {code}"
        )
        super().__init__(message)
        self.available = available
        self.required = required
        self.code = code


class ApiRequestError(Exception):
    """
    Ошибке обращения к внешнему API.
    """

    def __init__(self, reason: str):
        super().__init__(f"Ошибка при обращении к внешнему API: {reason}")
        self.reason = reason
