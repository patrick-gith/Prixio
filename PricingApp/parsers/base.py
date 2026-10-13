"""Contrat commun à tous les parsers."""
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ParsedRow:
    """Une ligne extraite d'un fichier, avant normalisation."""
    row_number: int
    raw: dict                # toutes les colonnes/valeurs brutes


@dataclass
class ParsedFile:
    """Résultat d'un parsing : colonnes + lignes."""
    columns: list[str]
    rows: list[ParsedRow]
    format: str
    warnings: list[str] = field(default_factory=list)

    @property
    def row_count(self) -> int:
        return len(self.rows)


class ParserBase:
    """Classe mère. Chaque parser implémente `parse()`."""

    format = "base"

    def parse(self, path: str | Path) -> ParsedFile:
        raise NotImplementedError