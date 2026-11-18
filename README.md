# Dataset Doctor

A dependency-free CSV profiler that turns a raw dataset into a quick, reproducible quality report.

## Features

- Detects comma, semicolon, tab, or pipe delimiters (or accepts one explicitly).
- Reports missing cells, duplicate rows, and malformed records.
- Profiles text and fully numeric columns separately.
- Calculates numeric mean, median, range, quartiles, and IQR outlier candidates.
- Exports readable Markdown or machine-readable JSON.
- Uses only the Python standard library at runtime.

> This is a descriptive data-quality helper. An IQR outlier is a review candidate, not an automatic error, and profile summaries do not establish that a dataset is valid for a particular analysis.

## Quick start

Requires Python 3.10+.

```bash
python -m pip install -e .
dataset-doctor sample-data/quality-demo.csv
dataset-doctor sample-data/quality-demo.csv --format json --output report.json
```

Without installing:

```bash
PYTHONPATH=src python -m dataset_doctor.cli sample-data/quality-demo.csv
```

## Example report

```bash
dataset-doctor sample-data/quality-demo.csv --format markdown
```

## Tests

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

GitHub Actions runs the test suite on Python 3.10, 3.11, and 3.12 and exercises the sample dataset.

## Project layout

```text
src/dataset_doctor/   CSV profiling engine and CLI
tests/                Unit and command-line tests
sample-data/          Synthetic demonstration data
pyproject.toml        Package metadata and CLI entry point
.github/workflows/    Continuous integration
```

## Privacy

Everything runs locally. The tool does not upload datasets or send data to external services. Avoid committing private datasets or generated reports containing sensitive information.

## License

MIT.
