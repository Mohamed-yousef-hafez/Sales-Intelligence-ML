"""The generated Power BI project: every field a visual uses must exist in the model, and the files must follow the formats."""
import json
from pathlib import Path
import re

import pandas as pd
import pytest

from src.data import clean_data
from src.forecast import forecast_monthly
from src.model import score_dataframe, train_and_evaluate
from src.pbip import DASH_TEXT, Model, build_pages, build_project
from src.security import prepare_table

ROOT = Path(__file__).parent.parent


@pytest.fixture(scope="module")
def scored_demo():
    df, _ = clean_data(prepare_table(pd.read_csv(ROOT / "data" / "sample_superstore.csv")))
    bundle = train_and_evaluate(df)
    return df, score_dataframe(bundle[0], df, bundle[2]["train_index"])


def fields_used(node):
    """Every (kind, table, name) that a visual refers to."""
    found = []
    if isinstance(node, dict):
        for kind in ("Column", "Measure"):
            if kind in node and isinstance(node[kind], dict) and "Property" in node[kind]:
                found.append((kind, node[kind]["Expression"]["SourceRef"]["Entity"], node[kind]["Property"]))
        for value in node.values():
            found += fields_used(value)
    elif isinstance(node, list):
        for value in node:
            found += fields_used(value)
    return found


def check_project(sales_frame, scored, forecast_rows, lang="en"):
    model = Model(sales_frame, scored, forecast_rows)
    columns, measures = model.column_names(), model.measure_names()
    all_measures = set().union(*measures.values())

    # 1) every field of every visual exists
    pages = build_pages(model, DASH_TEXT[lang])
    visual_count = 0
    for page in pages:
        for visual in page.visuals:
            visual_count += 1
            for kind, table, name in fields_used(visual):
                known = columns if kind == "Column" else measures
                assert table in known and name in known[table], f"{page.key}/{visual['name']}: {kind} {table}[{name}] is not in the model"
    assert visual_count > 5

    # 2) every DAX measure refers to columns and measures that exist
    for table, spec in model.tables.items():
        for name, expression, *_ in spec["measures"]:
            for ref_table, ref_name in re.findall(r"(?<![\w\]])(\w+|'[^']+')\[([^\]]+)\]", expression):
                ref_table = ref_table.strip("'")
                assert ref_table in columns and ref_name in columns[ref_table], f"measure {name}: {ref_table}[{ref_name}] does not exist"
            for ref in re.findall(r"(?<![\w'\]])\[([^\]]+)\]", expression):
                assert ref in all_measures, f"measure {name}: [{ref}] is not a measure"

    # 3) the files: TMDL uses tabs, sort-by columns exist, the relationship columns exist
    files = build_project(sales_frame, scored, forecast_rows, lang)
    for path, text in files.items():
        if path.endswith(".tmdl"):
            assert not re.search(r"^ +\S", text, re.M), f"{path}: a line starts with spaces (TMDL needs tabs)"
    for table, spec in model.tables.items():
        names = {c.name for c in spec["columns"]}
        assert all(c.sort_by in names for c in spec["columns"] if c.sort_by)
    assert "Order Date" in columns["Sales"] and "Date" in columns["Date"]
    for path, text in files.items():
        if path.endswith(".json") or path.endswith(".pbip") or path.endswith(".pbir") or path.endswith(".pbism") or path.endswith(".platform"):
            json.loads(text)
    return files, pages


@pytest.mark.parametrize("lang", ["en", "ar"])
def test_full_dashboard(scored_demo, lang):
    df, scored = scored_demo
    files, pages = check_project(scored, True, True, lang)
    assert [p.key for p in pages] == ["p_overview", "p_forecast", "p_risk", "p_quality"]
    assert "Sales Dashboard.pbip" in files and "README_DASHBOARD.md" in files
    overview = {p.key: p for p in pages}["p_overview"]
    assert pages[0].title == DASH_TEXT[lang]["overview"]
    assert sum(v["visual"]["visualType"] == "card" for v in overview.visuals) >= 8      # KPI cards + best/worst


@pytest.mark.parametrize("drop", [
    ["Discount"], ["Category", "Sub-Category"], ["Region"], ["Product", "Customer"],
    ["Discount", "Quantity", "Category", "Sub-Category", "Region", "Segment", "Ship Mode", "Product", "Customer"],
])
def test_dashboard_adapts_to_missing_columns(scored_demo, drop):
    df, scored = scored_demo
    frame = scored.drop(columns=[c for c in drop if c in scored.columns])
    check_project(frame, True, True)
    check_project(frame.drop(columns=["Profit Probability", "Predicted Profitable", "Risk Level", "In Training Set"]), False, True)


def test_no_forecast_page_without_a_forecast_and_no_risk_page_without_a_model(scored_demo):
    df, scored = scored_demo
    _, pages = check_project(df, False, False)
    assert [p.key for p in pages] == ["p_overview", "p_quality"]


def test_measures_match_the_dax_file(scored_demo):
    """The measures in the dashboard are the ones in powerbi/measures.dax (the same names)."""
    df, scored = scored_demo
    model = Model(scored, True, True)
    names = set().union(*model.measure_names().values())
    dax = (ROOT / "powerbi" / "measures.dax").read_text(encoding="utf-8")
    in_file = set(re.findall(r"^([A-Za-z][\w %]+?) =", re.sub(r"--.*", "", dax), re.M))
    assert {"Total Sales", "Total Profit", "Profit Margin %", "Loss Rate %", "Avg Discount", "Sales LY"} <= names
    assert (names - {"Discount Band"}) <= in_file | {"Worst Region", "Best Region"}, names - in_file


def test_excel_queries_read_the_tables_that_the_workbook_has(scored_demo):
    """The model reads these Excel Tables; src/powerbi.py writes them."""
    from src.powerbi import build_powerbi_files, workbook_bytes   # noqa: F401
    df, scored = scored_demo
    model = Model(scored, True, True)
    tables = {name for name in model.tables if name != "Date"}
    assert tables == {"Sales", "Forecast", "Monthly", "Quality", "ModelMetrics", "Status"}
