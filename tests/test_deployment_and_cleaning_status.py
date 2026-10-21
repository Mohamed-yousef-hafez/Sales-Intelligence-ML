"""Public demo mode, read-only hosting, the "was the file clean?" indicator and the new downloads in the app."""
from pathlib import Path
import shutil
import subprocess
import sys

import pandas as pd
import pytest

from src.data import clean_data
from src.security import prepare_table

ROOT = Path(__file__).parent.parent
APP = str(ROOT / "app.py")


def test_clean_file_is_reported_as_clean_and_dirty_file_as_dirty():
    clean, report = clean_data(prepare_table(pd.read_csv(ROOT / "data" / "sample_superstore.csv")))
    assert report["cleaning_needed"] is False and report["cleaning_changes"] == 0
    assert len(clean) == report["rows_before"]                              # nothing removed, nothing changed
    dirty = pd.DataFrame({
        "Order Date": ["2024-01-01", "2024-01-02", "2024-01-03"] * 4, "Sales": ["N/A", "10", "20"] * 4,
        "Profit": [1, 2, 3] * 4, "Discount": [0, 0, 0] * 4, "Quantity": [1, 1, 1] * 4,
    })
    _, report = clean_data(dirty)
    assert report["cleaning_needed"] is True and report["cleaning_changes"] > 0


def test_clean_file_gives_the_same_numbers_with_and_without_the_checks():
    """Nothing is changed in a clean file: the totals equal the raw totals."""
    raw = pd.read_csv(ROOT / "data" / "sample_superstore.csv")
    cleaned, report = clean_data(prepare_table(raw))
    assert cleaned["Sales"].sum() == pytest.approx(raw["Sales"].sum()) and cleaned["Profit"].sum() == pytest.approx(raw["Profit"].sum())


def test_app_shows_the_cleaning_status_in_both_languages():
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(APP, default_timeout=300).run()
    at.sidebar.radio[0].set_value("English").run()
    assert any("already clean" in s.value for s in at.success)               # English demo is clean
    at.sidebar.radio[1].set_value("ar").run()
    assert any("needed cleaning" in i.value for i in at.info)                # Arabic demo had 3 corrections
    at.sidebar.radio[0].set_value("العربية").run()
    assert any("احتاج تنظيفاً" in i.value for i in at.info)


def test_demo_only_mode_has_no_upload_button(monkeypatch):
    from streamlit.testing.v1 import AppTest
    monkeypatch.setenv("APP_DEMO_ONLY", "1")
    at = AppTest.from_file(APP, default_timeout=300).run()
    assert not at.exception and len(at.tabs) == 6                            # the app works on the demo data
    source = (ROOT / "app.py").read_text(encoding="utf-8")
    assert source.count("st.file_uploader(") == 1 and "DEMO_ONLY" in source
    assert any("public demo" in i.value or "العرض العام" in i.value for i in at.info)


def test_app_prepares_the_model_files_when_the_model_is_trained():
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(APP, default_timeout=300).run()
    [b.click() for b in at.button if "درّب" in b.label]
    at.run()
    joblib_file, package = at.session_state["model_download"]
    assert len(joblib_file) > 100_000 and package[:2] == b"PK"


def test_the_app_still_starts_when_the_logs_folder_cannot_be_created(tmp_path):
    shutil.copytree(ROOT / "src", tmp_path / "src")
    (tmp_path / "logs").write_text("a file, so the logs folder cannot be created")
    code = "from src.monitoring import log_event; log_event('x', 'y'); print('ok')"
    result = subprocess.run([sys.executable, "-c", code], cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 0 and "ok" in result.stdout


def test_password_and_demo_mode_can_come_from_streamlit_secrets(monkeypatch):
    """On Streamlit Community Cloud the settings are written in Secrets, not in environment variables."""
    from streamlit.testing.v1 import AppTest
    monkeypatch.delenv("APP_PASSWORD", raising=False)
    monkeypatch.delenv("APP_DEMO_ONLY", raising=False)
    at = AppTest.from_file(APP, default_timeout=300)
    at.secrets["APP_PASSWORD"] = "cloud-secret"
    at.run()
    assert not at.exception and not at.tabs                                     # asks for the password
    at.text_input[0].set_value("cloud-secret").run()
    at.button[0].click().run()
    assert len(at.tabs) == 6
    at2 = AppTest.from_file(APP, default_timeout=300)
    at2.secrets["APP_DEMO_ONLY"] = "1"
    at2.run()
    assert not at2.exception and any("public demo" in i.value or "العرض العام" in i.value for i in at2.info)


def test_number_of_cores_can_be_set_with_an_environment_variable():
    code = "import src.model as m; print(m.N_JOBS, m.build_model.__name__)"
    for value, expected in (("1", "1"), (None, "-1")):
        env = {k: v for k, v in __import__("os").environ.items() if k != "SALES_ML_JOBS"}
        if value:
            env["SALES_ML_JOBS"] = value
        result = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True, env=env)
        assert result.stdout.split()[0] == expected, result.stderr[-300:]
