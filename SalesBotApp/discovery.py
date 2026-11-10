import logging

import requests
from django.conf import settings

from .models import Opportunity

logger = logging.getLogger(__name__)


def _save(source, channel, title, text, url, author_id="", context=""):
    obj, _ = Opportunity.objects.get_or_create(
        url=url,
        defaults=dict(source=source, channel=channel, title=title,
                      text=text, author_id=author_id, context=context),
    )
    return obj


def fetch_brave(query: str, count: int = 20):
    api_key = getattr(settings, "BRAVE_SEARCH_API_KEY", "")
    if not api_key:
        return []
    try:
        r = requests.get(
            "https://api.search.brave.com/res/v1/web/search",
            headers={"X-Subscription-Token": api_key, "Accept": "application/json"},
            params={"q": query, "count": count},
            timeout=15,
        )
        r.raise_for_status()
    except Exception as e:
        logger.warning("brave failed: %s", e)
        return []
    return [
        _save("brave", "google", it.get("title", ""), it.get("description", ""), it.get("url", ""))
        for it in r.json().get("web", {}).get("results", [])
    ]


def fetch_google_alerts(feed_url: str):
    try:
        import feedparser
    except ImportError:
        logger.warning("feedparser missing")
        return []
    feed = feedparser.parse(feed_url)
    return [
        _save("google_alerts", "google", e.get("title", ""), e.get("summary", ""), e.get("link", ""))
        for e in feed.entries
    ]


def fetch_rss(feed_url: str, channel: str = "rss", context: str = ""):
    try:
        import feedparser
    except ImportError:
        return []
    feed = feedparser.parse(feed_url)
    return [
        _save(f"rss:{feed_url}", channel, e.get("title", ""), e.get("summary", ""),
              e.get("link", ""), context=context)
        for e in feed.entries
    ]
