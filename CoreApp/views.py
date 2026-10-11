from django.contrib import messages
from django.shortcuts import redirect, render
from django.utils.translation import gettext as _

from CatalogApp.services import get_or_create_product
from PricingApp.services import collect_prices_for
from PricingApp.analysis import analyze_product

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