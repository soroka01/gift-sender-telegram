import asyncio

from telethon import TelegramClient

from config import API_HASH, API_ID, USER_SESSION


async def main() -> None:
    client = TelegramClient(USER_SESSION or "user_account", int(API_ID), API_HASH)
    await client.start()
    me = await client.get_me()
    print(f"User session is ready: @{me.username}" if me.username else f"User session is ready: {me.id}")
    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
