"""Récupère les messages du bot et traite les codes de liaison.

À lancer toutes les minutes via un cron Render :
    */1 * * * * python manage.py telegram_poll
"""
import logging
import os

import requests
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from PrixioApp.models import UserProfile
from PricingApp import telegram_service

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Poll les nouveaux messages du bot et associe les codes de liaison."

    def handle(self, *args, **options):
        token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
        if not token:
            self.stderr.write("TELEGRAM_BOT_TOKEN manquant.")
            return

        # Récupère le dernier offset depuis le cache
        from django.core.cache import cache
        offset = cache.get("telegram_offset", 0)

        try:
            r = requests.get(
                f"https://api.telegram.org/bot{token}/getUpdates",
                params={"offset": offset, "timeout": 0},
                timeout=10,
            )
            r.raise_for_status()
            data = r.json()
        except requests.RequestException as exc:
            self.stderr.write(f"Telegram getUpdates failed: {exc}")
            return

        for update in data.get("result", []):
            offset = max(offset, update["update_id"] + 1)
            message = update.get("message") or {}
            text = (message.get("text") or "").strip()
            chat_id = str(message.get("chat", {}).get("id", ""))
            if not text or not chat_id:
                continue

            if text.startswith("/start"):
                # Format : /start CODE ou /start
                parts = text.split()
                code = parts[1].upper() if len(parts) > 1 else ""

                if not code:
                    telegram_service.send_message(
                        chat_id,
                        "Bienvenue sur Prixio 🌍\n\n"
                        "Pour lier votre compte, rendez-vous sur "
                        "prixio.app/telegram/ et envoyez-moi le code affiché.",
                    )
                    continue

                # Cherche un profil qui attend ce code
                # (on stocke le code dans la session → non accessible ici,
                # donc on cherche par code temporaire stocké en cache)
                key = f"telegram_code:{code}"
                user_id = cache.get(key)
                if not user_id:
                    telegram_service.send_message(
                        chat_id, "Code invalide ou expiré. Réessayez depuis le site."
                    )
                    continue

                try:
                    user = User.objects.get(id=user_id)
                    profile, _ = UserProfile.objects.get_or_create(user=user)
                    profile.telegram_chat_id = chat_id
                    profile.save(update_fields=["telegram_chat_id"])
                    cache.delete(key)

                    telegram_service.send_message(
                        chat_id,
                        f"✅ Compte lié !\n\n"
                        f"Vous recevrez les alertes pour {user.username}.",
                    )
                    self.stdout.write(f"Linked {user.username} → chat {chat_id}")
                except User.DoesNotExist:
                    pass

        cache.set("telegram_offset", offset, timeout=None)