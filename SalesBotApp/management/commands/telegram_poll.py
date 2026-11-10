from django.core.management.base import BaseCommand
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from django.conf import settings
from SalesBotApp.models import Opportunity
from SalesBotApp.tasks import process_opportunity_task

class Command(BaseCommand):
    help = "Écoute les messages Telegram et crée des opportunités"

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        msg = update.message
        if not msg or not msg.text:
            return
        opp = Opportunity.objects.create(
            source="telegram", channel="telegram",
            text=msg.text, author_id=str(msg.from_user.id),
            context=str(msg.chat_id),
            url=f"https://t.me/c/{str(msg.chat_id)[4:]}/{msg.message_id}"
        )
        process_opportunity_task.delay(opp.id)

    def handle(self, *args, **options):
        app = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        self.stdout.write("🤖 Bot Telegram en écoute...")
        app.run_polling()
