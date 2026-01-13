import datetime

import requests

import valutatrade_hub.core.exceptions as exceptions
import valutatrade_hub.parser_service.config as config


class BaseApiClient:
    def __init__(self):
        self.cfg = config.ParserConfig()

    def fetch_rates(self):
        return None


class CoinGeckoClient(BaseApiClient):
    """
    Обращается к CoinGecko API, чтобы получить
    курсы валют, указанных в файлах конфигурации,
    и переводит эти данные к словарному виду.
    """

    def fetch_rates(self):
        """
        Вывод: {
            "BTC_USD: {
                "rate": <float>,
                "updated_at": <datetime>,
                "source": "CoinGecko"
            },
            ...
        }
        """
        line_ids = ""
        for currency in self.cfg.CRYPTO_CURRENCIES:
            currency_id = self.cfg.CRYPTO_ID_MAP[currency]
            line_ids += currency_id + ","
        line_ids = line_ids[:-1]
        fiat_ids = ""
        for currency in self.cfg.FIAT_CURRENCIES:
            currency_id = currency.lower()
            fiat_ids += currency_id + ","
        fiat_ids = fiat_ids[:-1]
        url = (
            self.cfg.COINGECKO_URL
            + "?ids="
            + line_ids
            + "&vs_currencies="
            + self.cfg.BASE_CURRENCY.lower()
            + ","
            + fiat_ids
        )
        try:
            crypto_info = requests.get(url).json()
            update_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            result = {}
            for key in crypto_info.keys():
                for cur, val in self.cfg.CRYPTO_ID_MAP.items():
                    if str(key) == val:
                        parsed_cur = cur
                        break
                result[parsed_cur + "_" + self.cfg.BASE_CURRENCY] = {
                    "rate": float(crypto_info[key][self.cfg.BASE_CURRENCY.lower()]),
                    "updated_at": update_time,
                    "source": "CoinGecko",
                }
                result[self.cfg.BASE_CURRENCY + "_" + parsed_cur] = {
                    "rate": float(
                        1 / float(crypto_info[key][self.cfg.BASE_CURRENCY.lower()])
                    ),
                    "updated_at": update_time,
                    "source": "CoinGecko",
                }
                for fiat_cur in self.cfg.FIAT_CURRENCIES:
                    result[parsed_cur + "_" + fiat_cur] = {
                        "rate": float(crypto_info[key][fiat_cur.lower()]),
                        "updated_at": update_time,
                        "source": "CoinGecko",
                    }
                    result[fiat_cur + "_" + parsed_cur] = {
                        "rate": float(1 / float(crypto_info[key][fiat_cur.lower()])),
                        "updated_at": update_time,
                        "source": "CoinGecko",
                    }
            return result
        except requests.RequestException:
            raise exceptions.ApiRequestError("Ошибка обращения к 'api.coingecko.com'.")


class ExchangeRateApiClient(BaseApiClient):
    """
    Обращается к ExchangeRate API, чтобы получить
    курсы валют, указанных в файлах конфигурации,
    и переводит эти данные к словарному виду.
    """

    def fetch_rates(self):
        """
        Вывод: {
            "EUR_USD: {
                "rate": <float>,
                "updated_at": <datetime>,
                "source": "ExchangeRate-API"
                },
            ...
        }
        """
        check_currencies = [self.cfg.BASE_CURRENCY] + list(self.cfg.FIAT_CURRENCIES)
        base_url = (
            self.cfg.EXCHANGERATE_API_URL
            + "/"
            + self.cfg.EXCHANGERATE_API_KEY
            + "/latest/"
        )
        try:
            for base_currency in check_currencies:
                url = base_url + base_currency
                fiat_info = requests.get(url).json()
                if fiat_info["result"] != "success":
                    raise exceptions.ApiRequestError(
                        f"Ошибка обращения к "
                        f"'v6.exchangerate-api.com': {fiat_info["result"]}"
                    )
                update_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                result = {}
                for currency in check_currencies:
                    result[currency + "_" + base_currency] = {
                        "rate": float(
                            1 / float(fiat_info["conversion_rates"][currency])
                        ),
                        "updated_at": update_time,
                        "source": "ExchangeRate-API",
                    }
                    result[base_currency + "_" + currency] = {
                        "rate": float(fiat_info["conversion_rates"][currency]),
                        "updated_at": update_time,
                        "source": "ExchangeRate-API",
                    }
            return result
        except requests.RequestException:
            raise exceptions.ApiRequestError(
                "Ошибка обращения к 'v6.exchangerate-api.com'."
            )
