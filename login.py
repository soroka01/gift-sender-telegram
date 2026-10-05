import asyncio

from telethon import TelegramClient

import config as user_config
from config_compat import config_value


async def main() -> None:
    api_id = config_value(user_config, "API_ID", 0)
    api_hash = config_value(user_config, "API_HASH", "")
    if not api_id or not api_hash:
        raise RuntimeError("Fill API_ID and API_HASH in config.py before login.")
    session = config_value(user_config, "USER_SESSION", "user_account") or "user_account"
    phone = config_value(user_config, "PHONE", None)
    client = TelegramClient(session, int(api_id), api_hash)
    if phone:
        await client.start(phone=phone)
    else:
        await client.start()
    me = await client.get_me()
    print(f"User session is ready: @{me.username}" if me.username else f"User session is ready: {me.id}")
    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
