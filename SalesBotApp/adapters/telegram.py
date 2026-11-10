import asyncio
from telegram import Bot
from django.conf import settings
from .base import ChannelAdapter, PublishResult

class TelegramAdapter(ChannelAdapter):
    channel = "telegram"

    def _do_publish(self, opportunity, recommendation):
        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        try:
            asyncio.run(bot.send_message(
                chat_id=opportunity.context,  # ID du chat ou du groupe
                text=recommendation.reply,
            ))
            return PublishResult(True, "published")
        except Exception as e:
            return PublishResult(False, "failed", str(e))
