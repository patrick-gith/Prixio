import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task
def process_opportunity_task(opp_id: int):
    from .engine import recommend
    from .models import Opportunity, Recommendation
    try:
        opp = Opportunity.objects.get(id=opp_id)
    except Opportunity.DoesNotExist:
        return
    rec = recommend(opp.text)
    if not rec:
        return
    Recommendation.objects.create(
        opportunity=opp, service=rec.service, score=rec.score,
        confidence=rec.confidence, language=rec.language,
        intent=rec.intent, reply_text=rec.reply,
    )
    opp.status = "recommended"
    opp.score = rec.score
    opp.save(update_fields=["status", "score"])


@shared_task
def run_discovery_task():
    from .discovery import fetch_brave, fetch_google_alerts, fetch_rss
    from .models import SearchQuery
    for q in SearchQuery.objects.filter(is_active=True):
        try:
            if q.kind == "brave":
                fetch_brave(q.query)
            elif q.kind == "google_alerts":
                fetch_google_alerts(q.url)
            elif q.kind == "rss":
                fetch_rss(q.url, channel=q.channel)
        except Exception as e:
            logger.warning("discovery failed for %s: %s", q.id, e)


@shared_task
def process_pending_task(limit: int = 20):
    """
    Parcourt les opportunités 'new' (max `limit`) et lance le pipeline
    de recommandation sur chacune. Évite de surcharger le LLM.
    """
    import logging
    from .models import Opportunity
    logger = logging.getLogger(__name__)

    ids = list(
        Opportunity.objects.filter(status="new")
        .order_by("-created_at")
        .values_list("id", flat=True)[:limit]
    )
    logger.info("process_pending_task: %d opportunité(s) à traiter", len(ids))
    for oid in ids:
        process_opportunity_task.delay(oid)
    return {"queued": len(ids)}
