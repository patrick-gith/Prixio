from __future__ import annotations

import json
import logging
import math
import re
from collections import Counter
from dataclasses import dataclass
from typing import Optional

from django.conf import settings

logger = logging.getLogger(__name__)


@dataclass
class MatchResult:
    service: object
    score: float
    reason: str


@dataclass
class Recommendation:
    service: object
    score: float
    confidence: float
    language: str
    intent: str
    reply: str


def _client():
    from openai import OpenAI
    key = getattr(settings, "OPENAI_API_KEY", "")
    if not key:
        raise RuntimeError("OPENAI_API_KEY missing")
    return OpenAI(api_key=key)


def analyze_need(text: str) -> dict:
    try:
        resp = _client().chat.completions.create(
            model=getattr(settings, "OPENAI_MODEL", "gpt-4o-mini"),
            response_format={"type": "json_object"},
            messages=[
                {"role": "system",
                 "content": "Tu es un analyste commercial. Renvoie un JSON strict : "
                            '{"intent": string, "language": "fr"|"en", "confidence": float 0..1}.'},
                {"role": "user", "content": text},
            ],
        )
        return json.loads(resp.choices[0].message.content)
    except Exception as e:
        logger.warning("analyze_need failed: %s", e)
        return {"intent": "unknown", "language": "fr", "confidence": 0.5}


STOPWORDS = frozenset("""
le la les un une des de du et ou à au aux en sur pour par avec dans ce cette ces
votre vos mon mes ton tes son ses notre nos leur leurs
je tu il elle on nous vous ils elles me te se
que qui qu
d l s n y
est sont être avoir fait faire peut peuvent veut veux voulons voulez veulent
peux peut pouvons pouvez peuvent
tout tous toute toutes
plus moins très bien aussi même encore déjà
comment pourquoi quand où quel quelle quels quelles
si ne pas non oui
the a an of to in on for with and or
is are be been being have has had do does did
will would should can could may might must
not no yes how why when where what which who whom whose
some any all each every much many more most few less least
at by from up down out off over under again further then once
here there so than too very just also only own same such
i me my we our you your he him his she her it its they them their
this that these those
need needs needed want wants wanted wanting
someone somebody something
build building builds built make making makes made
""".split())

SUFFIXES = [
    "iquement", "isation", "isateur", "atrice", "ateur", "ation", "ement",
    "ique", "iser", "euse", "ées", "ée", "és", "er", "es", "e", "s",
    "ization", "ations", "ating", "ation", "ities", "ity",
    "ness", "ment", "ings", "ing", "ers", "er", "ed", "ly", "ies", "y", "s",
]

_WORD_RE = re.compile(r"[a-zàâäéèêëîïôöùûüç0-9]+")


def _stem(w: str) -> str:
    for suffix in SUFFIXES:
        if w.endswith(suffix) and len(w) - len(suffix) >= 4:
            return w[:-len(suffix)]
    return w


def _tokens(text: str) -> list[str]:
    out = []
    for w in _WORD_RE.findall((text or "").lower()):
        if len(w) < 3 or w in STOPWORDS:
            continue
        s = _stem(w)
        if len(s) >= 3:
            out.append(s)
    return out


def _match(a: str, b: str) -> bool:
    if a == b:
        return True
    if len(a) >= 5 and len(b) >= 5 and a[:5] == b[:5]:
        return True
    shorter, longer = (a, b) if len(a) <= len(b) else (b, a)
    if len(shorter) >= 4 and longer.startswith(shorter):
        return True
    return False


def _any_match(token: str, token_set: frozenset) -> bool:
    if token in token_set:
        return True
    return any(_match(token, t) for t in token_set)


def _normalize_keywords(svc) -> list[str]:
    raw = f"{svc.keywords_fr or ''},{svc.keywords_en or ''}"
    out, seen = [], set()
    for part in raw.replace("|", ",").split(","):
        k = part.strip().lower()
        if k and len(k) >= 3 and k not in seen:
            out.append(k)
            seen.add(k)
    return out


def _compute_idf(services) -> dict[str, float]:
    """IDF pondéré : 0.6 (mot générique) → 2.2 (mot unique)."""
    counter = Counter()
    for svc in services:
        for kw in set(_normalize_keywords(svc)):
            counter[kw] += 1
    n = len(services) or 1
    raw = {kw: math.log(n / (c + 1)) + 1 for kw, c in counter.items()}
    if not raw:
        return {}
    lo, hi = min(raw.values()), max(raw.values())
    span = (hi - lo) or 1
    return {kw: 0.6 + (v - lo) / span * 1.6 for kw, v in raw.items()}


def _keyword_coverage(text_lower: str, text_set: frozenset, kw: str) -> float:
    if kw in text_lower:
        return 1.0
    kw_tokens = _tokens(kw)
    if not kw_tokens:
        return 0.0
    matched = sum(1 for t in kw_tokens if _any_match(t, text_set))
    return matched / len(kw_tokens)


def _score_service(text_lower, text_set, svc, idf_map):
    title_tokens = _tokens(svc.title)
    keywords = _normalize_keywords(svc)

    service_all = set(title_tokens)
    for kw in keywords:
        for t in _tokens(kw):
            service_all.add(t)

    # 1) RECALL texte
    if text_set and service_all:
        matched_count = sum(
            1 for t in text_set if any(_match(t, s) for s in service_all)
        )
        recall = matched_count / len(text_set)
    else:
        recall = 0.0

    # 2) TITLE COVERAGE
    if title_tokens:
        title_matched = sum(1 for t in title_tokens if _any_match(t, text_set))
        title_cov = title_matched / len(title_tokens)
    else:
        title_cov = 0.0

    # 3) BEST KEYWORD pondéré par IDF (le vrai changement)
    best_weighted = 0.0
    matched_kws = []
    for kw in keywords:
        cov = _keyword_coverage(text_lower, text_set, kw)
        if cov >= 0.5:
            idf = idf_map.get(kw, 1.0)
            weighted = cov * (idf / 2.2)   # normalise 0..1
            if weighted > best_weighted:
                best_weighted = weighted
            if cov >= 0.75:
                matched_kws.append(kw)

    # 4) Combinaison : 60% best_kw + 30% recall + 10% title
    final = 0.60 * best_weighted + 0.30 * recall + 0.10 * title_cov
    return final, matched_kws


def match_services(text: str, top_k: int = 3) -> list[MatchResult]:
    from .models import Service

    if not text or not text.strip():
        return []

    services = list(Service.objects.filter(is_active=True))
    if not services:
        return []

    text_stems = _tokens(text)
    if not text_stems:
        return []
    text_set = frozenset(text_stems)
    text_lower = text.lower()
    idf_map = _compute_idf(services)

    results = []
    for svc in services:
        score, matched = _score_service(text_lower, text_set, svc, idf_map)
        reason = "matched: " + ", ".join(matched[:3]) if matched else ""
        results.append(MatchResult(service=svc, score=score, reason=reason))

    results.sort(key=lambda m: m.score, reverse=True)
    return results[:top_k]


def generate_reply(text: str, service, language: str) -> str:
    try:
        resp = _client().chat.completions.create(
            model=getattr(settings, "OPENAI_MODEL", "gpt-4o-mini"),
            messages=[{
                "role": "user",
                "content": (
                    "Tu es un commercial chaleureux et utile. Le prospect a écrit :\n"
                    f'"""{text}"""\n'
                    f"Réponds en {language}, 3-4 phrases max, en proposant : {service.title}.\n"
                    f"Inclus l'URL {service.url_comeup}. Pas de pression, sois utile."
                ),
            }],
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        logger.warning("generate_reply failed: %s", e)
        return (
            f"Bonjour, pour votre besoin je vous propose : {service.title}. "
            f"Plus d'infos : {service.url_comeup}"
        )


def recommend(text, *, min_score=None, min_confidence=None, top_k=3):
    min_score = min_score or getattr(settings, "SALESBOT_MIN_SCORE", 0.30)
    min_confidence = min_confidence or getattr(settings, "SALESBOT_MIN_CONFIDENCE", 0.50)

    if not text or len(text.strip()) < 15:
        return None

    analysis = analyze_need(text)
    if analysis.get("confidence", 0) < min_confidence:
        return None

    matches = match_services(text, top_k=top_k)
    if not matches or matches[0].score < min_score:
        return None

    best = matches[0]
    reply = generate_reply(text, best.service, analysis.get("language", "fr"))
    return Recommendation(
        service=best.service,
        score=best.score,
        confidence=analysis.get("confidence", 0),
        language=analysis.get("language", "fr"),
        intent=analysis.get("intent", "unknown"),
        reply=reply,
    )
