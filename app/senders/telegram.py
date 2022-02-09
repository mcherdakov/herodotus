import asyncio

import aiogram

from app.senders.models import Message
from app.settings import settings

bot = aiogram.Bot(settings.telegram_token)


async def send_telegram(chat_ids: list[int], message: Message):
    await asyncio.gather(
        *[
            bot.send_message(
                chat_id=chat_id,
                text=f"<strong>{message.title}</strong>\n\n{message.text}",
                parse_mode="HTML",
            )
            for chat_id in chat_ids
        ]
    )
