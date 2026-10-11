"""Things a real company file or deployment can hit."""
import io
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.agent import SalesAgent
from src.data import clean_data, to_number
from src.export import clean_csv_bytes, template_xlsx_bytes
from src.model import train_and_evaluate
from src.rag import SalesRAG
from src.security import load_uploaded_file


class FakeUpload(io.BytesIO):
    def __init__(self, data, name):
        super().__init__(data)
        self.name = name
        self.size = len(data)


def sales_table(n=120, **drop):
    rng = np.random.default_rng(3)
    df = pd.DataFrame({
        "Order Date": pd.date_range("2024-01-01", periods=n).strftime("%Y-%m-%d"),
        "Sales": rng.uniform(50, 500, n).round(2),
        "Profit": rng.uniform(-40, 120, n).round(2),
        "Discount": rng.choice([0, 0.1, 0.2, 0.3], n),
        "Quantity": rng.integers(1, 6, n),
        "Category": rng.choice(["Furniture", "Technology"], n),
        "Sub-Category": rng.choice(["Chairs", "Phones", "Tables"], n),
        "Region": rng.choice(["West", "East"], n),
        "Product": [f"Product {i % 40}" for i in range(n)],
        "Customer": [f"Customer {i % 25}" for i in range(n)],
    })
    return df.drop(columns=list(drop.get("drop", [])))


def run_everything(df):
    out, report = clean_data(df)
    agent = SalesAgent(out, SalesRAG(out))
    agent.run("What is the total sales?")
    agent.run("كيف يؤثر الخصم على الربح؟")
    return out, report, agent


@pytest.mark.parametrize("missing", [
    ["Discount"], ["Quantity"], ["Category", "Sub-Category"], ["Region"],
    ["Discount", "Quantity", "Category", "Sub-Category", "Region", "Product", "Customer"],  # only Date, Sales, Profit
])
def test_optional_columns_can_be_missing(missing):
    out, report, _ = run_everything(sales_table(drop=missing))
    assert len(out) == 120
    for column in missing:
        if column in ["Discount", "Quantity", "Category", "Sub-Category", "Region"]:
            assert column in report["optional_columns_missing"]
    train_and_evaluate(out)  # the model works with whatever columns exist


def test_discount_question_without_discount_column_is_explained():
    out, _, agent = run_everything(sales_table(drop=["Discount"]))
    result = agent.run("How does discount affect profit?")
    assert "no discount column" in result["answer"]
    assert "لا يحتوي" in agent.run("كيف يؤثر الخصم على الربح؟")["answer"]


def test_profit_is_calculated_from_cost():
    df = sales_table()
    df["Cost"] = (df["Sales"] - df["Profit"]).round(2)
    out, report = clean_data(df.drop(columns=["Profit"]))
    assert report["profit_calculated_from_cost"] is True
    assert np.allclose(out["Profit"], df["Sales"] - df["Cost"])


def test_missing_profit_and_cost_gives_a_clear_error():
    with pytest.raises(ValueError, match="Profit"):
        load_uploaded_file(FakeUpload(sales_table().drop(columns=["Profit"]).to_csv(index=False).encode(), "a.csv"))


def test_excel_with_several_sheets_uses_the_sales_sheet():
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer) as writer:
        pd.DataFrame({"ملاحظات": ["للاستخدام الداخلي"]}).to_excel(writer, sheet_name="ملاحظات", index=False)
        pd.DataFrame({"x": [1, 2], "y": [3, 4]}).to_excel(writer, sheet_name="ملخص", index=False)
        sales_table(50).to_excel(writer, sheet_name="مبيعات", index=False)
    assert len(load_uploaded_file(FakeUpload(buffer.getvalue(), "company.xlsx"))) == 50


def test_old_xls_files_are_supported():
    xlwt = pytest.importorskip("xlwt")
    df = sales_table(20)[["Order Date", "Sales", "Profit"]]
    book = xlwt.Workbook()
    sheet = book.add_sheet("Sales")
    for j, name in enumerate(df.columns):
        sheet.write(0, j, name)
    for i, row in enumerate(df.itertuples(index=False), start=1):
        for j, value in enumerate(row):
            sheet.write(i, j, value if isinstance(value, str) else float(value))
    buffer = io.BytesIO()
    book.save(buffer)
    assert len(load_uploaded_file(FakeUpload(buffer.getvalue(), "old.xls"))) == 20


@pytest.mark.parametrize("name,kwargs,encoding", [
    ("a.csv", dict(sep=","), "utf-8"),
    ("a.tsv", dict(sep="\t"), "utf-8"),
    ("a.csv", dict(sep=";", decimal=","), "cp1256"),   # Arabic Excel with a decimal comma
    ("a.txt", dict(sep="|"), "utf-8"),
])
def test_every_separator_and_number_format_gives_the_same_totals(name, kwargs, encoding):
    df = sales_table(100)
    df["Product"] = ["Chair, large" if i % 2 else "Table" for i in range(100)]   # commas inside values
    out, _ = clean_data(load_uploaded_file(FakeUpload(df.to_csv(index=False, **kwargs).encode(encoding), name)))
    assert len(out) == 100
    assert out["Sales"].sum() == pytest.approx(df["Sales"].sum(), abs=0.01)
    assert out["Profit"].sum() == pytest.approx(df["Profit"].sum(), abs=0.01)


def test_number_formats():
    text = pd.Series(["1,234.50", "1.234,50", "12,5", "1,200", "3,54", "$ 1,000", "(500)", "٣٫٥"], dtype="string")
    # each value alone (a column decides what a lone comma means)
    assert [to_number(pd.Series([v], dtype="string")).iloc[0] for v in text] == [1234.5, 1234.5, 12.5, 1200, 3.54, 1000, -500, 3.5]


def test_model_gives_clear_messages_when_data_is_not_enough():
    out, _ = clean_data(sales_table(20))
    with pytest.raises(ValueError, match="At least 30"):
        train_and_evaluate(out)
    df = sales_table(100)
    df["Profit"] = df["Profit"].abs() + 1          # every sale is profitable
    out, _ = clean_data(df)
    with pytest.raises(ValueError, match="at least 5 profitable"):
        train_and_evaluate(out)


def test_products_and_customers_are_understood_by_the_assistant():
    out, _, agent = run_everything(sales_table())
    result = agent.run("What is the profit of Product 7?")
    assert result["tool"] == "entity_summary" and "Product 7" in result["answer"]
    result = agent.run("أفضل عميل")
    assert result["tool"] == "ranking" and "Customer" in result["answer"]


def test_exported_csv_cannot_run_formulas_in_excel():
    csv = clean_csv_bytes(pd.DataFrame({"name": ["=HYPERLINK(\"http://x\")", "+1+1", "@SUM(A1)", "normal"], "n": [1, 2, 3, 4]}))
    names = pd.read_csv(io.BytesIO(csv), encoding="utf-8-sig")["name"].tolist()
    assert all(name.startswith("'") for name in names[:3]) and names[3] == "normal"


@pytest.mark.parametrize("lang", ["en", "ar"])
def test_template_can_be_uploaded_back(lang):
    out, report = clean_data(load_uploaded_file(FakeUpload(template_xlsx_bytes(lang), "template.xlsx")))
    assert len(out) == 3 and report["optional_columns_missing"] == ["Ship Date"]
    assert out["Discount"].tolist() == [0.1, 0.0, 0.3]


def test_password_protection(monkeypatch):
    from streamlit.testing.v1 import AppTest
    monkeypatch.setenv("APP_PASSWORD", "s3cret")
    at = AppTest.from_file(str(Path(__file__).parent.parent / "app.py"), default_timeout=120).run()
    assert not at.exception and not at.tabs                      # nothing is shown before login
    at.text_input[0].set_value("wrong").run()
    at.button[0].click().run()
    assert at.error and not at.tabs
    at.text_input[0].set_value("s3cret").run()
    at.button[0].click().run()
    assert not at.exception and len(at.tabs) == 4                # logged in
