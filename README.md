# 🎁 Telegram Gift Sender

> Приватная Telegram-панель на aiogram и Telethon для отправки обычных и снятых с витрины безлимитных подарков с пользовательского аккаунта.

🌐 **Язык / Language:** [Русский](README.md) · [English](README_EN.md)

![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![Telethon](https://img.shields.io/badge/Telethon-user_session-0088CC?logo=telegram&logoColor=white)
![aiogram](https://img.shields.io/badge/aiogram-Telegram_bot-26A5E4?logo=telegram&logoColor=white)
![MIT License](https://img.shields.io/badge/License-MIT-2EA44F.svg)

## 📌 Overview

Telegram Gift Sender использует отдельного Bot API-бота как приватную панель управления, а авторизованную пользовательскую Telethon session — для оплаты и отправки Telegram Gifts. Перед списанием Stars бот показывает получателя, подарок, стоимость, текст, анонимность и настройку улучшения.

Помимо актуального каталога Telegram, панель содержит известные безлимитные подарки за 50 Stars, которые сняты с витрины, но всё ещё принимаются Telegram API. Для каждого указана дата выхода, а перед оплатой выполняется `CheckCanSendGift`.

> [!WARNING]
> Отправка выполняется с баланса Stars пользовательского аккаунта. Укажите только собственные Telegram ID в `ADMIN_IDS`, защищайте session-файл как пароль и внимательно проверяйте итоговый экран перед отправкой.

> [!NOTE]
> Это неофициальный проект, не связанный с Telegram. Доступность снятых подарков определяется сервером Telegram и может измениться без обновления скрипта.

## ✨ Features

- актуальные Telegram Gifts из `payments.GetStarGifts`;
- десять снятых с витрины безлимитных подарков за 50 Stars с датой выхода на кнопке и экране подтверждения;
- собственные названия и описания подарков из публичного `gift_descriptions.json`;
- проверка возможности отправки через `payments.CheckCanSendGift`;
- переключатели анонимности и разрешения улучшения подарка получателем;
- сообщение до 255 символов с сохранением кастомных Premium Emoji (`MessageEntityCustomEmoji`);
- подробный итог: получатель, цена, дата, анонимность, текст и gift ID;
- доступ к командам и кнопкам только для админов;
- rotating log без текста сообщений и credentials;
- Windows-launcher'ы для установки, авторизации и запуска.

## 🏗️ How it works

```text
управляющий Bot API-бот
   ├── /gift @username
   ├── выбор подарка и параметров
   └── подтверждение оплаты
          │
          ▼
авторизованная Telethon session
   ├── GetStarGifts + локальный список снятых подарков
   ├── CheckCanSendGift
   ├── GetPaymentForm
   └── SendStarsForm
          │
          ▼
получатель получает подарок
```

Bot token не может оплачивать подарки: Bot API используется только как интерфейс, а Stars списываются с пользовательского аккаунта через MTProto. Один экран последовательно меняется между вводом текста, подтверждением, отправкой и итогом; Stars списываются только после последней кнопки.

## 🚀 Quick start

### Requirements

- Python 3.10 или новее;
- Windows для готовых `.bat`-launcher'ов (на Linux/macOS — запуск вручную);
- пользовательский Telegram-аккаунт с достаточным количеством Stars;
- `api_id` и `api_hash` из [Telegram API development tools](https://my.telegram.org);
- bot token от [@BotFather](https://t.me/BotFather);
- числовой Telegram ID каждого администратора.

Зависимости (`requirements.txt`): `aiogram>=3.28.0,<4.0`, `Telethon>=1.43.2,<2.0`.

### Installation

```powershell
git clone https://github.com/soroka01/gift-sender-telegram.git
cd gift-sender-telegram
```

### Configuration

```powershell
Copy-Item config.example.py config.py
```

Откройте `config.py` и замените placeholders своими значениями (см. раздел «Configuration» ниже). Если `config.py` отсутствует, `start.bat` и `login.bat` создадут его из примера и остановятся, чтобы credentials не вводились в неправильный файл.

### Run

1. Авторизуйте пользовательский аккаунт — Telethon запросит номер телефона, код из чата **Telegram** и пароль 2FA (если включён); рядом появится `user_account.session`:

   ```bat
   login.bat
   ```

2. Запустите панель — launcher создаёт `.venv` и устанавливает зависимости:

   ```bat
   start.bat
   ```

3. Отправьте управляющему боту `/gift @username`.

Ручной запуск, Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item config.example.py config.py
.\.venv\Scripts\python.exe login.py
.\.venv\Scripts\python.exe main.py
```

Linux и macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp config.example.py config.py
python login.py
python main.py
```

## ⚙️ Configuration

Настройки хранятся в `config.py` (секретный файл, не коммитится):

| Variable | Default | Description |
| --- | --- | --- |
| `BOT_TOKEN` | `"PUT_TELEGRAM_BOT_TOKEN_HERE"` | Token управляющего бота от BotFather |
| `API_ID` | `0` | ID Telegram API application |
| `API_HASH` | `"PUT_TELEGRAM_API_HASH_HERE"` | Hash Telegram API application |
| `USER_SESSION` | `"user_account"` | Имя Telethon session без расширения `.session` |
| `ADMIN_IDS` | `{123456789}` | Множество Telegram user ID с доступом к панели |
| `DEFAULT_HIDE_NAME` | `True` | Начальное состояние анонимной отправки |
| `DEFAULT_INCLUDE_UPGRADE` | `False` | Разрешать ли получателю улучшение по умолчанию |
| `GIFT_MESSAGE` | `""` | Необязательный обычный текст по умолчанию |

Значения в таблице — из `config.example.py`. `GIFT_MESSAGE` не содержит Telegram entities: чтобы прикрепить Premium Emoji, введите сообщение через интерфейс бота.

| Команда / элемент | Действие |
| --- | --- |
| `/gift @username` | Открыть выбор подарка для получателя |
| Кнопка выбора подарка | У снятых подарков вместо остатка показана дата выхода |
| Переключатели | Анонимность и разрешение улучшения |
| «Отправить» | Финальное подтверждение, после него списываются Stars |

### Снятые безлимитные подарки

Встроенный список содержит сезонные и временные подарки, выпущенные с 31.12.2025 по 13.08.2026. Они отсутствуют в текущем `GetStarGifts`, поэтому хранятся по ID и дате первого появления. Перед отправкой Telegram дополнительно проверяет ID: если подарок отключён, панель покажет отказ до запроса платёжной формы.

| Gift ID | Дата выхода | Встроенное название |
| --- | --- | --- |
| `5956217000635139069` | 31.12.2025 | Новогодний мишка |
| `5800655655995968830` | 14.02.2026 | Мишка на 14 февраля |
| `5801108895304779062` | 14.02.2026 | Сердечко «I LOVE U» |
| `5866352046986232958` | 08.03.2026 | Мишка на 8 марта |
| `5893356958802511476` | 17.03.2026 | Мишка на День святого Патрика |
| `5935895822435615975` | 01.04.2026 | Мишка на 1 апреля |
| `5969796561943660080` | 12.04.2026 | Мишка |
| `6026193266406327981` | 01.05.2026 | Мишка |
| `5974210632977745012` | 20.07.2026 | Мишка-футболист |
| `6046178578163303744` | 13.08.2026 | Мишка |

### Свои обозначения подарков

Отредактируйте публичный [`gift_descriptions.json`](gift_descriptions.json). Подарки идут от нового к старому и подписаны временем выхода по Екатеринбургу (`UTC+5`).

```json
{
  "released_at": "13.08.2026 00:37",
  "name": "Мишка с бомбой",
  "gift_id": "6046178578163303744",
  "description": "в тёмных очках и с красным шарфом"
}
```

- `name` — название на кнопке выбора;
- `description` — необязательное описание, показывается на экране ввода текста, подтверждении и в итоге;
- каждое поле ограничено 120 символами, пробелы нормализуются;
- `released_at` и `gift_id` менять не нужно;
- файл перечитывается при каждом `/gift`, перезапуск не нужен;
- JSON отделён от секретного `config.py`, поэтому его можно публиковать в репозитории.

### Логи

Журнал пишется в `gift_sender.log` рядом с `main.py` и дублируется в консоль.

| Параметр | Значение |
| --- | --- |
| Максимальный размер | 5 МБ |
| Архивы | `gift_sender.log.1` — `gift_sender.log.3` |
| Кодировка | UTF-8 |
| События | каталог, выбор, параметры, отправка, результат, ошибки и длительность |

## 🗂️ Project structure

```text
gift_sender/
├── main.py                 # Bot API-панель и отправка подарков
├── login.py                # Авторизация Telethon session
├── config.example.py       # Шаблон конфигурации
├── config.py               # Ваша конфигурация (не коммитится)
├── config_compat.py        # Чтение значений конфига (терпит случайную запятую)
├── gift_descriptions.json  # Публичные названия и описания снятых подарков
├── requirements.txt        # Зависимости Python
├── start.bat               # Установка зависимостей и запуск панели (Windows)
├── login.bat               # Авторизация аккаунта (Windows)
└── LICENSE                 # Лицензия MIT
```

## 🔒 Security & privacy

- Никогда не коммитьте `config.py`, `*.session`, `*.session-journal`, `.venv` и `*.log` (всё это есть в `.gitignore`).
- Telethon session даёт доступ к аккаунту — защищайте её как пароль.
- Не запускайте несколько процессов с одним session-файлом: SQLite вернёт `database is locked`.
- Не оставляйте `ADMIN_IDS` пустым и не добавляйте незнакомые ID.
- Проверяйте username, цену и анонимность перед подтверждением.
- После утечки bot token или API credentials немедленно отзовите их.
- Лог содержит Telegram ID администратора, username получателя и gift ID; текст подарка, bot token, API hash, session key и платёжная ссылка в него не записываются.
- Используйте проект только для собственного аккаунта и с соблюдением правил Telegram.

## ⚠️ Limitations

- Telegram может в любой момент отключить отправку снятого подарка.
- Список снятых подарков обновляется вручную при появлении новых ID.
- Возможность улучшения зависит от данных подарка и Telegram API.
- Payment verification может потребовать отдельного перехода по ссылке; скрипт не повторяет списание автоматически.
- Полноценный end-to-end тест требует реального аккаунта, Stars и получателя.

Проверка синтаксиса без credentials: `python -m py_compile main.py login.py config.example.py`

| Симптом | Что проверить |
| --- | --- |
| `database is locked` | Остановите второй процесс с той же Telethon session |
| Бот отвечает «Нет доступа» | Добавьте свой числовой user ID в `ADMIN_IDS` |
| Подарок недоступен | Telegram отключил ID или ограничил получателя |
| Premium Emoji стал обычным | Добавляйте текст через интерфейс бота после обновления и перезапуска |
| Платёж не завершён | Откройте verification URL и начните отправку заново |
| Непонятная ошибка | Изучите `gift_sender.log` |

## 📄 License

Проект распространяется по [лицензии MIT](LICENSE).

## 💬 Support

Если проект оказался полезным, поставьте ⭐ репозиторию [soroka01/gift-sender-telegram](https://github.com/soroka01/gift-sender-telegram) или сделайте fork и доработайте под себя.

---

with love ❤️
