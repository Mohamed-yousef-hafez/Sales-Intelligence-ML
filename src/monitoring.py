import logging
from pathlib import Path
import time

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"

logger = logging.getLogger("sales_ml")
logger.setLevel(logging.INFO)

if not logger.handlers:
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    try:
        LOG_DIR.mkdir(exist_ok=True)
        handler = logging.FileHandler(LOG_DIR / "app.log", encoding="utf-8")
    except OSError:
        # Some hosting services give a read-only folder. The app must still run: log to the console instead.
        handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def log_event(event, details=""):
    logger.info("%s | %s", event, details)


class Timer:
    def __enter__(self):
        self.start = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.elapsed = time.perf_counter() - self.start
