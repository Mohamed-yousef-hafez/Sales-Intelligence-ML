"""Automatic refresh: reads the newest sales file(s) from a folder, cleans them, trains the model, makes the
forecast and writes the Power BI files into another folder. Used by refresh_exports.py."""
import io
import os
from pathlib import Path
import time

import pandas as pd

from .data import clean_data
from .export import clean_csv_bytes
from .model import cross_validate_time, reliability_verdict, train_and_evaluate
from .model_export import model_files
from .monitoring import log_event
from .powerbi import build_powerbi_files, status_frame
from .security import ALLOWED_EXTENSIONS, load_uploaded_file


class PathUpload(io.BytesIO):
    """A file on disk that looks like an uploaded file (name, size, read, seek)."""

    def __init__(self, path):
        data = Path(path).read_bytes()
        super().__init__(data)
        self.name = Path(path).name
        self.size = len(data)


def list_input_files(input_path):
    path = Path(input_path)
    if path.is_file():
        return [path]
    if not path.is_dir():
        return []
    files = [
        p for p in path.iterdir()
        if p.is_file() and p.suffix.lower() in ALLOWED_EXTENSIONS and not p.name.startswith(("~$", "."))  # ~$ = Excel lock file
    ]
    return sorted(files, key=lambda p: p.stat().st_mtime)


def write_atomic(path, content):
    """Write to a temporary file, then rename. Power BI never reads a half-written file."""
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_bytes(content)
    os.replace(temporary, path)


def run_pipeline(input_path, output_dir, horizon=3, combine=False, reliability=True, lang="en"):
    """One refresh. Returns {'status': 'OK' | 'FAILED' | 'NO_FILES', 'message': ..., 'files': [...]}.
    When something fails, the previous export files are left untouched and refresh_status.csv says why."""
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    files = list_input_files(input_path)
    if not files:
        message = f"No sales file found in {input_path}"
        write_atomic(output / "refresh_status.csv", clean_csv_bytes(status_frame(str(input_path), 0, 0, "NO_FILES", message)))
        return {"status": "NO_FILES", "message": message, "files": []}
    if not combine:
        files = files[-1:]   # the newest file
    source = ", ".join(p.name for p in files)

    try:
        raw = pd.concat([load_uploaded_file(PathUpload(p)) for p in files], ignore_index=True)
        df, report = clean_data(raw)

        bundle, verdict, model_message = None, None, ""
        try:
            bundle = train_and_evaluate(df)
            if reliability:
                verdict = reliability_verdict(cross_validate_time(df))
        except ValueError as error:   # not enough data for a model: everything else is still exported
            model_message = str(error)

        exports = build_powerbi_files(df, report, bundle, verdict, horizon, source=source, lang=lang)
        if bundle is not None:   # the model itself, for the company's own system
            exports.update(model_files(bundle, df, source))
        exports["refresh_status.csv"] = clean_csv_bytes(status_frame(source, len(raw), len(df), "OK", model_message))
        status_file = exports.pop("refresh_status.csv")
        for name, content in exports.items():
            write_atomic(output / name, content)
        write_atomic(output / "refresh_status.csv", status_file)   # last: when it says OK, every file is ready

        log_event("auto_refresh_ok", f"source={source}, rows={len(df)}")
        return {"status": "OK", "message": model_message, "files": sorted(exports) + ["refresh_status.csv"], "rows": len(df)}
    except Exception as error:
        message = str(error)[:300]
        log_event("auto_refresh_failed", message)
        write_atomic(output / "refresh_status.csv", clean_csv_bytes(status_frame(source, 0, 0, "FAILED", message)))
        return {"status": "FAILED", "message": message, "files": []}


def folder_signature(input_path):
    """Changes whenever a file is added, replaced or modified."""
    return tuple((p.name, p.stat().st_mtime_ns, p.stat().st_size) for p in list_input_files(input_path))


def watch(input_path, output_dir, interval=300, settle=5, max_cycles=None, report=print, **options):
    """Check the folder every `interval` seconds and refresh when something changed.
    A file that was modified in the last `settle` seconds is still being copied, so we wait for it."""
    last_signature, cycles = None, 0
    while max_cycles is None or cycles < max_cycles:
        cycles += 1
        files = list_input_files(input_path)
        copying = any(time.time() - p.stat().st_mtime < settle for p in files)
        signature = folder_signature(input_path)
        if files and not copying and signature != last_signature:
            result = run_pipeline(input_path, output_dir, **options)
            report(f"[{time.strftime('%H:%M:%S')}] {result['status']} {result['message']}")
            last_signature = signature
        if max_cycles is None or cycles < max_cycles:
            time.sleep(interval)
