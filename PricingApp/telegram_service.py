# PricingApp/telegram_service.py
"""
Notifications Telegram.

Architecture :
  - L'utilisateur envoie /start à ton bot
  - Le bot répond avec un code à 6 caractères + deep link
  - L'utilisateur colle le code dans son profil Prixio
  - Prixio associe le chat_id à l'utilisateur
  - Ensuite, les alertes partent via sendMessage

On utilise l'API HTTP directement (pas de framework bot) pour rester léger.
"""
from __future__ import annotations

import logging
import os
import secrets
import string

import requests

logger = logging.getLogger(__name__)


TELEGRAM_API = "https://api.telegram.org"
LINK_CODE_LENGTH = 6
LINK_CODE_ALPHABET = string.ascii_uppercase + string.digits


def _bot_token() -> str:
    return os.environ.get("TELEGRAM_BOT_TOKEN", "")


def is_configured() -> bool:
    return bool(_bot_token())


def generate_link_code() -> str:
    """Code à 6 caractères, sans I/O ambiguës."""
    safe = LINK_CODE_ALPHABET.replace("O", "").replace("I", "").replace("0", "")
    return "".join(secrets.choice(safe) for _ in range(LINK_CODE_LENGTH))


def send_message(chat_id: str, text: str, parse_mode: str = "HTML") -> bool:
    """Envoie un message. Retourne True si Telegram a accepté."""
    token = _bot_token()
    if not token or not chat_id:
        return False

    try:
        r = requests.post(
            f"{TELEGRAM_API}/bot{token}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": parse_mode,
                "disable_web_page_preview": True,
            },
            timeout=6,
        )
        if r.status_code != 200:
            logger.warning("Telegram sendMessage failed: %s %s", r.status_code, r.text[:200])
            return False
        return True
    except requests.RequestException as exc:
        logger.warning("Telegram network error: %s", exc)
        return False


def format_alert_message(product, analysis: dict, url: str | None = None) -> str:
    """
    Formate une alerte pour Telegram (HTML supporté).

    Exemple de sortie :
        🔥 <b>Le Petit Prince</b>
        Prix : <b>8.90 EUR</b> (médiane 12.40)
        Économie : -28.2%
        Score : 84/100

        <a href="...">Voir la fiche</a>
    """
    title = product.title[:60]
    score = analysis.get("score", 0)
    emoji = "🔥" if score >= 80 else "✅" if score >= 60 else "🟡"

    price = analysis.get("current_price", 0)
    median = analysis.get("baseline", {}).get("median", 0)
    currency = analysis.get("currency", "EUR")
    deviation = analysis.get("deviation_pct", 0)

    lines = [
        f"{emoji} <b>{title}</b>",
        f"Prix : <b>{price:.2f} {currency}</b> (médiane {median:.2f})",
        f"Économie : <b>-{deviation}%</b>" if deviation > 0 else "Prix stable",
        f"Score : {score}/100",
    ]
    if url:
        lines.append(f"\n<a href=\"{url}\">Voir la fiche produit</a>")

    return "\n".join(lines)