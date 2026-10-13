"""Parser Excel (.xlsx / .xls) avec openpyxl."""
from pathlib import Path

from .base import ParserBase, ParsedFile, ParsedRow


class ExcelParser(ParserBase):
    format = "xlsx"

    def parse(self, path: str | Path) -> ParsedFile:
        try:
            from openpyxl import load_workbook
        except ImportError:
            raise ImportError("Installe openpyxl : pip install openpyxl")

        wb = load_workbook(filename=str(path), read_only=True, data_only=True)
        sheet = wb.active

        rows_iter = sheet.iter_rows(values_only=True)
        try:
            header = next(rows_iter)
        except StopIteration:
            return ParsedFile(columns=[], rows=[], format=self.format,
                              warnings=["Fichier vide."])

        columns = [self._clean_cell(c) or f"Col_{i+1}" for i, c in enumerate(header)]

        rows = []
        for i, raw in enumerate(rows_iter, start=1):
            if all(self._clean_cell(c) == "" for c in raw):
                continue  # ligne vide
            row_dict = {}
            for j, val in enumerate(raw):
                col = columns[j] if j < len(columns) else f"Col_{j+1}"
                row_dict[col] = self._clean_cell(val)
            rows.append(ParsedRow(row_number=i, raw=row_dict))

        wb.close()
        return ParsedFile(columns=columns, rows=rows, format=self.format)

    @staticmethod
    def _clean_cell(value) -> str:
        if value is None:
            return ""
        return str(value).strip()