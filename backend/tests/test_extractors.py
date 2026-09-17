"""Unit tests for the multi-format extraction module."""

import tempfile
import unittest
from pathlib import Path

import pymupdf as fitz
import pandas as pd

try:
    from backend.extractors import (
        ExtractedDocument,
        convert_to_markdown,
        extract_csv,
        extract_excel,
        extract_file,
        extract_markdown,
        extract_pdf,
        extract_text,
    )
except ModuleNotFoundError:
    from extractors import (
        ExtractedDocument,
        convert_to_markdown,
        extract_csv,
        extract_excel,
        extract_file,
        extract_markdown,
        extract_pdf,
        extract_text,
    )


class TestExtractors(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.base_path = Path(self.test_dir.name)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_extract_pdf(self):
        pdf_path = self.base_path / "sample_proposal.pdf"

        # Create a 2-page PDF using PyMuPDF: page 1 portrait (document), page 2 landscape (slide)
        doc = fitz.open()
        # Page 1: Portrait (595 x 842 - A4)
        p1 = doc.new_page(width=595, height=842)
        p1.insert_text(fitz.Point(50, 72), "RFP Proposal: Warehouse Automation System\nVendor: Acme Corp")

        # Page 2: Landscape / Slide (960 x 540 - 16:9)
        p2 = doc.new_page(width=960, height=540)
        p2.insert_text(fitz.Point(50, 72), "Slide 2: Architecture & Cloud Infrastructure")

        doc.set_metadata({"title": "Sample RFP Proposal", "author": "Acme Engineering"})
        doc.save(pdf_path)
        doc.close()

        # Test direct extractor
        extracted = extract_pdf(pdf_path)
        self.assertIsInstance(extracted, ExtractedDocument)
        self.assertEqual(extracted.file_type, "pdf")
        self.assertEqual(extracted.metadata["total_pages"], 2)
        self.assertEqual(extracted.metadata["title"], "Sample RFP Proposal")
        self.assertEqual(len(extracted.sections), 2)
        self.assertEqual(extracted.sections[0].name, "Page 1")
        self.assertEqual(extracted.sections[1].name, "Slide 2")
        self.assertTrue(extracted.sections[1].metadata["is_slide"])
        self.assertIn("Warehouse Automation System", extracted.raw_text)
        self.assertIn("Architecture & Cloud Infrastructure", extracted.raw_text)

        # Test autoselection via extract_file
        auto_extracted = extract_file(pdf_path)
        self.assertEqual(auto_extracted.file_type, "pdf")
        self.assertEqual(len(auto_extracted.sections), 2)

    def test_extract_excel(self):
        xlsx_path = self.base_path / "budget_plan.xlsx"

        # Create multi-sheet Excel file
        df_pricing = pd.DataFrame({
            "Item": ["Hardware", "License", "Deployment", "Support"],
            "Cost": [35000, 20000, 15000, 10000],
            "Currency": ["EUR", "EUR", "EUR", "EUR"],
        })
        df_milestones = pd.DataFrame({
            "Milestone": ["M1 Pilot", "M2 Core", "M3 Full Rollout"],
            "Month": [3, 5, 6],
            "Status": ["Planned", "Planned", "Planned"],
        })

        with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
            df_pricing.to_excel(writer, sheet_name="Pricing", index=False)
            df_milestones.to_excel(writer, sheet_name="Milestones", index=False)

        # Test direct extractor
        extracted = extract_excel(xlsx_path)
        self.assertEqual(extracted.file_type, "excel")
        self.assertEqual(len(extracted.sections), 2)
        self.assertIn("Pricing", extracted.metadata["sheet_names"])
        self.assertIn("Milestones", extracted.metadata["sheet_names"])
        self.assertIn("Hardware", extracted.raw_text)
        self.assertIn("Full Rollout", extracted.raw_text)

        # Test autoselection via extract_file
        auto_extracted = extract_file(xlsx_path)
        self.assertEqual(auto_extracted.file_type, "excel")
        self.assertEqual(auto_extracted.metadata["total_sheets"], 2)

    def test_extract_csv(self):
        csv_path = self.base_path / "inventory_levels.csv"
        df = pd.DataFrame({
            "Warehouse_ID": ["WH-01", "WH-02", "WH-03"],
            "Location": ["Munich", "Vienna", "Hamburg"],
            "Capacity_Pct": [82.5, 91.0, 74.2],
        })
        df.to_csv(csv_path, index=False)

        extracted = extract_csv(csv_path)
        self.assertEqual(extracted.file_type, "csv")
        self.assertEqual(extracted.metadata["row_count"], 3)
        self.assertIn("Munich", extracted.raw_text)
        self.assertIn("Capacity_Pct", extracted.raw_text)

        # Test autoselection
        auto_extracted = extract_file(csv_path)
        self.assertEqual(auto_extracted.file_type, "csv")

    def test_extract_markdown(self):
        md_path = self.base_path / "spec.md"
        content = (
            "# Project Title\n\n"
            "This is the project overview.\n\n"
            "## Section 1: Scope\n\n"
            "Detailed scope description.\n\n"
            "## Section 2: Requirements\n\n"
            "- Req 1\n- Req 2\n"
        )
        md_path.write_text(content, encoding="utf-8")

        extracted = extract_markdown(md_path)
        self.assertEqual(extracted.file_type, "markdown")
        self.assertGreaterEqual(len(extracted.sections), 2)
        self.assertIn("Detailed scope description", extracted.raw_text)

        # Test autoselection
        auto_extracted = extract_file(md_path)
        self.assertEqual(auto_extracted.file_type, "markdown")

    def test_extract_text(self):
        txt_path = self.base_path / "notes.txt"
        txt_path.write_text("Meeting notes:\n- Reviewed budget\n- Approved timeline", encoding="utf-8")

        extracted = extract_text(txt_path)
        self.assertEqual(extracted.file_type, "text")
        self.assertIn("Meeting notes:", extracted.raw_text)

        # Test autoselection
        auto_extracted = extract_file(txt_path)
        self.assertEqual(auto_extracted.file_type, "text")

    def test_extract_existing_repo_files(self):
        rfp_file = Path("rfp/rfp_nordframe.md")
        if rfp_file.exists():
            res = extract_file(rfp_file)
            self.assertEqual(res.file_type, "markdown")
            self.assertIn("NordFrame Logistics", res.raw_text)

        response_file = Path("response/response_1_weak.md")
        if response_file.exists():
            res = extract_file(response_file)
            self.assertEqual(res.file_type, "markdown")
            self.assertIn("BrightPath", res.raw_text)

    def test_autoselect_unsupported_file(self):
        unsupported_path = self.base_path / "archive.bin"
        unsupported_path.write_bytes(b"\x00\x01\x02\x03\x04")

        with self.assertRaises(ValueError):
            extract_file(unsupported_path)

    def test_convert_to_markdown(self):
        # 1. Test converting PDF to .md file
        pdf_path = self.base_path / "doc.pdf"
        doc = fitz.open()
        p = doc.new_page(width=595, height=842)
        p.insert_text(fitz.Point(50, 72), "Proposal Title: Cloud Optimization")
        doc.save(pdf_path)
        doc.close()

        md_output = convert_to_markdown(pdf_path)
        self.assertTrue(md_output.is_file())
        self.assertEqual(md_output.suffix, ".md")
        content = md_output.read_text(encoding="utf-8")
        self.assertIn("# doc", content)
        self.assertIn("Cloud Optimization", content)

        # 2. Test converting Excel to .md file with staging directory
        xlsx_path = self.base_path / "pricing.xlsx"
        df = pd.DataFrame({"Service": ["Consulting", "DevOps"], "Price": [5000, 8000]})
        df.to_excel(xlsx_path, sheet_name="Cost", index=False)

        staging_dir = self.base_path / "agent_workspace"
        md_excel = convert_to_markdown(xlsx_path, output_path=staging_dir)
        self.assertTrue(md_excel.is_file())
        self.assertEqual(md_excel.parent, staging_dir)
        excel_content = md_excel.read_text(encoding="utf-8")
        self.assertIn("## Sheet: Cost", excel_content)
        self.assertIn("Consulting", excel_content)

        # 3. Test when input is already a .md file (returns original path directly)
        existing_md = self.base_path / "agent_input.md"
        existing_md.write_text("# Direct Markdown for Agent", encoding="utf-8")
        retrieved_path = convert_to_markdown(existing_md)
        self.assertEqual(retrieved_path, existing_md)

    def test_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            extract_file("non_existent_file.pdf")

    def test_clean_extracted_text_symbols_and_bullets(self):
        from extractors import _clean_extracted_text

        raw = (
            "Other mini games & events:\n"
            "●\n"
            "Street Racing\n"
            "●\n"
            "Mountain Biking\n"
            "● Off-Road Race\n"
            "We have to ﬁnd the sum and use ﬁrearms.\n"
            "Here are “smart quotes” and ‘apostrophes’ – plus em—dash.\n"
            "45\n"
        )
        cleaned = _clean_extracted_text(raw)
        self.assertIn("- Street Racing", cleaned)
        self.assertIn("- Mountain Biking", cleaned)
        self.assertIn("- Off-Road Race", cleaned)
        self.assertIn("find the sum and use firearms", cleaned)
        self.assertIn('"smart quotes"', cleaned)
        self.assertIn("'apostrophes'", cleaned)
        # Standalone slide/page number 45 stripped
        self.assertNotIn("\n45\n", f"\n{cleaned}\n")

    def test_genuine_table_detection(self):
        from extractors import _is_genuine_table

        # Real table (2+ non-empty headers, concise headers)
        real_table = [
            ["Sections", "Pages"],
            ["Intro", "3"],
            ["Creativity", "4 - 16"],
        ]
        self.assertTrue(_is_genuine_table(real_table))

        # False positive: single-column slide text card
        card_box = [
            ["Hair cutting is a creative art form that requires deep dedication.", "", ""],
            ["", "1", "3"],
        ]
        self.assertFalse(_is_genuine_table(card_box))


if __name__ == "__main__":
    unittest.main()

