"""Parser PDF — extrait les tableaux avec pdfplumber."""
from pathlib import Path

from .base import ParserBase, ParsedFile, ParsedRow


class PDFParser(ParserBase):
    format = "pdf"

    def parse(self, path: str | Path) -> ParsedFile:
        try:
            import pdfplumber
        except ImportError:
            raise ImportError("Installe pdfplumber : pip install pdfplumber")

        warnings = []
        all_tables = []

        with pdfplumber.open(str(path)) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                tables = page.extract_tables() or []
                for t_idx, table in enumerate(tables):
                    if len(table) < 2:
                        continue
                    all_tables.append((page_num, t_idx, table))

            # Fallback : pas de tableaux détectés → extraction texte ligne par ligne
            if not all_tables:
                warnings.append("Aucun tableau détecté — extraction texte brut.")
                rows = []
                row_n = 0
                for page in pdf.pages:
                    text = page.extract_text() or ""
                    for line in text.splitlines():
                        line = line.strip()
                        if not line:
                            continue
                        row_n += 1
                        rows.append(ParsedRow(row_number=row_n, raw={"Texte": line}))
                return ParsedFile(
                    columns=["Texte"], rows=rows,
                    format=self.format, warnings=warnings,
                )

        # Utiliser le premier tableau trouvé comme référence
        _, _, main_table = max(all_tables, key=lambda x: len(x[2]))
        header = main_table[0]
        columns = [self._clean(c) or f"Col_{i+1}" for i, c in enumerate(header)]

        rows = []
        row_n = 0
        for _, _, table in all_tables:
            body = table[1:] if table is main_table else table
            for raw in body:
                if all(self._clean(c) == "" for c in raw):
                    continue
                row_n += 1
                row_dict = {}
                for j, val in enumerate(raw):
                    col = columns[j] if j < len(columns) else f"Col_{j+1}"
                    row_dict[col] = self._clean(val)
                rows.append(ParsedRow(row_number=row_n, raw=row_dict))

        return ParsedFile(columns=columns, rows=rows, format=self.format, warnings=warnings)

    @staticmethod
    def _clean(value) -> str:
        if value is None:
            return ""
        return str(value).replace("\n", " ").strip()