import json
import tempfile
import unittest
from pathlib import Path

from dataset_doctor.cli import main


class CliTests(unittest.TestCase):
    def test_json_output_to_file(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "input.csv"
            output = Path(folder) / "report.json"
            source.write_text("a\n1\n2\n", encoding="utf-8")
            status = main([str(source), "--format", "json", "--output", str(output)])
            self.assertEqual(status, 0)
            data = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(data["row_count"], 2)

    def test_missing_input_returns_nonzero(self):
        self.assertEqual(main(["/definitely/not/a/real/file.csv"]), 2)


if __name__ == "__main__":
    unittest.main()
