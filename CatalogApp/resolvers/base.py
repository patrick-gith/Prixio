from dataclasses import dataclass, field
from typing import Any


@dataclass
class ResolvedProduct:
    canonical_type: str
    primary_id: str
    title: str
    brand: str = ""
    image_url: str = ""
    attributes: dict[str, Any] = field(default_factory=dict)


class Resolver:
    name = "base"

    def can_handle(self, raw: str) -> bool:
        raise NotImplementedError

    def resolve(self, raw: str) -> ResolvedProduct | None:
        raise NotImplementedError
