"""Parser CSV — détecte automatiquement le séparateur et l'encoding."""
import csv
import io
from pathlib import Path

from .base import ParserBase, ParsedFile, ParsedRow


class CSVParser(ParserBase):
    format = "csv"

    def parse(self, path: str | Path) -> ParsedFile:
        # Détection encoding
        raw = Path(path).read_bytes()
        encoding = self._detect_encoding(raw)
        text = raw.decode(encoding, errors="replace")

        # Détection séparateur
        sample = text[:4096]
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
            delimiter = dialect.delimiter
        except csv.Error:
            delimiter = ","
            if sample.count(";") > sample.count(","):
                delimiter = ";"

        reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
        columns = [c.strip() for c in (reader.fieldnames or [])]
        rows = []
        for i, row in enumerate(reader, start=1):
            cleaned = {(k or "").strip(): (v or "").strip() for k, v in row.items()}
            rows.append(ParsedRow(row_number=i, raw=cleaned))

        warnings = []
        if not columns:
            warnings.append("Aucune colonne détectée.")
        return ParsedFile(columns=columns, rows=rows, format=self.format, warnings=warnings)

    @staticmethod
    def _detect_encoding(raw: bytes) -> str:
        for enc in ("utf-8-sig", "utf-8", "latin-1", "cp1252"):
            try:
                raw.decode(enc)
                return enc
            except UnicodeDecodeError:
                continue
        return "utf-8"