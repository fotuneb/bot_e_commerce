# Telegram Shop Bot (demo)

Небольшой демонстрационный Telegram-бот для интернет-магазина с основными возможностями: каталог товаров, карточки товаров, корзина, оформление заказа и простая админ-панель.

## Краткое содержание

- Язык: Python 3.11
- Библиотеки: aiogram (v3), aiosqlite, pytest
- Хранение данных: SQLite (асинхронно через aiosqlite)

Этот репозиторий предоставляет рабочий каркас: асинхронный слой БД, обработчики для каталога/корзины/заказа, простые админ-команды, тесты и Docker-конфигурацию.

## Контракт (коротко)

- Вход: сообщения и callback-запросы от Telegram-пользователей; команда /confirm для подтверждения заказа.
- Выход: сообщения, кнопки (inline клавиатуры), записи в SQLite (orders, carts, products, categories).
- Ошибки: логируются в `bot.log` и возвращаются пользователю дружелюбные сообщения об ошибке.

## Быстрый старт (локально)

1) Создайте виртуальное окружение и установите зависимости:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1  # -> если PowerShell блокирует, используйте python -m ...
pip install -r requirements.txt
```

Если у вас проблемы с политиками PowerShell, можно установить зависимости напрямую:

```powershell
python -m pip install -r requirements.txt
```

2) Заполните базу примерными данными (optional):

```powershell
python scripts\seed_db.py
```

3) Задайте токен и админ-ids. Лучше задать переменные окружения или создать `.env` на основе `.env.example`.

Пример `.env.example`:

```text
API_TOKEN=123456:ABCDEF
ADMIN_IDS=12345678,87654321
```

4) Запустите бота (локально):

```powershell
python -m src.main
```

После запуска бот автоматически создаст файл базы данных (по умолчанию `bot_store.db`) и необходимые таблицы.

## Архитектура проекта

- `src/main.py` — точка входа: настройка логирования, Bot, Dispatcher и подключение роутеров.
- `src/db.py` — класс `DB` с асинхронными методами для работы с SQLite: init_db, CRUD для категорий/товаров, операции с корзиной и заказами.
- `src/handlers/` — набор модулей: `catalog.py`, `cart.py`, `order.py`, `admin.py` (логика взаимодействия с пользователем и FSM для оформления заказа).
- `src/utils.py` — утилиты, например, генерация номера заказа.
- `scripts/seed_db.py` — скрипт для наполнения примерными данными.
- `tests/` — pytest тесты для базового покрытия логики.

### FSM и хранение состояния

В демо используется MemoryStorage для FSM (в `aiogram`). Для production рекомендуется RedisStorage (persistent) и перевод больших/мультимедийных данных в внешнее хранилище.

## Схема БД (детально)

Ниже — SQL-описание таблиц, используемых в проекте.

```sql
-- categories
CREATE TABLE IF NOT EXISTS categories (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL
);

-- products
CREATE TABLE IF NOT EXISTS products (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  category_id INTEGER REFERENCES categories(id),
  name TEXT NOT NULL,
  description TEXT,
  price REAL NOT NULL DEFAULT 0.0,
  photo TEXT
);

-- carts
-- items хранится как JSON: [{"product_id": 1, "qty": 2}, ...]
CREATE TABLE IF NOT EXISTS carts (
  user_id INTEGER PRIMARY KEY,
  items TEXT
);

-- orders
-- items дублируют момент покупки (JSON) для историчности
CREATE TABLE IF NOT EXISTS orders (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  order_number TEXT UNIQUE NOT NULL,
  user_id INTEGER,
  customer_name TEXT,
  phone TEXT,
  address TEXT,
  delivery_method TEXT,
  items TEXT,
  total REAL,
  status TEXT DEFAULT 'new'
);
```

Примечания:
- Поле `products.photo` может содержать URL или относительный путь. В текущем каркасе загрузка/хранение фото не реализовано.
- `carts.items` и `orders.items` — JSON-строки, сериализуются/десериализуются в коде.

## Примеры команд бота и сценарии

- /start — приветственное сообщение
- /catalog — показать категории; далее пользователь выбирает категорию и видит товары
- Кнопки в карточке товара: "В корзину" — добавляет товар
- /cart — открыть корзину; внутри кнопки: увеличить/уменьшить/удалить/очистить и Оформить заказ

Оформление заказа (FSM): бот по шагам соберёт имя, телефон, адрес и предложит подтвердить. После подтверждения создаётся запись в `orders` с уникальным `order_number`.

### Примеры админ-операций (в одном сообщении)

- Добавить категорию:

```
/add_category Новая категория
```

- Добавить товар (пример форматирования):

```
/add_product 1|Красивый стул|Комфортный деревянный стул|199.99
```

- Изменить товар:

```
/edit_product 5|Новое имя|Новое описание|149.99
```

- Удалить товар:

```
/delete_product 5
```

- Список заказов:

```
/list_orders
```

- Установить статус заказа:

```
/set_status 10 shipped
```

> Админ-команды ограничены `ADMIN_IDS` (переменная окружения). По умолчанию в проекте указан `1`.

## Тестирование

Запуск локальных unit-тестов:

```powershell
python -m pytest -q
```

Текущий набор тестов покрывает основные операции DB, утилит и простую логику корзины/админ-операций.

## Docker (быстро)

Dockerfile и `docker-compose.yml` уже добавлены. Пример быстрой сборки и запуска:

```powershell
docker compose build
docker compose up -d
```

Если хотите запустить контейнер вручную:

```powershell
docker build -t telegram-shop-bot .
docker run -e API_TOKEN="<your_token>" -e ADMIN_IDS="1" telegram-shop-bot
```

При запуске в Docker не забудьте пробросить или смонтировать каталог для хранения файла БД, если хотите сохранить данные между перезапусками.

## Отладка и Troubleshooting

- Логи пишутся в `bot.log` (rotating file handler). Проверяйте его при ошибках.
- Если бот не отвечает — проверьте `API_TOKEN` и доступность Telegram API.
- На Windows при проблемах с активацией venv используйте `python -m pip install` и `python -m src.main`.

## Ограничения и дальнейшие улучшения

- В продакшне стоит заменить MemoryStorage на RedisStorage для FSM.
- Хранение фото/медиа: использовать S3/Google Cloud Storage или том Docker-контейнера.
- Авторизация админов: сейчас по списку id; можно добавить OAuth или токены.
- Добавить интеграционные тесты для FSM и end-to-end сценариев.

## Контакты и вклад

Если хотите внести улучшения — форкните репозиторий, создайте feature-ветку и PR. Тесты в `tests/` должны проходить локально.

---

README был расширен: добавлены подробные инструкции запуска, схема БД, примеры команд и заметки по продакшену.

