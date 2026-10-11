import re
import requests
from .base import Resolver, ResolvedProduct


class ISBNResolver(Resolver):
    name = "isbn"

    def can_handle(self, raw: str) -> bool:
        cleaned = re.sub(r"[^0-9X]", "", raw.upper())
        if len(cleaned) == 10:
            return cleaned[:9].isdigit()
        return len(cleaned) == 13 and cleaned.isdigit()

    def resolve(self, raw: str) -> ResolvedProduct | None:
        isbn = re.sub(r"[^0-9X]", "", raw.upper())
        try:
            r = requests.get(
                "https://openlibrary.org/api/books",
                params={"bibkeys": f"ISBN:{isbn}", "format": "json", "jscmd": "data"},
                timeout=8,
            )
            r.raise_for_status()
            data = r.json()
            key = f"ISBN:{isbn}"
            if key not in data:
                return None
            info = data[key]
            return ResolvedProduct(
                canonical_type="book",
                primary_id=isbn,
                title=info.get("title", "—"),
                brand=", ".join(a["name"] for a in info.get("authors", [])),
                image_url=info.get("cover", {}).get("medium", ""),
                attributes={
                    "publish_date": info.get("publish_date", ""),
                    "publishers": [p["name"] for p in info.get("publishers", [])],
                },
            )
        except requests.RequestException:
            return None
