import json
from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.http import FileResponse, HttpResponse
from django.shortcuts import redirect, render
from django.utils.translation import gettext as _
from django.views.decorators.cache import cache_control

from CatalogApp.services import get_or_create_product
from PricingApp.analysis import analyze_product
from PricingApp.services import collect_prices_for

from .forms import SearchForm

EXAMPLES = [
    {"label": "📚 Le Petit Prince", "value": "9782070408504"},
    {"label": "₿ Bitcoin", "value": "bitcoin"},
    {"label": "Ξ Ethereum", "value": "ethereum"},
    {"label": "◎ Solana", "value": "solana"},
]


def home(request):
    if request.method == "POST":
        form = SearchForm(request.POST)
        if form.is_valid():
            return redirect("CoreApp:analyze", identifier=form.cleaned_data["identifier"])
    else:
        form = SearchForm()

    return render(request, "CoreApp/home.html", {
        "form": form,
        "examples": EXAMPLES,
    })


def analyze(request, identifier: str):
    product = get_or_create_product(identifier)
    if not product:
        messages.error(
            request,
            _("Aucun produit trouvé pour « %(id)s ». Essayez un ISBN, un code-barres ou une crypto.") % {"id": identifier},
        )
        return redirect("CoreApp:home")

    collect_prices_for(product)
    analysis = analyze_product(product)

    return render(request, "CoreApp/product.html", {
        "product": product,
        "analysis": analysis,
    })



@cache_control(max_age=3600)
def manifest(request):
    """Renvoie le manifest PWA avec le bon MIME type."""
    manifest_path = Path(settings.BASE_DIR) / "static" / "manifest.webmanifest"
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return HttpResponse("{}", content_type="application/manifest+json")

    # Injecter les URLs dynamiques
    data.setdefault("start_url", "/")
    data.setdefault("scope", "/")
    return HttpResponse(
        json.dumps(data, ensure_ascii=False),
        content_type="application/manifest+json",
    )


def service_worker(request):
    """
    Sert le service-worker.js depuis la RACINE (obligatoire pour qu'il
    contrôle tout le scope du site).
    """
    sw_path = Path(settings.BASE_DIR) / "static" / "service-worker.js"
    try:
        response = FileResponse(
            open(sw_path, "rb"),
            content_type="application/javascript",
        )
        response["Service-Worker-Allowed"] = "/"
        response["Cache-Control"] = "no-cache"
        return response
    except FileNotFoundError:
        return HttpResponse("", content_type="application/javascript")