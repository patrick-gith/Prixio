import re

import requests

from .base import ResolvedProduct, Resolver


class GTINResolver(Resolver):
    name = "gtin"

    def can_handle(self, raw: str) -> bool:
        cleaned = re.sub(r"[^0-9]", "", raw)
        return len(cleaned) in (8, 12, 13, 14)

    def resolve(self, raw: str) -> ResolvedProduct | None:
        gtin = re.sub(r"[^0-9]", "", raw)
        try:
            r = requests.get(
                "https://api.upcitemdb.com/prod/trial/lookup",
                params={"upc": gtin},
                timeout=8,
            )
            if r.status_code != 200:
                return None
            data = r.json()
            if not data.get("items"):
                return None
            item = data["items"][0]
            return ResolvedProduct(
                canonical_type="electronics",
                primary_id=gtin,
                title=item.get("title", "—"),
                brand=item.get("brand", ""),
                image_url=(item.get("images") or [""])[0],
                attributes={"category": item.get("category", "")},
            )
        except requests.RequestException:
            return None
