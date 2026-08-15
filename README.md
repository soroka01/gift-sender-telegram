# 🎁 Telegram Gift Sender

> Приватная Telegram-панель на aiogram и Telethon для отправки обычных и снятых с витрины безлимитных подарков с пользовательского аккаунта.

🌐 **Язык:** [Русский](README.md) · [English](README_EN.md)

![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![Telethon](https://img.shields.io/badge/Telethon-user_session-0088CC?logo=telegram&logoColor=white)
![aiogram](https://img.shields.io/badge/aiogram-Telegram_bot-26A5E4?logo=telegram&logoColor=white)
![MIT License](https://img.shields.io/badge/License-MIT-2EA44F.svg)

## ✨ Обзор

Telegram Gift Sender использует отдельного Bot API-бота как приватную панель управления, а авторизованную пользовательскую Telethon session — для оплаты и отправки Telegram Gifts. Перед списанием Stars бот показывает получателя, подарок, стоимость, текст, анонимность и настройку улучшения.

Помимо актуального каталога Telegram, панель содержит известные безлимитные подарки-мишки за 50 Stars, которые уже сняты с витрины, но всё ещё принимаются Telegram API. У каждой такой позиции указана дата выхода, а непосредственно перед оплатой выполняется `CheckCanSendGift`.

> [!WARNING]
> Отправка выполняется с баланса Stars пользовательского аккаунта. Укажите только собственные Telegram ID в `ADMIN_IDS`, защищайте session-файл как пароль и внимательно проверяйте итоговый экран перед нажатием кнопки отправки.

> [!NOTE]
> Это неофициальный проект, не связанный с Telegram. Доступность снятых подарков определяется сервером Telegram и может измениться без обновления скрипта.

## 🚀 Возможности

- актуальные Telegram Gifts из `payments.GetStarGifts`;
- девять снятых с витрины безлимитных мишек за 50 Stars;
- дата выхода снятого подарка прямо на кнопке и экране подтверждения;
- проверка возможности отправки через `payments.CheckCanSendGift`;
- переключатель видимости имени отправителя: видно или анонимно;
- отдельное разрешение на последующее улучшение подарка получателем;
- сообщение длиной до 255 символов;
- сохранение кастомных Telegram Premium Emoji через `MessageEntityCustomEmoji`;
- подробный итог после отправки: получатель, цена, дата, анонимность, текст и gift ID;
- admin-only доступ ко всем командам и кнопкам;
- rotating log без текста сообщений и credentials;
- Windows launchers для установки, авторизации и запуска.

## 🏗️ Как это работает

```text
управляющий Bot API-бот
          │
          ├── /gift @username
          ├── выбор подарка и параметров
          └── подтверждение оплаты
          │
          ▼
авторизованная Telethon session
          ├── GetStarGifts + локальный список снятых мишек
          ├── CheckCanSendGift
          ├── GetPaymentForm
          └── SendStarsForm
          │
          ▼
получатель получает подарок
```

Bot token не может оплачивать подарки. Bot API используется только для интерфейса, а Stars списываются с авторизованного пользовательского аккаунта через MTProto.

## 📋 Требования

- Python 3.10 или новее;
- Windows для готовых `.bat`-launcher'ов;
- пользовательский Telegram-аккаунт с достаточным количеством Stars;
- `api_id` и `api_hash` из [Telegram API development tools](https://my.telegram.org);
- Telegram bot token от [@BotFather](https://t.me/BotFather);
- числовой Telegram ID каждого администратора.

Основные зависимости:

| Пакет | Назначение |
| --- | --- |
| `telethon` | User session, каталог подарков и оплата через MTProto |
| `aiogram` | Приватная Bot API-панель и inline keyboard |

## ⚙️ Быстрый запуск

### 1. Клонируйте репозиторий

```powershell
git clone https://github.com/soroka01/gift-sender-telegram.git
cd gift-sender-telegram
```

### 2. Создайте конфигурацию

```powershell
Copy-Item config.example.py config.py
```

Откройте `config.py` и замените placeholders своими значениями.

### 3. Авторизуйте пользовательский аккаунт

```bat
login.bat
```

Telethon запросит номер телефона, код из официального чата **Telegram** и пароль 2FA, если он включён. После успешного входа рядом со скриптом появится `user_account.session`.

### 4. Запустите панель

```bat
start.bat
```

Launcher создаёт локальную `.venv` и устанавливает зависимости из `requirements.txt`. Затем отправьте управляющему боту:

```text
/gift @username
```

Если `config.py` отсутствует, `start.bat` или `login.bat` создаст его из примера и остановится, чтобы credentials не вводились в неправильный файл.

### Ручной запуск

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item config.example.py config.py
.\.venv\Scripts\python.exe login.py
.\.venv\Scripts\python.exe main.py
```

На Linux и macOS можно использовать те же Python-файлы без `.bat`-launcher'ов:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp config.example.py config.py
python login.py
python main.py
```

## 🔧 Конфигурация

```python
BOT_TOKEN = "PUT_TELEGRAM_BOT_TOKEN_HERE"

API_ID = 0
API_HASH = "PUT_TELEGRAM_API_HASH_HERE"
USER_SESSION = "user_account"

ADMIN_IDS = {123456789}

DEFAULT_HIDE_NAME = True
DEFAULT_INCLUDE_UPGRADE = False
GIFT_MESSAGE = ""
```

| Поле | Назначение |
| --- | --- |
| `BOT_TOKEN` | Token управляющего бота от BotFather |
| `API_ID` | ID Telegram API application |
| `API_HASH` | Hash Telegram API application |
| `USER_SESSION` | Имя Telethon session без расширения `.session` |
| `ADMIN_IDS` | Множество Telegram user ID с доступом к панели |
| `DEFAULT_HIDE_NAME` | Начальное состояние анонимной отправки |
| `DEFAULT_INCLUDE_UPGRADE` | Разрешать ли получателю улучшение по умолчанию |
| `GIFT_MESSAGE` | Необязательный обычный текст по умолчанию |

`GIFT_MESSAGE` из конфигурации не содержит Telegram entities. Чтобы прикрепить кастомные Premium Emoji, введите сообщение через интерфейс бота.

## 🤖 Сценарий отправки

1. Отправьте `/gift @username`.
2. Выберите подарок. У снятых мишек вместо остатка указана дата выхода.
3. Проверьте цену и переключите анонимность или разрешение улучшения.
4. При необходимости добавьте текст и Premium Emoji.
5. Нажмите «Отправить» только после проверки итоговых параметров.

Один экран последовательно меняется между вводом текста, подтверждением, отправкой и подробным итогом. Stars списываются только после последней кнопки.

## 🧸 Снятые безлимитные подарки

Встроенный список содержит сезонных и временных мишек, выпущенных с 31 декабря 2025 года по 13 августа 2026 года. Они отсутствуют в текущем `GetStarGifts`, поэтому хранятся по техническому ID и дате первого появления.

Перед каждой отправкой сервер Telegram дополнительно проверяет ID. Если Telegram отключит конкретный подарок, панель покажет отказ до запроса платёжной формы.

## 📝 Логи

Технический журнал записывается в `gift_sender.log` рядом с `main.py` и одновременно выводится в консоль.

| Параметр | Значение |
| --- | --- |
| Максимальный размер | 5 МБ |
| Архивы | `gift_sender.log.1` — `gift_sender.log.3` |
| Кодировка | UTF-8 |
| События | каталог, выбор, параметры, отправка, результат, ошибки и длительность |

Лог содержит Telegram ID администратора, username получателя и gift ID. Текст подарка, bot token, API hash, session key и платёжная ссылка в него не записываются.

## 🔐 Безопасность и приватность

- Никогда не коммитьте `config.py`, `*.session`, `*.session-journal`, `.venv` и `*.log`.
- Telethon session даёт доступ к пользовательскому аккаунту и требует защиты на уровне пароля.
- Не запускайте несколько процессов с одним session-файлом: SQLite вернёт `database is locked`.
- Не оставляйте `ADMIN_IDS` пустым и не добавляйте туда незнакомые ID.
- Проверяйте username, цену и анонимность перед подтверждением.
- После утечки bot token или API credentials немедленно отзовите их.
- Используйте проект только для собственного аккаунта и с соблюдением правил Telegram.

## ⚠️ Ограничения

- Telegram может в любой момент отключить отправку снятого подарка.
- Список снятых мишек обновляется вручную при появлении новых ID.
- Возможность улучшения зависит от данных конкретного подарка и Telegram API.
- Payment verification может потребовать отдельного перехода по ссылке; скрипт не повторяет списание автоматически.
- Полноценный end-to-end тест требует реального аккаунта, Stars и получателя.

## 🧪 Проверка и диагностика

Синтаксис можно проверить без Telegram credentials:

```powershell
python -m py_compile main.py login.py config.example.py
```

| Симптом | Что проверить |
| --- | --- |
| `database is locked` | Остановите второй процесс с той же Telethon session |
| Бот отвечает «Нет доступа» | Добавьте свой числовой user ID в `ADMIN_IDS` |
| Подарок недоступен | Telegram отключил ID или ограничил получателя |
| Premium Emoji стал обычным | Добавляйте текст через интерфейс после обновления и перезапуска бота |
| Платёж не завершён | Откройте verification URL и начните отправку заново |
| Непонятная ошибка | Изучите `gift_sender.log` |

## 📄 Лицензия

Проект распространяется по [лицензии MIT](LICENSE).

---

🎁 Проверяйте получателя и параметры — Stars списываются с реального пользовательского аккаунта.
