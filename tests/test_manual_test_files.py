"""Runs every file made by tools/make_test_files.py through the real code and checks it against expected.json."""
import importlib.util
from pathlib import Path

import pytest

from src.data import clean_data
from src.forecast import forecast_monthly
from src.model import train_and_evaluate
from src.pipeline import PathUpload, run_pipeline
from src.security import load_uploaded_file

ROOT = Path(__file__).parent.parent


@pytest.fixture(scope="module")
def cases(tmp_path_factory):
    spec = importlib.util.spec_from_file_location("make_test_files", ROOT / "tools" / "make_test_files.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    folder = tmp_path_factory.mktemp("test_files")
    return folder, module.build_all(folder)


def single_files(folder, expected):
    return [(name, info) for name, info in expected.items() if (folder / name).is_file()]


def test_every_file_gives_the_expected_result(cases):
    folder, expected = cases
    checked = 0
    for name, info in single_files(folder, expected):
        if "load_error_contains" in info:
            with pytest.raises(ValueError, match=info["load_error_contains"]):
                load_uploaded_file(PathUpload(folder / name))
            checked += 1
            continue
        cleaned, report = clean_data(load_uploaded_file(PathUpload(folder / name)))
        assert len(cleaned) == info["rows_after_cleaning"], f"{name}: rows"
        # dirty files had 10% of the sales values rewritten with 2 decimals, so allow a tiny rounding difference
        assert cleaned["Sales"].sum() == pytest.approx(info["sales_total"], abs=10), f"{name}: sales total"
        assert cleaned["Profit"].sum() == pytest.approx(info["profit_total"], abs=0.5), f"{name}: profit total"
        if "model_error_contains" in info:
            with pytest.raises(ValueError, match=info["model_error_contains"]):
                train_and_evaluate(cleaned)
        if "forecast_status" in info:
            assert forecast_monthly(cleaned, "Sales")["status"] == info["forecast_status"]
        checked += 1
    assert checked >= 10


def test_the_two_overlapping_files_with_the_refresh_script(cases, tmp_path):
    folder, expected = cases
    result = run_pipeline(folder / "12_two_files_for_refresh", tmp_path / "exports", combine=True, reliability=False)
    assert result["status"] == "OK" and result["rows"] == expected["12_two_files_for_refresh"]["rows_after_cleaning"]
