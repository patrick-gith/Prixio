"""Parsers multi-format pour l'import batch."""
from pathlib import Path

from .csv_parser import CSVParser
from .excel_parser import ExcelParser
from .pdf_parser import PDFParser
from .word_parser import WordParser


PARSERS = {
    "csv":  CSVParser,
    "xlsx": ExcelParser,
    "xls":  ExcelParser,
    "pdf":  PDFParser,
    "docx": WordParser,
    "doc":  WordParser,
}


def get_parser(path: str | Path):
    ext = Path(path).suffix.lower().lstrip(".")
    cls = PARSERS.get(ext)
    if not cls:
        raise ValueError(f"Format non supporté : .{ext}")
    return cls()


SUPPORTED_EXTENSIONS = list(PARSERS.keys())