### Сервис ValutaTrade Hub
Проект реализует CLI-приложение для торговли фиатными и криптовалютными активами.
Данные курсов обновляются из публичных API CoinGecko и ExchangeRate-API.
Пользователи могут регистрироваться, просматривать курсы, покупать и продавать валюты, а также управлять своим портфелем.

Поддерживаемые валюты: USD, EUR, RUB, BTC, ETH.

## Требования
Python 3.13+

Poetry 1.8.0+

Ruff (для линтинга)

Requests (для работы с API)

## 1. Установка
	# Способ 1 С использованием Make (Linux/macOS)
	make install

	# Способ 2 С использованием Poetry (Windows)
	poetry install

## 2. Запуск
	#Способ 1
	make project

	#Способ 2
	poetry run project

## 3. Список команд
# Регистрация и авторизация
register --username <имя> --password <пароль>

Регистрация нового пользователя. Пароль должен быть не короче 4 символов.

login --username <имя> --password <пароль>
Вход в систему.

# Управление портфелем
show-portfolio [--base <валюта>]
Показать баланс по всем кошелькам.
Пример: show-portfolio --base EUR — показать портфель в евро.

buy --currency <код> --amount <число>
Покупка валюты.
Пример: buy --currency EUR --amount 100

sell --currency <код> --amount <число>
Продажа валюты.
Пример: sell --currency BTC --amount 0.5

# Курсы валют
get-rate --from <валюта> --to <валюта>
Получить курс обмена.
Пример: get-rate --from USD --to RUB

show-rates [--currency <код>] [--base <код>] [--top <число>]
Показать курсы с фильтрацией.
Примеры:
show-rates — все курсы
show-rates --currency USD — только курсы с USD
show-rates --top 5 — топ-5 курсов
show-rates --base EUR — курсы относительно EUR

update-rates [--source coingecko|exchangerate]
Обновить курсы из API.
Пример: update-rates --source coingecko

# Вспомогательные команды
help — показать справку по всем командам
exit — выйти из приложения

## Демонастрация приложения (GIF)
![ValutaTrade Hub Demo](https://github.com/SergeyIguminov/finalproject_Iguminov_M25-555/releases/download/gif_for_demonstration/finalproject.gif)]
