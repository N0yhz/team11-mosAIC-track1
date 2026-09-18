"""Document extractors module for multi-format document parsing.

Supports:
- PDF (.pdf) via PyMuPDF (fitz)
- Excel (.xlsx, .xls, .xlsm) via pandas & openpyxl
- CSV / TSV (.csv, .tsv) via pandas
- Markdown (.md, .markdown)
- Plain text (.txt, .log, .text)
"""

from .extractor import (
    DocumentSection,
    ExtractedDocument,
    convert_to_markdown,
    extract_csv,
    extract_excel,
    extract_file,
    extract_markdown,
    extract_pdf,
    extract_text,
)

__all__ = [
    "DocumentSection",
    "ExtractedDocument",
    "convert_to_markdown",
    "extract_csv",
    "extract_excel",
    "extract_file",
    "extract_markdown",
    "extract_pdf",
    "extract_text",
]
