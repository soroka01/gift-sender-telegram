# 🎁 Telegram Gift Sender

> A private aiogram and Telethon control panel for sending current and removed unlimited Telegram gifts from a user account.

🌐 **Язык / Language:** [Русский](README.md) · [English](README_EN.md)

![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![Telethon](https://img.shields.io/badge/Telethon-user_session-0088CC?logo=telegram&logoColor=white)
![aiogram](https://img.shields.io/badge/aiogram-Telegram_bot-26A5E4?logo=telegram&logoColor=white)
![MIT License](https://img.shields.io/badge/License-MIT-2EA44F.svg)

## 📌 Overview

Telegram Gift Sender uses a separate Bot API bot as a private control panel and an authorized Telethon user session to pay for and send Telegram Gifts. Before any Stars are charged, the bot shows the recipient, gift, price, message, sender visibility, and upgrade setting.

In addition to Telegram's current catalog, the panel includes known unlimited 50-Star gifts that were removed from the storefront but are still accepted by the Telegram API. Each shows its release date, and `CheckCanSendGift` runs before payment.

> [!WARNING]
> Gifts are paid from the user account's real Stars balance. Add only your own Telegram IDs to `ADMIN_IDS`, protect the session file like a password, and review the final confirmation before sending.

> [!NOTE]
> This is an unofficial project and is not affiliated with Telegram. Server-side availability of removed gifts can change without a script update.

## ✨ Features

- current Telegram Gifts from `payments.GetStarGifts`;
- ten removed unlimited 50-Star gifts with release dates on buttons and confirmation screens;
- custom gift names and descriptions from the public `gift_descriptions.json`;
- sendability checks through `payments.CheckCanSendGift`;
- toggles for anonymity and recipient-upgrade permission;
- messages up to 255 characters with custom Premium Emoji preserved (`MessageEntityCustomEmoji`);
- detailed final receipt: recipient, price, date, anonymity, text, and gift ID;
- administrator-only commands and buttons;
- rotating logs without message contents or credentials;
- Windows launchers for setup, authorization, and startup.

## 🏗️ How it works

```text
Bot API control panel
   ├── /gift @username
   ├── gift and option selection
   └── final payment confirmation
          │
          ▼
authorized Telethon user session
   ├── GetStarGifts + local removed-gift list
   ├── CheckCanSendGift
   ├── GetPaymentForm
   └── SendStarsForm
          │
          ▼
recipient receives the gift
```

A bot token cannot pay for gifts: Bot API is only the interface, while Stars are charged from the user account over MTProto. A single message is edited through text input, confirmation, sending, and the final receipt; Stars are charged only after the last button press.

## 🚀 Quick start

### Requirements

- Python 3.10 or newer;
- Windows for the included `.bat` launchers (run manually on Linux/macOS);
- a Telegram user account with enough Stars;
- an `api_id` and `api_hash` from [Telegram API development tools](https://my.telegram.org);
- a bot token from [@BotFather](https://t.me/BotFather);
- the numeric Telegram ID of every administrator.

Dependencies (`requirements.txt`): `aiogram>=3.28.0,<4.0`, `Telethon>=1.43.2,<2.0`.

### Installation

```powershell
git clone https://github.com/soroka01/gift-sender-telegram.git
cd gift-sender-telegram
```

### Configuration

```powershell
Copy-Item config.example.py config.py
```

Open `config.py` and replace the placeholders with your own values (see the "Configuration" section below). If `config.py` is missing, `start.bat` and `login.bat` create it from the example and stop, so credentials are never entered into the wrong file.

### Run

1. Authorize the user account — Telethon asks for the phone number, the code from the official **Telegram** chat, and the 2FA password (if enabled); `user_account.session` appears next to the script:

   ```bat
   login.bat
   ```

2. Start the panel — the launcher creates `.venv` and installs dependencies:

   ```bat
   start.bat
   ```

3. Send `/gift @username` to the control bot.

Manual startup, Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item config.example.py config.py
.\.venv\Scripts\python.exe login.py
.\.venv\Scripts\python.exe main.py
```

Linux and macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp config.example.py config.py
python login.py
python main.py
```

## ⚙️ Configuration

Settings live in `config.py` (a secret file that is never committed):

| Variable | Default | Description |
| --- | --- | --- |
| `BOT_TOKEN` | `"PUT_TELEGRAM_BOT_TOKEN_HERE"` | Control bot token from BotFather |
| `API_ID` | `0` | Telegram API application ID |
| `API_HASH` | `"PUT_TELEGRAM_API_HASH_HERE"` | Telegram API application hash |
| `USER_SESSION` | `"user_account"` | Telethon session name without `.session` |
| `ADMIN_IDS` | `{123456789}` | Telegram user IDs allowed to use the panel |
| `DEFAULT_HIDE_NAME` | `True` | Initial anonymous-sending state |
| `DEFAULT_INCLUDE_UPGRADE` | `False` | Whether recipient upgrades are allowed by default |
| `GIFT_MESSAGE` | `""` | Optional default plain-text message |

Defaults are taken from `config.example.py`. `GIFT_MESSAGE` has no Telegram entities: enter the message through the bot interface when Premium Emoji are needed.

| Command / control | Action |
| --- | --- |
| `/gift @username` | Open gift selection for the recipient |
| Gift selection button | Removed gifts show a release date instead of remaining supply |
| Toggles | Anonymity and upgrade permission |
| "Send" | Final confirmation; Stars are charged after it |

### Removed unlimited gifts

The built-in list contains seasonal and temporary gifts released between 2025-12-31 and 2026-08-13. They are absent from the current `GetStarGifts`, so their IDs and first-seen dates are stored locally. Telegram validates each ID again before payment: if a gift is disabled, the panel reports the refusal before requesting a payment form.

| Gift ID | Release date | Built-in name |
| --- | --- | --- |
| `5956217000635139069` | 2025-12-31 | New Year bear |
| `5800655655995968830` | 2026-02-14 | Valentine's Day bear |
| `5801108895304779062` | 2026-02-14 | “I LOVE U” heart |
| `5866352046986232958` | 2026-03-08 | International Women's Day bear |
| `5893356958802511476` | 2026-03-17 | Saint Patrick's Day bear |
| `5935895822435615975` | 2026-04-01 | April Fools' Day bear |
| `5969796561943660080` | 2026-04-12 | Bear |
| `6026193266406327981` | 2026-05-01 | Bear |
| `5974210632977745012` | 2026-07-20 | Football bear |
| `6046178578163303744` | 2026-08-13 | Bear |

### Custom gift labels

Edit the public [`gift_descriptions.json`](gift_descriptions.json). Gifts are ordered newest to oldest and labeled with the Yekaterinburg release time (`UTC+5`).

```json
{
  "released_at": "13.08.2026 00:37",
  "name": "Bear with a bomb",
  "gift_id": "6046178578163303744",
  "description": "wearing dark glasses and a red scarf"
}
```

- `name` is the label on the selection button;
- `description` is optional and shown on the text-input screen, confirmation, and final receipt;
- each field is limited to 120 characters and whitespace is normalized;
- do not change `released_at` and `gift_id`;
- the file is reloaded on every `/gift`, so no restart is needed;
- the JSON is separate from the secret `config.py`, so it can be published in the repository.

### Logs

The log is written to `gift_sender.log` next to `main.py` and printed to the console.

| Setting | Value |
| --- | --- |
| Maximum size | 5 MB |
| Archives | `gift_sender.log.1` through `gift_sender.log.3` |
| Encoding | UTF-8 |
| Events | catalog, selection, options, send attempt, result, errors, and duration |

## 🗂️ Project structure

```text
gift_sender/
├── main.py                 # Bot API panel and gift sending
├── login.py                # Telethon session authorization
├── config.example.py       # Configuration template
├── config.py               # Your configuration (not committed)
├── config_compat.py        # Config value reader (tolerates a stray trailing comma)
├── gift_descriptions.json  # Public names and descriptions of removed gifts
├── requirements.txt        # Python dependencies
├── start.bat               # Install dependencies and start the panel (Windows)
├── login.bat               # Account authorization (Windows)
└── LICENSE                 # MIT license
```

## 🔒 Security & privacy

- Never commit `config.py`, `*.session`, `*.session-journal`, `.venv`, or `*.log` (all are in `.gitignore`).
- A Telethon session grants access to the account — protect it like a password.
- Do not run multiple processes with the same session file; SQLite will report `database is locked`.
- Never leave `ADMIN_IDS` empty or add unknown IDs.
- Verify the username, price, and anonymity setting before confirmation.
- Revoke bot tokens or API credentials immediately after a leak.
- The log contains the administrator Telegram ID, recipient username, and gift ID; it never stores message contents, bot tokens, API hashes, session keys, or payment verification URLs.
- Use the project only with your own account and in accordance with Telegram's rules.

## ⚠️ Limitations

- Telegram can disable a removed gift at any time.
- Removed gift IDs are updated manually when new gifts appear.
- Upgrade availability depends on the gift and the current Telegram API response.
- Payment verification may require opening a separate URL; the script never retries a charge automatically.
- A complete end-to-end test requires a real account, Stars, and a recipient.

Syntax check without credentials: `python -m py_compile main.py login.py config.example.py`

| Symptom | What to check |
| --- | --- |
| `database is locked` | Stop the second process using the same Telethon session |
| The bot replies with access denied | Add your numeric user ID to `ADMIN_IDS` |
| A gift is unavailable | Telegram disabled the ID or restricted the recipient |
| Premium Emoji became plain | Enter the message through the bot interface after updating and restarting |
| Payment did not finish | Open the verification URL and start the send flow again |
| Unknown failure | Inspect `gift_sender.log` |

## 📄 License

This project is distributed under the [MIT License](LICENSE).

## 💬 Support

If this project helped you, give [soroka01/gift-sender-telegram](https://github.com/soroka01/gift-sender-telegram) a ⭐ or fork it and adapt it to your needs.

---

with love ❤️
