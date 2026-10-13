# PrixioApp/views.py
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST
import os
from django.views.decorators.http import require_POST
from PricingApp import telegram_service
from CatalogApp.models import Product
from PricingApp.models import Alert, Watchlist
from PricingApp.analysis import analyze_product
from PricingApp.services import collect_prices_for

from .forms import RegisterForm


# ==========================================================
# AUTHENTIFICATION
# ==========================================================

def register(request):
    """Inscription utilisateur. Pas de modèle custom — UserCreationForm suffit."""
    if request.user.is_authenticated:
        return redirect("PrixioApp:dashboard")

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            messages.success(
                request,
                _("Bienvenue %(name)s ! Votre compte est créé.") % {"name": user.username},
            )
            return redirect("PrixioApp:dashboard")
    else:
        form = RegisterForm()

    return render(request, "registration/register.html", {"form": form})


# ==========================================================
# DASHBOARD
# ==========================================================

@login_required
def dashboard(request):
    watchlists = (
        Watchlist.objects
        .filter(user=request.user)
        .select_related("product")
        .order_by("-created_at")
    )

    opportunities = []
    for w in watchlists:
        analysis = analyze_product(w.product)
        if analysis.get("has_data"):
            opportunities.append({
                "product": w.product,
                "score": analysis["score"],
                "label": analysis["label"],
                "current": analysis["current_price"],
                "currency": analysis["currency"],
                "baseline": analysis["baseline"].get("median", 0),
                "deviation_pct": analysis["deviation_pct"],
            })

    opportunities.sort(key=lambda o: o["score"], reverse=True)

    alerts_qs = (
        Alert.objects
        .filter(user=request.user)
        .select_related("product")
        .order_by("-created_at")[:10]
    )

    stats = {
        "watchlist_count": watchlists.count(),
        "alerts_count": Alert.objects.filter(user=request.user, is_read=False).count(),
        "avg_score": round(
            sum(o["score"] for o in opportunities) / len(opportunities), 1
        ) if opportunities else 0,
        # Ne garder que les économies positives (prix sous la baseline)
        "best_saving": max(
            (o["deviation_pct"] for o in opportunities if o["deviation_pct"] > 0),
            default=0,
        ),
    }

    return render(request, "PrixioApp/dashboard.html", {
        "opportunities": opportunities[:6],
        "alerts": alerts_qs,
        "stats": stats,
    })


# ==========================================================
# WATCHLIST
# ==========================================================

@login_required
def add_to_watchlist(request, product_id: int):
    product = get_object_or_404(Product, pk=product_id)

    # ⚠️ Ne JAMAIS utiliser `_` comme variable jetable dans un fichier
    # qui utilise `_` pour la traduction. Sinon `_` devient un Watchlist
    # et `_("...")` plante avec "'Watchlist' object is not callable".
    item, created = Watchlist.objects.get_or_create(
        user=request.user,
        product=product,
    )

    if created:
        messages.success(
            request,
            _("« %(title)s » ajouté à votre veille.") % {"title": product.title},
        )
    else:
        messages.info(
            request,
            _("« %(title)s » est déjà dans votre veille.") % {"title": product.title},
        )

    # Redirection : on préfère `?next=` au referer (plus fiable, plus sûr).
    # Le referer reste en fallback pour ne pas casser les liens existants.
    next_url = request.GET.get("next")
    if next_url and next_url.startswith("/") and not next_url.startswith("//"):
        return redirect(next_url)

    referer = request.META.get("HTTP_REFERER")
    if referer and referer.startswith(request.build_absolute_uri("/")):
        return redirect(referer)

    return redirect("PrixioApp:dashboard")


@login_required
def remove_from_watchlist(request, product_id: int):
    product = get_object_or_404(Product, pk=product_id)

    deleted, _count = Watchlist.objects.filter(
        user=request.user, product=product,
    ).delete()

    # Réponse JSON si requête AJAX (swipe)
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    if is_ajax:
        from django.http import JsonResponse
        return JsonResponse({
            "ok": True,
            "deleted": deleted,
            "product": product.title,
        })

    if deleted:
        messages.info(
            request,
            _("« %(title)s » retiré de votre veille.") % {"title": product.title},
        )
    else:
        messages.warning(
            request,
            _("« %(title)s » n'était pas dans votre veille.") % {"title": product.title},
        )

    return redirect("PrixioApp:dashboard")


@login_required
def watchlist(request):
    items = (
        Watchlist.objects
        .filter(user=request.user)
        .select_related("product")
        .order_by("-created_at")
    )
    return render(request, "PrixioApp/watchlist.html", {"items": items})


# ==========================================================
# ALERTES
# ==========================================================

@login_required
def alerts(request):
    qs = (
        Alert.objects
        .filter(user=request.user)
        .select_related("product")
        .order_by("-created_at")
    )

    # On ne marque comme lues QUE celles qui ne le sont pas encore,
    # pour éviter un UPDATE inutile à chaque visite.
    unread_ids = list(qs.filter(is_read=False).values_list("id", flat=True))
    if unread_ids:
        Alert.objects.filter(id__in=unread_ids).update(is_read=True)

    return render(request, "PrixioApp/alerts.html", {"alerts": qs})


# ==========================================================
# RAFRAÎCHISSEMENT DES PRIX
# ==========================================================
@login_required
@require_POST
def refresh_all(request):
    """Rafraîchit tous les produits suivis (parallélisé)."""
    watchlists = (
        Watchlist.objects
        .filter(user=request.user)
        .select_related("product")
    )

    refreshed = 0
    for w in watchlists:
        try:
            result = collect_prices_for(w.product)
            if result.created:
                refreshed += 1
        except Exception as exc:  # noqa: BLE001
            messages.warning(
                request,
                _("Impossible d'actualiser « %(title)s » : %(err)s")
                % {"title": w.product.title, "err": str(exc)},
            )

    if refreshed:
        messages.success(
            request,
            _("%(n)s produit(s) actualisé(s).") % {"n": refreshed},
        )
    else:
        messages.info(request, _("Aucun changement de prix détecté."))

    return redirect("PrixioApp:dashboard")





@login_required
def telegram_link(request):
    from django.core.cache import cache
    cache.set(f"telegram_code:{code}", request.user.id, timeout=600)
    """Affiche un code à coller dans le bot Telegram."""
    profile = getattr(request.user, "prixio_profile", None)
    if not profile:
        from .models import UserProfile
        profile = UserProfile.objects.create(user=request.user)

    # Code éphémère : on le régénère à chaque visite
    code = telegram_service.generate_link_code()
    request.session["telegram_link_code"] = code
    request.session.set_expiry(600)   # 10 min

    bot_username = os.environ.get("TELEGRAM_BOT_USERNAME", "")
    deep_link = f"https://t.me/{bot_username}?start={code}" if bot_username else ""

    return render(request, "PrixioApp/telegram_link.html", {
        "code": code,
        "deep_link": deep_link,
        "linked": bool(profile.telegram_chat_id),
        "telegram_configured": telegram_service.is_configured(),
    })


@login_required
@require_POST
def telegram_unlink(request):
    profile = getattr(request.user, "prixio_profile", None)
    if profile:
        profile.telegram_chat_id = ""
        profile.save(update_fields=["telegram_chat_id"])
    messages.info(request, _("Telegram déconnecté."))
    return redirect("PrixioApp:telegram_link")