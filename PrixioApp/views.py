# PrixioApp/views.py
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _
from CatalogApp.models import Product
from PricingApp.models import Alert, Watchlist
from PricingApp.analysis import analyze_product
from PricingApp.services import collect_prices_for
from django.contrib.auth import login as auth_login
from .forms import RegisterForm

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
        "best_saving": max(
            (o["deviation_pct"] for o in opportunities), default=0
        ),
    }

    return render(request, "PrixioApp/dashboard.html", {
        "opportunities": opportunities[:6],
        "alerts": alerts_qs,
        "stats": stats,
    })


@login_required
def add_to_watchlist(request, product_id: int):
    product = get_object_or_404(Product, pk=product_id)
    _, created = Watchlist.objects.get_or_create(user=request.user, product=product)

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

    # Redirection sûre : n'accepter que le referer interne
    next_url = request.META.get("HTTP_REFERER")
    if next_url and next_url.startswith(request.build_absolute_uri("/")):
        return redirect(next_url)
    return redirect("PrixioApp:dashboard")


@login_required
def remove_from_watchlist(request, product_id: int):
    product = get_object_or_404(Product, pk=product_id)
    Watchlist.objects.filter(user=request.user, product=product).delete()
    messages.info(
        request,
        _("« %(title)s » retiré de votre veille.") % {"title": product.title},
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


@login_required
def alerts(request):
    qs = (
        Alert.objects
        .filter(user=request.user)
        .select_related("product")
        .order_by("-created_at")
    )
    # Marquer tout comme lu
    qs.filter(is_read=False).update(is_read=True)
    return render(request, "PrixioApp/alerts.html", {"alerts": qs})


@login_required
def refresh_all(request):
    watchlists = Watchlist.objects.filter(user=request.user).select_related("product")
    for w in watchlists:
        collect_prices_for(w.product)
    messages.success(request, _("Tous les prix ont été actualisés."))
    return redirect("PrixioApp:dashboard")