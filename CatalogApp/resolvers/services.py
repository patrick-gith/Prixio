from .models import Product
from .resolvers import resolve as raw_resolve


def get_or_create_product(raw_identifier: str) -> Product | None:
    resolved = raw_resolve(raw_identifier)
    if not resolved:
        return None
    product, _ = Product.objects.update_or_create(
        primary_id=resolved.primary_id,
        defaults={
            "canonical_type": resolved.canonical_type,
            "title": resolved.title,
            "brand": resolved.brand,
            "image_url": resolved.image_url,
            "attributes": resolved.attributes,
        },
    )
    return product