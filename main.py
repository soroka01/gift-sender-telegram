import asyncio
import html
import json
import logging
import re
import secrets
import time
from dataclasses import dataclass, field, replace
from datetime import date
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Iterable

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import MessageEntityType, ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from telethon import TelegramClient, functions, types
from telethon.errors import RPCError

from config import ADMIN_IDS, API_HASH, API_ID, BOT_TOKEN, DEFAULT_HIDE_NAME, DEFAULT_INCLUDE_UPGRADE, GIFT_MESSAGE, USER_SESSION

USERNAME_RE = re.compile(r"^@?[A-Za-z0-9_]{5,32}$")
MAX_GIFTS_IN_KEYBOARD = 24
MAX_GIFT_MESSAGE_LENGTH = 255
MAX_GIFT_DESCRIPTION_LENGTH = 120
LOG_PATH = Path(__file__).resolve().with_name("gift_sender.log")
GIFT_DESCRIPTIONS_PATH = Path(__file__).resolve().with_name("gift_descriptions.json")
logger = logging.getLogger("gift_sender")


def configure_logging() -> None:
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    file_handler = RotatingFileHandler(
        LOG_PATH,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    logging.basicConfig(level=logging.INFO, handlers=[console, file_handler], force=True)


@dataclass(frozen=True)
class Config:
    bot_token: str
    api_id: int
    api_hash: str
    user_session: str
    admin_ids: set[int]
    default_hide_name: bool
    default_include_upgrade: bool
    gift_message: str | None


@dataclass
class PendingGift:
    target_username: str
    target_peer: types.TypeInputPeer
    gift_id: int
    gift_title: str
    stars: int
    availability: str
    release_date: str | None
    description: str | None
    upgrade_details: str
    hide_name: bool
    include_upgrade: bool
    message: str | None
    message_entities: list[types.TypeMessageEntity] = field(default_factory=list)


@dataclass(frozen=True)
class GiftOption:
    id: int
    title: str
    emoji: str
    stars: int
    availability: str
    upgrade_details: str
    release_date: date | None = None
    removed_from_store: bool = False
    description: str | None = None

    @property
    def release_date_label(self) -> str | None:
        return self.release_date.strftime("%d.%m.%Y") if self.release_date else None

    @property
    def button_details(self) -> str:
        if self.removed_from_store and self.release_date_label:
            details = f"{self.release_date_label} · {self.title}"
        else:
            details = self.availability.replace("осталось ", "ост. ")
        return f"{details} · {self.description}" if self.description else details


@dataclass(frozen=True)
class GiftCustomization:
    name: str | None = None
    description: str | None = None


# Telegram removes these unlimited 50-Star bears from GetStarGifts after their
# short storefront window, but CheckCanSendGift and InputInvoiceStarGift still
# accept their IDs. Dates are the first public availability dates in local time
# (Asia/Yekaterinburg).
REMOVED_UNLIMITED_GIFTS = (
    GiftOption(5956217000635139069, "Новогодний мишка", "🧸", 50, "без лимита (снят с витрины)", "не поддерживается", date(2025, 12, 31), True),
    GiftOption(5800655655995968830, "Мишка на 14 февраля", "🧸", 50, "без лимита (снят с витрины)", "не поддерживается", date(2026, 2, 14), True),
    GiftOption(5866352046986232958, "Мишка на 8 марта", "🧸", 50, "без лимита (снят с витрины)", "не поддерживается", date(2026, 3, 8), True),
    GiftOption(5893356958802511476, "Мишка на День святого Патрика", "🧸", 50, "без лимита (снят с витрины)", "не поддерживается", date(2026, 3, 17), True),
    GiftOption(5935895822435615975, "Мишка на 1 апреля", "🧸", 50, "без лимита (снят с витрины)", "не поддерживается", date(2026, 4, 1), True),
    GiftOption(5969796561943660080, "Мишка", "🧸", 50, "без лимита (снят с витрины)", "не поддерживается", date(2026, 4, 12), True),
    GiftOption(6026193266406327981, "Мишка", "🧸", 50, "без лимита (снят с витрины)", "не поддерживается", date(2026, 5, 1), True),
    GiftOption(5974210632977745012, "Мишка-футболист", "🧸", 50, "без лимита (снят с витрины)", "не поддерживается", date(2026, 7, 20), True),
    GiftOption(6046178578163303744, "Мишка", "🧸", 50, "без лимита (снят с витрины)", "не поддерживается", date(2026, 8, 13), True),
)


class PaymentVerificationRequired(Exception):
    def __init__(self, url: str) -> None:
        self.url = url


class GiftService:
    def __init__(self, client: TelegramClient, descriptions_path: Path = GIFT_DESCRIPTIONS_PATH) -> None:
        self.client = client
        self.descriptions_path = descriptions_path

    async def resolve_user(self, username: str) -> types.TypeInputPeer:
        return await self.client.get_input_entity(await self.client.get_entity(username.lstrip("@")))

    async def available_gifts(self) -> list[GiftOption]:
        result = await self.client(functions.payments.GetStarGiftsRequest(hash=0))
        current = [
            gift_option(gift)
            for gift in getattr(result, "gifts", [])
            if not getattr(gift, "sold_out", False) and int(getattr(gift, "stars", 0)) > 0
        ]
        gifts_by_id = {gift.id: gift for gift in current}
        for gift in REMOVED_UNLIMITED_GIFTS:
            gifts_by_id.setdefault(gift.id, gift)
        customizations = load_gift_customizations(self.descriptions_path)
        return [
            replace(
                gift,
                title=customizations[gift.id].name or gift.title,
                description=customizations[gift.id].description,
            ) if gift.id in customizations else gift
            for gift in gifts_by_id.values()
        ]

    async def check_can_send(self, gift_id: int) -> tuple[bool, str | None]:
        request = getattr(functions.payments, "CheckCanSendGiftRequest", None)
        if request is None:
            return True, None
        result = await self.client(request(gift_id=gift_id))
        if result.__class__.__name__.endswith("Ok"):
            return True, None
        return False, getattr(getattr(result, "reason", None), "text", None) or "Telegram не разрешил отправку."

    async def send_gift(self, item: PendingGift) -> None:
        text = item.message or ""
        invoice = types.InputInvoiceStarGift(
            peer=item.target_peer, gift_id=item.gift_id, hide_name=item.hide_name,
            include_upgrade=item.include_upgrade,
            message=types.TextWithEntities(text=text, entities=item.message_entities) if text else None,
        )
        form = await self.client(functions.payments.GetPaymentFormRequest(invoice=invoice))
        result = await self.client(functions.payments.SendStarsFormRequest(form_id=form.form_id, invoice=invoice))
        if url := getattr(result, "url", None):
            raise PaymentVerificationRequired(url)


def load_config() -> Config:
    try:
        admins = {int(value) for value in ADMIN_IDS}
    except (TypeError, ValueError) as exc:
        raise RuntimeError("ADMIN_IDS in config.py must contain numeric Telegram user IDs.") from exc
    if not BOT_TOKEN or not API_HASH or not API_ID:
        raise RuntimeError("Fill BOT_TOKEN, API_ID and API_HASH in config.py before starting.")
    if not admins:
        raise RuntimeError("ADMIN_IDS must not be empty: otherwise anyone could spend your Stars.")
    message = (GIFT_MESSAGE or "").strip() or None
    if message and len(message) > MAX_GIFT_MESSAGE_LENGTH:
        raise RuntimeError(f"GIFT_MESSAGE must be at most {MAX_GIFT_MESSAGE_LENGTH} characters.")
    return Config(BOT_TOKEN, int(API_ID), API_HASH, USER_SESSION or "user_account", admins, bool(DEFAULT_HIDE_NAME), bool(DEFAULT_INCLUDE_UPGRADE), message)


def load_gift_customizations(path: Path = GIFT_DESCRIPTIONS_PATH) -> dict[int, GiftCustomization]:
    if not path.exists():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Cannot read gift descriptions from {path.name}: {exc}") from exc
    if not isinstance(raw, dict):
        raise RuntimeError(f"{path.name} must contain a JSON object.")

    if "gifts" in raw:
        gifts = raw["gifts"]
        if not isinstance(gifts, list):
            raise RuntimeError(f"The gifts field in {path.name} must be a JSON array.")
        entries = []
        for index, gift in enumerate(gifts, start=1):
            if not isinstance(gift, dict):
                raise RuntimeError(f"Gift entry #{index} in {path.name} must be a JSON object.")
            if "gift_id" not in gift:
                raise RuntimeError(f"Gift entry #{index} in {path.name} has no gift_id.")
            entries.append((gift["gift_id"], gift.get("name"), gift.get("description", "")))
    else:
        # Backward compatibility with the original {"gift_id": "description"} format.
        entries = [(gift_id, None, description) for gift_id, description in raw.items()]

    customizations: dict[int, GiftCustomization] = {}
    seen_ids: set[int] = set()
    for raw_id, raw_name, raw_description in entries:
        try:
            gift_id = int(raw_id)
        except (TypeError, ValueError) as exc:
            raise RuntimeError(f"Invalid gift ID in {path.name}: {raw_id!r}") from exc
        if gift_id in seen_ids:
            raise RuntimeError(f"Duplicate gift ID in {path.name}: {gift_id}")
        seen_ids.add(gift_id)
        if raw_name is not None and not isinstance(raw_name, str):
            raise RuntimeError(f"Name for gift {gift_id} must be a string.")
        if not isinstance(raw_description, str):
            raise RuntimeError(f"Description for gift {gift_id} must be a string.")
        name = " ".join(raw_name.split()) if raw_name else ""
        description = " ".join(raw_description.split())
        if len(name) > MAX_GIFT_DESCRIPTION_LENGTH:
            raise RuntimeError(
                f"Name for gift {gift_id} exceeds {MAX_GIFT_DESCRIPTION_LENGTH} characters."
            )
        if len(description) > MAX_GIFT_DESCRIPTION_LENGTH:
            raise RuntimeError(
                f"Description for gift {gift_id} exceeds {MAX_GIFT_DESCRIPTION_LENGTH} characters."
            )
        if name or description:
            customizations[gift_id] = GiftCustomization(
                name=name or None,
                description=description or None,
            )
    return customizations


def is_admin(config: Config, update: Message | CallbackQuery) -> bool:
    return update.from_user is not None and update.from_user.id in config.admin_ids


def username(raw: str) -> str | None:
    return "@" + raw.strip().lstrip("@") if USERNAME_RE.fullmatch(raw.strip()) else None


def emoji(gift: types.TypeStarGift) -> str:
    sticker = getattr(gift, "sticker", None)
    alt = getattr(sticker, "alt", None)
    if not alt:
        alt = next((getattr(attribute, "alt", None) for attribute in getattr(sticker, "attributes", []) if getattr(attribute, "alt", None)), None)
    return str(alt or "🎁")


def availability(gift: types.TypeStarGift) -> str:
    remains, total = getattr(gift, "availability_remains", None), getattr(gift, "availability_total", None)
    return "без лимита" if remains is None or total is None else f"осталось {int(remains)} из {int(total)}"


def upgrade_details(gift: types.TypeStarGift) -> str:
    stars = getattr(gift, "upgrade_stars", None)
    return "нет данных" if stars is None else ("не поддерживается" if int(stars) <= 0 else f"доступно за {int(stars)} Stars")


def gift_option(gift: types.TypeStarGift) -> GiftOption:
    gift_emoji = emoji(gift)
    return GiftOption(
        id=int(gift.id),
        title=str(getattr(gift, "title", None) or "подарок"),
        emoji=gift_emoji,
        stars=int(gift.stars),
        availability=availability(gift),
        upgrade_details=upgrade_details(gift),
    )


def gift_sort_key(gift: GiftOption) -> tuple[int, int, int, int]:
    released = gift.release_date.toordinal() if gift.release_date else 0
    return gift.stars, int(gift.removed_from_store), -released, gift.id


def utf16_length(text: str) -> int:
    return len(text.encode("utf-16-le")) // 2


def custom_emoji_entities(message: Message, text: str) -> list[types.TypeMessageEntity]:
    text_length = utf16_length(text)
    result: list[types.TypeMessageEntity] = []
    for entity in message.entities or []:
        entity_type = entity.type.value if hasattr(entity.type, "value") else str(entity.type)
        if entity_type != MessageEntityType.CUSTOM_EMOJI.value or not entity.custom_emoji_id:
            continue
        if entity.offset < 0 or entity.length <= 0 or entity.offset + entity.length > text_length:
            continue
        result.append(types.MessageEntityCustomEmoji(
            offset=entity.offset,
            length=entity.length,
            document_id=int(entity.custom_emoji_id),
        ))
    return result


def gifts_keyboard(gifts: Iterable[GiftOption], target: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text=f"{gift.emoji} · {gift.stars} ⭐ · {gift.button_details}"[:64],
            callback_data=f"pick:{target.lstrip('@')}:{gift.id}",
        )
    ] for gift in list(gifts)[:MAX_GIFTS_IN_KEYBOARD]])


def message_preview(item: PendingGift, limit: int | None = None) -> str:
    if not item.message:
        return "не добавлен"
    shown = item.message if limit is None else item.message[:limit]
    suffix = "..." if limit is not None and len(item.message) > limit else ""
    return f"«{html.escape(shown)}{suffix}»"


def gift_details_text(item: PendingGift, message_limit: int | None = 120) -> str:
    custom_emoji_note = f" (Premium Emoji сохранено: {len(item.message_entities)})" if item.message_entities else ""
    release_date = f"Дата выхода: <b>{html.escape(item.release_date)}</b>\n" if item.release_date else ""
    description = f"Описание: <b>{html.escape(item.description)}</b>\n" if item.description else ""
    return (
        f"Получатель: <b>{html.escape(item.target_username)}</b>\n"
        f"Подарок: <b>{html.escape(item.gift_title)}</b>\n"
        f"Стоимость: <b>{item.stars} Stars</b>\n"
        f"{release_date}"
        f"{description}"
        f"Доступность: <b>{html.escape(item.availability)}</b>\n"
        f"Улучшение подарка: <b>{html.escape(item.upgrade_details)}</b>\n"
        f"Разрешить улучшение: <b>{'да' if item.include_upgrade else 'нет'}</b>\n"
        f"Имя отправителя: <b>{'скрыто (анонимно)' if item.hide_name else 'видно получателю'}</b>\n"
        f"Текст на подарке: <b>{message_preview(item, message_limit)}</b>{custom_emoji_note}\n\n"
        f"Технический ID: <code>{item.gift_id}</code>"
    )


def confirmation_text(item: PendingGift) -> str:
    return "<b>Проверь параметры перед оплатой</b>\n\n" + gift_details_text(item)


def text_input_text(item: PendingGift) -> str:
    description = f"\nОписание: <b>{html.escape(item.description)}</b>" if item.description else ""
    return (
        "<b>✍️ Текст для подарка</b>\n\n"
        f"Получатель: <b>{html.escape(item.target_username)}</b>\n"
        f"Подарок: <b>{html.escape(item.gift_title)}</b> за <b>{item.stars} Stars</b>"
        f"{description}\n\n"
        f"Текущий текст: <b>{message_preview(item)}</b>\n\n"
        f"Пришли следующим сообщением новый текст (до {MAX_GIFT_MESSAGE_LENGTH} символов). "
        "Кастомные Premium Emoji сохранятся."
    )


def final_text(item: PendingGift) -> str:
    return "<b>✅ Подарок успешно отправлен</b>\n\n" + gift_details_text(item, message_limit=None)


def confirmation_keyboard(token: str, item: PendingGift) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="👤 Имя: скрыто" if item.hide_name else "👤 Имя: видно", callback_data=f"anon:{token}")],
        [InlineKeyboardButton(text="⬆️ Улучшение: разрешено" if item.include_upgrade else "⬆️ Улучшение: запрещено", callback_data=f"upgrade:{token}")],
        [InlineKeyboardButton(text="✍️ Изменить текст" if item.message else "✍️ Добавить текст", callback_data=f"text:{token}")],
    ]
    if item.message:
        rows.append([InlineKeyboardButton(text="🗑 Убрать текст", callback_data=f"clear:{token}")])
    rows += [
        [InlineKeyboardButton(text=f"✅ Отправить за {item.stars} ⭐", callback_data=f"send:{token}")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data=f"cancel:{token}")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def main() -> None:
    configure_logging()
    config = load_config()
    logger.info("service_starting log_file=%s admins=%d", LOG_PATH, len(config.admin_ids))
    user_client = TelegramClient(config.user_session, config.api_id, config.api_hash)
    await user_client.start()
    service = GiftService(user_client)
    bot = Bot(config.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp, router = Dispatcher(), Router()
    pending: dict[str, PendingGift] = {}
    waiting_text: dict[int, tuple[str, int, int]] = {}

    async def show_confirmation(query: CallbackQuery, token: str, item: PendingGift) -> None:
        await query.message.edit_text(confirmation_text(item), reply_markup=confirmation_keyboard(token, item))

    @router.message(CommandStart())
    async def on_start(message: Message) -> None:
        if not is_admin(config, message):
            logger.warning("access_denied action=start user_id=%s", getattr(message.from_user, "id", None))
            await message.answer("Нет доступа.")
            return
        logger.info("start_opened admin_id=%d", message.from_user.id)
        await message.answer(
            "<b>Отправка Telegram Gifts</b>\n\nКоманда: <code>/gift @username</code>\n\n"
            "Выбери подарок по цене и остатку, затем проверь текст, анонимность и возможность улучшения перед оплатой.\n\n"
            "Журнал операций: <code>gift_sender.log</code>"
        )

    @router.message(Command("gift"))
    async def on_gift(message: Message) -> None:
        if not is_admin(config, message):
            logger.warning("access_denied action=gift user_id=%s", getattr(message.from_user, "id", None))
            await message.answer("Нет доступа.")
            return
        args = (message.text or "").split(maxsplit=1)
        target = username(args[1]) if len(args) > 1 else None
        if not target:
            logger.info("gift_request_invalid admin_id=%d", message.from_user.id)
            await message.answer("Укажи получателя: <code>/gift @username</code>")
            return
        logger.info("catalog_requested admin_id=%d target=%s", message.from_user.id, target)
        status = await message.answer("Получаю доступные Telegram Gifts…")
        try:
            await service.resolve_user(target)
            gifts = sorted(await service.available_gifts(), key=gift_sort_key)
        except (RPCError, ValueError) as exc:
            logger.warning("catalog_failed admin_id=%d target=%s error=%s", message.from_user.id, target, type(exc).__name__)
            await status.edit_text(f"Не удалось получить подарки: <code>{html.escape(str(exc))}</code>")
            return
        except Exception as exc:
            logger.exception("catalog_failed admin_id=%d target=%s", message.from_user.id, target)
            await status.edit_text(f"Не удалось получить подарки: <code>{type(exc).__name__}</code>")
            return
        if not gifts:
            logger.info("catalog_empty admin_id=%d target=%s", message.from_user.id, target)
            await status.edit_text("Сейчас нет доступных подарков для отправки.")
            return
        shown = min(len(gifts), MAX_GIFTS_IN_KEYBOARD)
        logger.info("catalog_loaded admin_id=%d target=%s total=%d shown=%d", message.from_user.id, target, len(gifts), shown)
        await status.edit_text(
            f"Получатель: <b>{html.escape(target)}</b>\nДоступно: <b>{len(gifts)}</b>, показаны первые <b>{shown}</b> по цене.\n\nНа кнопках: эмодзи, цена и остаток; у снятых мишек — дата выхода.",
            reply_markup=gifts_keyboard(gifts, target),
        )

    @router.callback_query(F.data.startswith("pick:"))
    async def on_pick(query: CallbackQuery) -> None:
        if not is_admin(config, query):
            logger.warning("access_denied action=pick user_id=%s", getattr(query.from_user, "id", None))
            await query.answer("Нет доступа.", show_alert=True)
            return
        try:
            _, user_part, raw_id = (query.data or "").split(":", 2)
            target, gift_id = "@" + user_part, int(raw_id)
            target_peer = await service.resolve_user(target)
            gift = next(g for g in await service.available_gifts() if g.id == gift_id)
            can_send, reason = await service.check_can_send(gift_id)
            if not can_send:
                logger.warning("gift_unavailable admin_id=%d target=%s gift_id=%d", query.from_user.id, target, gift_id)
                await query.answer(reason or "Отправка недоступна.", show_alert=True)
                return
        except StopIteration:
            logger.warning("gift_missing admin_id=%d gift_id=%s", query.from_user.id, locals().get("gift_id"))
            await query.answer("Подарок уже недоступен. Запусти /gift заново.", show_alert=True)
            return
        except Exception as exc:
            logger.exception("gift_prepare_failed admin_id=%d gift_id=%s", query.from_user.id, locals().get("gift_id"))
            await query.answer(f"Ошибка подготовки: {type(exc).__name__}", show_alert=True)
            return
        token = secrets.token_urlsafe(8)
        item = PendingGift(
            target_username=target,
            target_peer=target_peer,
            gift_id=gift_id,
            gift_title=f"{gift.emoji} {gift.title}",
            stars=gift.stars,
            availability=gift.availability,
            release_date=gift.release_date_label,
            description=gift.description,
            upgrade_details=gift.upgrade_details,
            hide_name=config.default_hide_name,
            include_upgrade=config.default_include_upgrade,
            message=config.gift_message,
        )
        pending[token] = item
        logger.info(
            "gift_prepared admin_id=%d target=%s gift_id=%d price=%d removed=%s described=%s hide_name=%s include_upgrade=%s",
            query.from_user.id, target, gift_id, item.stars, gift.removed_from_store, bool(item.description), item.hide_name, item.include_upgrade,
        )
        await query.answer()
        await show_confirmation(query, token, item)

    @router.callback_query(F.data.startswith("anon:") | F.data.startswith("upgrade:"))
    async def on_toggle(query: CallbackQuery) -> None:
        action, token = (query.data or "").split(":", 1)
        item = pending.get(token)
        if not is_admin(config, query) or not item:
            await query.answer("Заявка устарела или нет доступа.", show_alert=True)
            return
        if action == "anon":
            item.hide_name = not item.hide_name
        else:
            item.include_upgrade = not item.include_upgrade
        logger.info(
            "gift_option_changed admin_id=%d gift_id=%d option=%s value=%s",
            query.from_user.id,
            item.gift_id,
            action,
            item.hide_name if action == "anon" else item.include_upgrade,
        )
        await query.answer("Параметр обновлён.")
        await show_confirmation(query, token, item)

    @router.callback_query(F.data.startswith("text:") | F.data.startswith("clear:") | F.data.startswith("back:") | F.data.startswith("cancel:"))
    async def on_text_actions(query: CallbackQuery) -> None:
        action, token = (query.data or "").split(":", 1)
        item = pending.get(token)
        if not is_admin(config, query) or not item:
            await query.answer("Заявка устарела или нет доступа.", show_alert=True)
            return
        if action == "cancel":
            pending.pop(token, None); waiting_text.pop(query.from_user.id, None)
            logger.info("gift_cancelled admin_id=%d target=%s gift_id=%d", query.from_user.id, item.target_username, item.gift_id)
            await query.answer("Отменено.")
            await query.message.edit_text("Отправка отменена. Stars не списывались.")
        elif action == "clear":
            item.message = None; item.message_entities.clear(); waiting_text.pop(query.from_user.id, None)
            logger.info("gift_text_cleared admin_id=%d gift_id=%d", query.from_user.id, item.gift_id)
            await query.answer("Текст убран.")
            await show_confirmation(query, token, item)
        elif action == "back":
            waiting_text.pop(query.from_user.id, None)
            logger.info("gift_text_input_closed admin_id=%d gift_id=%d", query.from_user.id, item.gift_id)
            await query.answer()
            await show_confirmation(query, token, item)
        else:
            waiting_text[query.from_user.id] = (token, query.message.chat.id, query.message.message_id)
            logger.info("gift_text_input_opened admin_id=%d gift_id=%d", query.from_user.id, item.gift_id)
            await query.answer()
            await query.message.edit_text(
                text_input_text(item),
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🗑 Без текста", callback_data=f"clear:{token}")],
                    [InlineKeyboardButton(text="↩️ Назад", callback_data=f"back:{token}"), InlineKeyboardButton(text="❌ Отмена", callback_data=f"cancel:{token}")],
                ]),
            )

    @router.message(F.text)
    async def on_gift_text(message: Message) -> None:
        if not is_admin(config, message) or message.from_user is None:
            return
        waiting = waiting_text.get(message.from_user.id)
        token = waiting[0] if waiting else None
        item = pending.get(token) if token else None
        if not item:
            waiting_text.pop(message.from_user.id, None)
            return
        text = message.text or ""
        if not text.strip():
            logger.info("gift_text_rejected admin_id=%d gift_id=%d reason=empty", message.from_user.id, item.gift_id)
            await message.answer("Пустой текст не сохранён. Пришли непустое сообщение или нажми «Без текста».")
            return
        waiting_text.pop(message.from_user.id, None)
        item.message = text[:MAX_GIFT_MESSAGE_LENGTH]
        item.message_entities = custom_emoji_entities(message, item.message)
        logger.info(
            "gift_text_saved admin_id=%d gift_id=%d length=%d custom_emoji=%d truncated=%s",
            message.from_user.id,
            item.gift_id,
            len(item.message),
            len(item.message_entities),
            len(text) > MAX_GIFT_MESSAGE_LENGTH,
        )
        note = "\n\nТекст сокращён до 255 символов." if len(text) > MAX_GIFT_MESSAGE_LENGTH else ""
        try:
            await bot.edit_message_text(
                chat_id=waiting[1],
                message_id=waiting[2],
                text=confirmation_text(item) + note,
                reply_markup=confirmation_keyboard(token, item),
            )
        except TelegramBadRequest:
            await message.answer(confirmation_text(item) + note, reply_markup=confirmation_keyboard(token, item))

    @router.callback_query(F.data.startswith("send:"))
    async def on_send(query: CallbackQuery) -> None:
        if not is_admin(config, query):
            logger.warning("access_denied action=send user_id=%s", getattr(query.from_user, "id", None))
            await query.answer("Нет доступа.", show_alert=True)
            return
        token = (query.data or "").split(":", 1)[1]
        item = pending.pop(token, None)
        if not item:
            logger.warning("gift_send_stale admin_id=%d", query.from_user.id)
            await query.answer("Заявка устарела или уже отправлена.", show_alert=True)
            return
        started_at = time.monotonic()
        logger.info(
            "gift_send_started admin_id=%d target=%s gift_id=%d price=%d hide_name=%s include_upgrade=%s text_length=%d custom_emoji=%d",
            query.from_user.id,
            item.target_username,
            item.gift_id,
            item.stars,
            item.hide_name,
            item.include_upgrade,
            len(item.message or ""),
            len(item.message_entities),
        )
        await query.answer()
        await query.message.edit_text("<b>⏳ Отправляю подарок и списываю Stars…</b>\n\n" + gift_details_text(item))
        try:
            await service.send_gift(item)
        except PaymentVerificationRequired as exc:
            logger.warning(
                "gift_send_verification_required admin_id=%d target=%s gift_id=%d duration_ms=%d",
                query.from_user.id, item.target_username, item.gift_id, int((time.monotonic() - started_at) * 1000),
            )
            await query.message.edit_text(
                "<b>⚠️ Telegram запросил проверку платежа</b>\n\n"
                f"{html.escape(exc.url)}\n\nПосле проверки запусти отправку заново.\n\n"
                + gift_details_text(item, message_limit=None)
            )
        except RPCError as exc:
            logger.warning(
                "gift_send_rpc_failed admin_id=%d target=%s gift_id=%d error=%s duration_ms=%d",
                query.from_user.id, item.target_username, item.gift_id, type(exc).__name__, int((time.monotonic() - started_at) * 1000),
            )
            await query.message.edit_text(
                f"<b>❌ Telegram API вернул ошибку</b>\n<code>{html.escape(str(exc))}</code>\n\n"
                + gift_details_text(item, message_limit=None)
            )
        except Exception as exc:
            logger.exception(
                "gift_send_failed admin_id=%d target=%s gift_id=%d duration_ms=%d",
                query.from_user.id, item.target_username, item.gift_id, int((time.monotonic() - started_at) * 1000),
            )
            await query.message.edit_text(
                f"<b>❌ Не удалось отправить</b>: <code>{type(exc).__name__}</code>\n\n"
                + gift_details_text(item, message_limit=None)
            )
        else:
            logger.info(
                "gift_send_succeeded admin_id=%d target=%s gift_id=%d price=%d hide_name=%s duration_ms=%d",
                query.from_user.id,
                item.target_username,
                item.gift_id,
                item.stars,
                item.hide_name,
                int((time.monotonic() - started_at) * 1000),
            )
            await query.message.edit_text(final_text(item))

    dp.include_router(router)
    try:
        await dp.start_polling(bot)
    finally:
        logger.info("service_stopped")
        await bot.session.close()
        await user_client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
