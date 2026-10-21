"""The exported model must work outside this project and give the same answers as the app."""
import io
import json
from pathlib import Path
import subprocess
import sys
import zipfile

import numpy as np
import pandas as pd
import pytest

from src.data import clean_data
from src.export import clean_csv_bytes
from src.model import score_dataframe, train_and_evaluate
from src.model_export import MODEL_FILE, model_files, model_package_zip
from src.security import prepare_table

ROOT = Path(__file__).parent.parent


@pytest.fixture(scope="module")
def trained():
    df, _ = clean_data(prepare_table(pd.read_csv(ROOT / "data" / "sample_superstore.csv")))
    return df, train_and_evaluate(df)


def test_package_contents_and_model_card(trained):
    df, bundle = trained
    files = model_files(bundle, df, "demo")
    assert set(files) == {MODEL_FILE, "model_card.json", "use_model.py", "README_MODEL.md"}
    card = json.loads(files["model_card.json"])
    assert card["metrics_on_the_most_recent_rows"]["accuracy"] > 0.9
    names = [c["name"] for c in card["input_columns"]]
    assert "Discount" in names and "Unit Price" in names and "scikit-learn" in card["versions"]
    assert any("trust" in warning for warning in card["warnings"])           # the pickle warning is there
    assert zipfile.ZipFile(io.BytesIO(model_package_zip(bundle, df))).testzip() is None


def test_exported_model_runs_without_this_project_and_matches_the_app(trained, tmp_path):
    df, bundle = trained
    for name, content in model_files(bundle, df).items():
        (tmp_path / name).write_bytes(content)
    sample = df.sample(500, random_state=3).sort_index()
    (tmp_path / "sales.csv").write_bytes(clean_csv_bytes(sample))
    # run in another folder with a clean environment: only pandas, scikit-learn and joblib are available there
    result = subprocess.run([sys.executable, "-I", "use_model.py", "sales.csv"], cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr[-600:]
    scored = pd.read_csv(tmp_path / "scored_sales.csv", encoding="utf-8-sig")
    expected = score_dataframe(bundle[0], sample)
    assert np.allclose(scored["Profit Probability"], expected["Profit Probability"], atol=1e-4)
    assert (scored["Risk Level"].values == expected["Risk Level"].values).all()


def test_script_works_with_a_file_that_has_only_raw_columns(trained, tmp_path):
    """A company file with only the original columns (no Ship Days, Order Month...) is prepared by the script."""
    df, bundle = trained
    for name, content in model_files(bundle, df).items():
        (tmp_path / name).write_bytes(content)
    raw = df.sample(200, random_state=1)[["Order Date", "Ship Date", "Sales", "Quantity", "Discount", "Ship Mode", "Segment",
                                           "Region", "Category", "Sub-Category"]]
    raw.to_csv(tmp_path / "raw.csv", index=False)
    result = subprocess.run([sys.executable, "-I", "use_model.py", "raw.csv"], cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr[-600:]
    scored = pd.read_csv(tmp_path / "scored_sales.csv", encoding="utf-8-sig")
    assert len(scored) == 200 and scored["Profit Probability"].between(0, 1).all()
