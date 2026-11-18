import csv
import json
import tempfile
import unittest
from pathlib import Path

from dataset_doctor import profile_csv, render_markdown


class DatasetDoctorTests(unittest.TestCase):
    def write_csv(self, content):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "sample.csv"
        path.write_text(content, encoding="utf-8")
        return path

    def test_profiles_missing_duplicates_and_numeric_columns(self):
        path = self.write_csv(
            "name,score\nAri,10\nBea,11\nCy,\nCy,\n"
        )
        report = profile_csv(path)
        self.assertEqual(report["row_count"], 4)
        self.assertEqual(report["column_count"], 2)
        self.assertEqual(report["duplicate_row_count"], 1)
        self.assertEqual(report["missing_cell_count"], 2)
        score = report["columns"][1]
        self.assertEqual(score["type"], "numeric")
        self.assertEqual(score["numeric"]["mean"], 10.5)

    def test_counts_malformed_rows_without_silently_shifting_columns(self):
        path = self.write_csv("a,b\n1,2\n3\n4,5,6\n7,8\n")
        report = profile_csv(path)
        self.assertEqual(report["row_count"], 2)
        self.assertEqual(report["malformed_row_count"], 2)
        self.assertEqual(report["columns"][0]["unique_count"], 2)

    def test_detects_semicolon_delimiter_and_utf8_bom(self):
        path = self.write_csv("\ufeffcity;population\nKolkata;500\nDelhi;700\n")
        report = profile_csv(path)
        self.assertEqual(report["delimiter"], ";")
        self.assertEqual(report["column_count"], 2)

    def test_explicit_delimiter_is_supported(self):
        path = self.write_csv("a|b\n1|2\n")
        self.assertEqual(profile_csv(path, delimiter="|")["row_count"], 1)
        with self.assertRaisesRegex(ValueError, "one character"):
            profile_csv(path, delimiter="||")

    def test_rejects_empty_and_ambiguous_headers(self):
        empty = self.write_csv("")
        with self.assertRaisesRegex(ValueError, "empty"):
            profile_csv(empty)
        duplicate = self.write_csv("a,a\n1,2\n")
        with self.assertRaisesRegex(ValueError, "duplicate"):
            profile_csv(duplicate)
        blank = self.write_csv("a,\n1,2\n")
        with self.assertRaisesRegex(ValueError, "non-empty"):
            profile_csv(blank)

    def test_numeric_outlier_count_is_a_review_signal(self):
        path = self.write_csv("value\n1\n2\n3\n4\n100\n")
        numeric = profile_csv(path)["columns"][0]["numeric"]
        self.assertEqual(numeric["iqr_outlier_count"], 1)

    def test_report_is_json_serializable_and_markdown_is_readable(self):
        report = profile_csv(self.write_csv("city\nKolkata\n"))
        self.assertIn('"row_count": 1', json.dumps(report))
        markdown = render_markdown(report)
        self.assertIn("# Dataset quality report", markdown)
        self.assertIn("IQR outliers", markdown)


if __name__ == "__main__":
    unittest.main()
