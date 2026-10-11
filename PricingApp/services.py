from CatalogApp.models import Product
from .models import Source, PricePoint
from .adapters import get_adapters_for


def collect_prices_for(product: Product) -> int:
    count = 0
    for adapter in get_adapters_for(product):
        fetched = adapter.fetch(product)
        if not fetched:
            continue
        source, _ = Source.objects.get_or_create(
            adapter_key=fetched.adapter_key,
            region=fetched.region,
            defaults={
                "name": fetched.source_name,
                "currency": fetched.currency,
            },
        )
        PricePoint.objects.create(
            product=product,
            source=source,
            price_local=fetched.price_local,
            currency=fetched.currency,
            in_stock=fetched.in_stock,
        )
        count += 1
    return count
