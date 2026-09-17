"""Multi-format file extraction module.

Supports:
- PDFs (Proposals, RFPs, PPTX exports) via PyMuPDF (fitz)
- Excel Spreadsheets (.xlsx, .xls) via pandas & openpyxl
- CSV files (.csv, .tsv) via pandas
- Markdown documents (.md)
- Plain text (.txt)
- Auto-selection dispatcher: `extract_file`
"""

from __future__ import annotations

import mimetypes
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Union, Tuple

import pymupdf as fitz
import pandas as pd
from pydantic import BaseModel, Field


class DocumentSection(BaseModel):
    """Represents an extracted segment (e.g., page, slide, sheet, or heading)."""
    name: str
    content: str
    page_or_sheet: Optional[Union[int, str]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExtractedDocument(BaseModel):
    """Unified container for extracted document content and metadata."""

    filename: str
    file_type: str
    raw_text: str
    sections: List[DocumentSection] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def to_markdown(
        self,
        include_metadata: bool = True,
        include_page_headers: bool = False,
    ) -> str:
        """Convert the extracted document into clean, standardized Markdown for LLMs and AI Agents.

        Args:
            include_metadata: Prepend metadata banner blockquote (source, type, pages).
            include_page_headers: If True, adds '## Page X' / '## Slide X' headers. Default False for clean data.
        """
        parts: List[str] = []

        # Document title
        title = self.metadata.get("title") or Path(self.filename).stem
        has_top_h1 = self.raw_text.lstrip().startswith("# ")

        if not (self.file_type == "markdown" and has_top_h1):
            parts.append(f"# {title}\n")

        # Metadata banner
        if include_metadata and self.metadata:
            meta_items = [f"**Source:** `{self.filename}`", f"**Type:** `{self.file_type}`"]
            if "total_pages" in self.metadata:
                meta_items.append(f"**Pages:** {self.metadata['total_pages']}")
            if "total_sheets" in self.metadata:
                meta_items.append(f"**Sheets:** {self.metadata['total_sheets']}")
            if "row_count" in self.metadata:
                meta_items.append(f"**Rows:** {self.metadata['row_count']}")
            if "author" in self.metadata and self.metadata["author"]:
                meta_items.append(f"**Author:** {self.metadata['author']}")
            parts.append(f"> {' | '.join(meta_items)}\n")

        # Body content
        if self.file_type == "markdown":
            parts.append(self.raw_text.strip())
        elif self.sections:
            for section in self.sections:
                content = section.content.strip()
                if not content:
                    continue
                # For Excel workbooks, always keep sheet names
                if self.file_type == "excel":
                    sec_header = f"## {section.name}"
                    parts.append(f"{sec_header}\n\n{content}\n")
                elif include_page_headers:
                    sec_header = f"## {section.name}"
                    parts.append(f"{sec_header}\n\n{content}\n")
                else:
                    parts.append(f"{content}\n")
        else:
            parts.append(self.raw_text.strip())

        return "\n".join(parts).strip() + "\n"

    def save_markdown(
        self,
        output_path: Union[str, Path],
        include_metadata: bool = True,
        include_page_headers: bool = False,
    ) -> Path:
        """Write the extracted content as a .md file to disk."""
        target = Path(output_path)
        if target.is_dir():
            target = target / f"{Path(self.filename).stem}.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        md_content = self.to_markdown(
            include_metadata=include_metadata,
            include_page_headers=include_page_headers,
        )
        target.write_text(md_content, encoding="utf-8")
        return target


def _read_text_with_encoding(file_path: Path) -> str:
    """Read a text file trying common encodings."""
    encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
    for enc in encodings:
        try:
            return file_path.read_text(encoding=enc)
        except (UnicodeDecodeError, LookupError):
            continue
    return file_path.read_text(encoding="utf-8", errors="replace")


def _df_to_markdown_table(df: pd.DataFrame) -> str:
    """Safely convert a pandas DataFrame to a Markdown table."""
    if df.empty:
        return "*[Empty table]*"
    try:
        return df.to_markdown(index=False)
    except Exception:
        # Fallback if tabulate is not available or encounters issues
        headers = [str(c) for c in df.columns]
        header_row = "| " + " | ".join(headers) + " |"
        sep_row = "| " + " | ".join(["---"] * len(headers)) + " |"
        body_rows = []
        for _, row in df.iterrows():
            row_str = "| " + " | ".join(str(val) if pd.notna(val) else "" for val in row) + " |"
            body_rows.append(row_str)
        return "\n".join([header_row, sep_row] + body_rows)


UNICODE_LIGATURES = {
    "ﬁ": "fi",
    "ﬂ": "fl",
    "ﬀ": "ff",
    "ﬃ": "ffi",
    "ﬄ": "ffl",
    "ﬅ": "ft",
    "ﬆ": "st",
}

TYPOGRAPHICAL_REPLACEMENTS = {
    "“": '"',
    "”": '"',
    "„": '"',
    "«": '"',
    "»": '"',
    "‘": "'",
    "’": "'",
    "‚": ",",
    "…": "...",
    "—": " -- ",
    "–": "-",
    "‒": "-",
    "―": " -- ",
    "\xa0": " ",
    "\u200b": "",
    "\u200c": "",
    "\u200d": "",
    "\ufeff": "",
}

BULLET_SYMBOLS = r"[●○■▪▫◆◇➢▶►•✓✔]"

PAGE_NUM_RE = re.compile(
    r"^\s*(?:(?:page|slide)\s*\d+(?:\s*(?:of|/)\s*\d+)?|\d+\s*[/|]\s*\d+|(?!(?:19|20)\d{2}\b)\d{1,3})\s*$",
    re.IGNORECASE,
)


def _clean_extracted_text(text: str) -> str:
    """Normalize text for LLMs: convert ligatures, quotes, bullets to markdown, strip page numbers."""
    if not text:
        return ""
    # Strip form feed and null characters
    text = text.replace("\x0c", "\n").replace("\x00", "")
    # Normalize carriage returns
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Replace ligatures
    for lig, rep in UNICODE_LIGATURES.items():
        text = text.replace(lig, rep)

    # Replace typographical quotes, dashes, and invisible characters
    for orig, rep in TYPOGRAPHICAL_REPLACEMENTS.items():
        text = text.replace(orig, rep)

    # Fix hyphenated words broken across line breaks (e.g. "con-\nfiguration" -> "configuration")
    text = re.sub(r'(\b\w+)-\n(\w+\b)', r'\1\2', text)

    # Convert bullet symbols:
    # 1. Bullet symbol alone on a line preceding text on the next line (e.g. "●\nStreet Racing" -> "- Street Racing")
    text = re.sub(r'^[ \t]*' + BULLET_SYMBOLS + r'[ \t]*\n+[ \t]*(\S)', r'- \1', text, flags=re.MULTILINE)
    # 2. Bullet symbol at the start of a line
    text = re.sub(r'^[ \t]*' + BULLET_SYMBOLS + r'[ \t]*', r'- ', text, flags=re.MULTILINE)
    # 3. Orphaned bullet symbols alone on a line
    text = re.sub(r'^[ \t]*' + BULLET_SYMBOLS + r'[ \t]*$', r'', text, flags=re.MULTILINE)

    # Filter out standalone page numbers, slide numbers, and footers
    cleaned_lines = []
    for raw_line in text.split("\n"):
        line = raw_line.strip()
        if not line:
            cleaned_lines.append("")
        elif not PAGE_NUM_RE.match(line):
            cleaned_lines.append(raw_line.rstrip())

    text = "\n".join(cleaned_lines)
    # Collapse 3 or more consecutive newlines into 2
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def _is_genuine_table(rows: List[List[Any]]) -> bool:
    """Distinguish genuine data tables from presentation shape boxes/cards."""
    if not rows or len(rows) < 2 or len(rows[0]) < 2:
        return False
    header_cells = [str(c or "").strip() for c in rows[0]]
    non_empty_headers = sum(1 for c in header_cells if c)
    if non_empty_headers < 2:
        return False
    # Table headers are concise labels, not multi-sentence paragraphs
    if any(len(c) > 80 for c in header_cells):
        return False
    total_cells = sum(len(r) for r in rows)
    filled_cells = sum(1 for r in rows for c in r if c is not None and str(c).strip())
    if total_cells == 0 or filled_cells < 4:
        return False
    return True


def _format_table_rows(rows: List[List[Any]]) -> str:
    """Convert raw table rows from PyMuPDF into a clean Markdown table."""
    if not rows or len(rows) < 2:
        return ""
    raw_header = [_clean_extracted_text(str(c or "")).replace("\n", " ") for c in rows[0]]
    seen: Dict[str, int] = {}
    headers: List[str] = []
    for idx, col in enumerate(raw_header):
        name = col.strip() or f"Col_{idx+1}"
        if name in seen:
            seen[name] += 1
            name = f"{name}_{seen[name]}"
        else:
            seen[name] = 1
        headers.append(name)

    body_rows = []
    for r in rows[1:]:
        cleaned_row = [_clean_extracted_text(str(c or "")).replace("\n", " ").strip() for c in r]
        # Skip completely empty rows
        if not any(cleaned_row):
            continue
        if len(cleaned_row) < len(headers):
            cleaned_row += [""] * (len(headers) - len(cleaned_row))
        body_rows.append(cleaned_row[:len(headers)])

    if not body_rows:
        return ""
    df = pd.DataFrame(body_rows, columns=headers)
    return _df_to_markdown_table(df)


def _bbox_overlaps_table(block_bbox: Tuple[float, float, float, float], table_bbox: Tuple[float, float, float, float]) -> bool:
    """Check if the midpoint of a text block falls inside a table bounding box."""
    cx = (block_bbox[0] + block_bbox[2]) / 2.0
    cy = (block_bbox[1] + block_bbox[3]) / 2.0
    return (table_bbox[0] <= cx <= table_bbox[2]) and (table_bbox[1] <= cy <= table_bbox[3])


def extract_pdf(file_path: Union[str, Path]) -> ExtractedDocument:
    """Extract text, tables, and metadata from a PDF file using PyMuPDF (fitz).

    Handles standard multi-page documents (RFPs, proposals) and slide decks (PPTX exports).
    Converts genuine tables into Markdown tables without text duplication,
    normalizes symbols and ligatures, and strips page numbers.
    """
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"PDF file not found: {path}")

    # Detect corrupted binary PDFs (e.g. downloaded as text instead of binary)
    raw_head = path.read_bytes()
    replacement_count = raw_head.count(b"\xef\xbf\xbd")
    if replacement_count > 100:
        raise ValueError(
            f"Corrupted PDF file '{path.name}': Detected {replacement_count:,} Unicode replacement bytes (\\xef\\xbf\\xbd). "
            f"This happens when a binary PDF is downloaded, copied, or saved as text (e.g. response.text instead of response.content)."
        )

    doc = fitz.open(path)
    sections: List[DocumentSection] = []
    text_blocks: List[str] = []

    try:
        total_pages = len(doc)
        pdf_metadata = doc.metadata or {}

        for page_idx in range(total_pages):
            page = doc[page_idx]
            page_num = page_idx + 1

            # Detect if page is likely a slide (landscape orientation or aspect ratio > 1.2)
            rect = page.rect
            is_slide = rect.width > rect.height * 1.15
            label = f"Slide {page_num}" if is_slide else f"Page {page_num}"

            # Check for genuine tables on this page
            genuine_tables: List[Tuple[Any, str]] = []
            try:
                tables = page.find_tables()
                for t in tables:
                    extracted_rows = t.extract()
                    if _is_genuine_table(extracted_rows):
                        table_md = _format_table_rows(extracted_rows)
                        if table_md:
                            genuine_tables.append((t.bbox, table_md))
            except Exception:
                genuine_tables = []

            if genuine_tables:
                # Merge non-table text blocks and genuine tables in vertical reading order
                page_items: List[Tuple[float, str]] = []
                blocks = page.get_text("blocks")
                for b in blocks:
                    if b[6] != 0:  # ignore non-text blocks (images)
                        continue
                    in_table = any(_bbox_overlaps_table(b[:4], tb[0]) for tb in genuine_tables)
                    if not in_table:
                        txt = _clean_extracted_text(b[4])
                        if txt:
                            page_items.append((b[1], txt))

                for tb in genuine_tables:
                    page_items.append((tb[0][1], tb[1]))

                page_items.sort(key=lambda x: x[0])
                page_text = "\n\n".join(item[1] for item in page_items).strip()
            else:
                page_text = _clean_extracted_text(page.get_text("text"))

            section = DocumentSection(
                name=label,
                content=page_text,
                page_or_sheet=page_num,
                metadata={
                    "width": round(rect.width, 2),
                    "height": round(rect.height, 2),
                    "is_slide": is_slide,
                    "tables_found": len(genuine_tables),
                },
            )
            sections.append(section)

            header = f"--- {label} ---"
            text_blocks.append(f"{header}\n{page_text}" if page_text else f"{header}\n[No text]")

        raw_text = "\n\n".join(text_blocks)

        metadata: Dict[str, Any] = {
            "total_pages": total_pages,
            "title": pdf_metadata.get("title") or path.stem,
            "author": pdf_metadata.get("author") or "",
            "subject": pdf_metadata.get("subject") or "",
            "creator": pdf_metadata.get("creator") or "",
            "producer": pdf_metadata.get("producer") or "",
            "file_size_bytes": path.stat().st_size,
        }

        return ExtractedDocument(
            filename=path.name,
            file_type="pdf",
            raw_text=raw_text,
            sections=sections,
            metadata=metadata,
        )
    finally:
        doc.close()


def extract_excel(file_path: Union[str, Path]) -> ExtractedDocument:
    """Extract all sheets from an Excel (.xlsx, .xls) workbook using pandas."""
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Excel file not found: {path}")

    sections: List[DocumentSection] = []
    text_blocks: List[str] = []

    excel_file = pd.ExcelFile(path, engine="openpyxl")
    try:
        sheet_names = excel_file.sheet_names
        sheet_summaries: Dict[str, Any] = {}

        for sheet_name in sheet_names:
            df = pd.read_excel(excel_file, sheet_name=sheet_name)
            # Drop rows and columns that are entirely NaN
            df = df.dropna(how="all").dropna(axis=1, how="all")

            md_table = _df_to_markdown_table(df)

            section = DocumentSection(
                name=f"Sheet: {sheet_name}",
                content=md_table,
                page_or_sheet=sheet_name,
                metadata={
                    "row_count": len(df),
                    "column_count": len(df.columns),
                    "columns": [str(c) for c in df.columns],
                },
            )
            sections.append(section)

            sheet_block = f"## Sheet: {sheet_name}\n\n{md_table}"
            text_blocks.append(sheet_block)
            sheet_summaries[sheet_name] = {"rows": len(df), "columns": len(df.columns)}

        raw_text = "\n\n".join(text_blocks)

        return ExtractedDocument(
            filename=path.name,
            file_type="excel",
            raw_text=raw_text,
            sections=sections,
            metadata={
                "sheet_names": sheet_names,
                "total_sheets": len(sheet_names),
                "sheets": sheet_summaries,
                "file_size_bytes": path.stat().st_size,
            },
        )
    finally:
        excel_file.close()


def extract_csv(file_path: Union[str, Path]) -> ExtractedDocument:
    """Extract tabular data from a CSV/TSV file using pandas."""
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"CSV file not found: {path}")

    # Read CSV with pandas, sniffing delimiter automatically with python engine
    try:
        df = pd.read_csv(path, sep=None, engine="python")
    except Exception:
        # Fallback to standard comma delimiter
        df = pd.read_csv(path)

    df = df.dropna(how="all").dropna(axis=1, how="all")
    md_table = _df_to_markdown_table(df)

    section = DocumentSection(
        name=path.stem,
        content=md_table,
        page_or_sheet=1,
        metadata={
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": [str(c) for c in df.columns],
        },
    )

    raw_text = f"# {path.stem}\n\n{md_table}"

    return ExtractedDocument(
        filename=path.name,
        file_type="csv",
        raw_text=raw_text,
        sections=[section],
        metadata={
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": [str(c) for c in df.columns],
            "file_size_bytes": path.stat().st_size,
        },
    )


def extract_markdown(file_path: Union[str, Path]) -> ExtractedDocument:
    """Extract content and sections from a Markdown (.md) file."""
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Markdown file not found: {path}")

    text = _read_text_with_encoding(path)
    sections: List[DocumentSection] = []

    # Split into sections based on top-level headers (# or ##)
    header_pattern = re.compile(r"^(#{1,3}\s+.+)$", re.MULTILINE)
    splits = header_pattern.split(text)

    if len(splits) > 1:
        # First split might be preamble before the first header
        preamble = splits[0].strip()
        if preamble:
            sections.append(
                DocumentSection(
                    name="Preamble",
                    content=preamble,
                    page_or_sheet=0,
                )
            )

        for i in range(1, len(splits), 2):
            header = splits[i].strip()
            content = splits[i + 1].strip() if i + 1 < len(splits) else ""
            title = header.lstrip("#").strip()
            sections.append(
                DocumentSection(
                    name=title,
                    content=f"{header}\n\n{content}".strip(),
                    page_or_sheet=len(sections) + 1,
                )
            )
    else:
        sections.append(
            DocumentSection(
                name="Document",
                content=text.strip(),
                page_or_sheet=1,
            )
        )

    return ExtractedDocument(
        filename=path.name,
        file_type="markdown",
        raw_text=text,
        sections=sections,
        metadata={
            "section_count": len(sections),
            "character_count": len(text),
            "line_count": len(text.splitlines()),
            "file_size_bytes": path.stat().st_size,
        },
    )


def extract_text(file_path: Union[str, Path]) -> ExtractedDocument:
    """Extract content from a plain text (.txt) file."""
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Text file not found: {path}")

    text = _clean_extracted_text(_read_text_with_encoding(path))

    section = DocumentSection(
        name="Document",
        content=text.strip(),
        page_or_sheet=1,
    )

    return ExtractedDocument(
        filename=path.name,
        file_type="text",
        raw_text=text,
        sections=[section],
        metadata={
            "character_count": len(text),
            "line_count": len(text.splitlines()),
            "file_size_bytes": path.stat().st_size,
        },
    )


def extract_file(file_path: Union[str, Path]) -> ExtractedDocument:
    """Autoselect the appropriate extractor based on file type and extract content.

    Supported formats:
    - PDF: .pdf (proposals, RFPs, PPTX exports)
    - Excel: .xlsx, .xls, .xlsm
    - CSV / TSV: .csv, .tsv
    - Markdown: .md, .markdown
    - Plain text: .txt, .log, .text

    Args:
        file_path: Path to the target file.

    Returns:
        ExtractedDocument containing normalized raw_text, structured sections, and metadata.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file type is unsupported.
    """
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"File not found: {path}")

    suffix = path.suffix.lower()

    # Route by extension
    if suffix == ".pdf":
        return extract_pdf(path)
    elif suffix in (".xlsx", ".xls", ".xlsm"):
        return extract_excel(path)
    elif suffix in (".csv", ".tsv"):
        return extract_csv(path)
    elif suffix in (".md", ".markdown"):
        return extract_markdown(path)
    elif suffix in (".txt", ".log", ".text"):
        return extract_text(path)

    # Fallback to magic byte / header detection if extension is ambiguous or missing
    with open(path, "rb") as f:
        header_bytes = f.read(16)

    if header_bytes.startswith(b"%PDF"):
        return extract_pdf(path)
    if header_bytes.startswith(b"PK\x03\x04"):  # ZIP-based format (e.g. xlsx)
        try:
            return extract_excel(path)
        except Exception:
            pass

    # MIME type fallback
    mime_type, _ = mimetypes.guess_type(path)
    if mime_type:
        if "pdf" in mime_type:
            return extract_pdf(path)
        if "excel" in mime_type or "spreadsheet" in mime_type:
            return extract_excel(path)
        if "csv" in mime_type:
            return extract_csv(path)
        if "text" in mime_type:
            return extract_text(path)

    supported = [".pdf", ".xlsx", ".xls", ".xlsm", ".csv", ".tsv", ".md", ".markdown", ".txt"]
    raise ValueError(
        f"Unsupported file format '{suffix}' for file: {path.name}. Supported extensions: {', '.join(supported)}"
    )


def convert_to_markdown(
    file_path: Union[str, Path],
    output_path: Optional[Union[str, Path]] = None,
    include_metadata: bool = True,
    include_page_headers: bool = False,
) -> Path:
    """Parse any document (PDF, Excel, CSV, TXT, MD) and retrieve a clean .md file for an AI Agent.

    Args:
        file_path: Path to the input file (e.g. proposal.pdf, pricing.xlsx, spec.md).
        output_path: Target .md file path or directory.
                     - If None and input is already .md, returns original file directly.
                     - If None and input is non-markdown, defaults to <input_stem>.md in the same directory.
                     - If a directory, saves as <output_dir>/<input_stem>.md.
                     - If a file path, saves to that exact path.
        include_metadata: Whether to include the metadata banner blockquote (default: True).
        include_page_headers: Whether to include '## Page X' / '## Slide X' headers (default: False for clean data).

    Returns:
        Path: Path to the generated or existing Markdown (.md) file.
    """
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"File not found: {path}")

    # If already markdown and no custom destination requested, reuse directly
    if path.suffix.lower() in (".md", ".markdown") and output_path is None:
        return path

    doc = extract_file(path)

    if output_path is None:
        target = path.with_suffix(".md")
    else:
        target = Path(output_path)
        if target.is_dir() or not target.suffix:
            target = target / f"{path.stem}.md"

    return doc.save_markdown(
        target,
        include_metadata=include_metadata,
        include_page_headers=include_page_headers,
    )


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: uv run python extractors.py <file_path> [--save]")
        print("Examples:")
        print("  uv run python extractors.py rfp/rfp_nordframe.md")
        print("  uv run python extractors.py proposal.pdf --save")
        sys.exit(1)

    target_file = sys.argv[1]
    save_flag = "--save" in sys.argv

    print(f"\n📂 Inspecting file extraction: {target_file}")
    print("=" * 60)

    try:
        doc = extract_file(target_file)
        print(f"✅ Detected Type:  {doc.file_type.upper()}")
        print(f"📄 Total Sections: {len(doc.sections)}")
        print(f"📊 Metadata:       {doc.metadata}")
        print("-" * 60)
        print("📑 Sections / Pages / Sheets:")
        for idx, sec in enumerate(doc.sections, 1):
            preview = sec.content.strip().splitlines()[0] if sec.content.strip() else "[Empty]"
            print(f"  {idx}. [{sec.name}] -> {preview[:70]}...")

        print("-" * 60)
        print("📝 Converted Markdown Preview (first 500 chars):")
        md_text = doc.to_markdown()
        print(md_text[:500] + ("..." if len(md_text) > 500 else ""))
        print("=" * 60)

        if save_flag:
            out_file = convert_to_markdown(target_file)
            print(f"💾 Saved .md file to: {out_file}\n")
    except Exception as err:
        print(f"❌ Extraction error: {err}\n")



