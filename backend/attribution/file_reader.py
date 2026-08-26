import io
import polars as pl

SUPPORTED_ENCODINGS = ["utf-8-sig", "utf-8", "cp1251", "cp1252"]
CSV_DELIMITERS = [",", ";", "\t"]


class FileReadError(Exception):
    """Raised when a file can't be decoded or parsed into a table."""


def read_tabular_file(raw_bytes: bytes, filename: str) -> pl.DataFrame:
    """
    Reads a CSV or Excel file into a DataFrame, auto-detecting text
    encoding and delimiter for CSVs (common pain point with 1C/Excel
    exports that use Windows-1251 encoding and semicolon delimiters).
    """
    lower = filename.lower()
    if lower.endswith(".xlsx") or lower.endswith(".xls"):
        return _read_excel(raw_bytes)
    if lower.endswith(".csv"):
        return _read_csv(raw_bytes)
    raise FileReadError(f"Unsupported file type: {filename}. Use .csv or .xlsx.")


def _read_excel(raw_bytes: bytes) -> pl.DataFrame:
    try:
        return pl.read_excel(io.BytesIO(raw_bytes))
    except Exception as e:
        raise FileReadError(f"Could not read Excel file: {e}")


def _read_csv(raw_bytes: bytes) -> pl.DataFrame:
    text = None
    for encoding in SUPPORTED_ENCODINGS:
        try:
            candidate = raw_bytes.decode(encoding)
        except UnicodeDecodeError:
            continue
        if "\x00" in candidate:
            # a NUL byte after decoding means we picked the wrong
            # encoding (e.g. misread a binary/UTF-16 file as a
            # single-byte codepage), not real text — keep trying
            continue
        text = candidate
        break

    if text is None:
        raise FileReadError("Could not decode file — unrecognized text encoding.")

    first_line = text.splitlines()[0] if text.splitlines() else ""
    delimiter = max(CSV_DELIMITERS, key=lambda d: first_line.count(d))

    try:
        return pl.read_csv(io.StringIO(text), separator=delimiter)
    except Exception as e:
        raise FileReadError(f"Could not parse CSV (tried delimiter '{delimiter}'): {e}") 
    
