"""Dirty-data tests: a clean table is damaged in known ways, and the result must match the expected clean table."""
import io

import pandas as pd
import pytest

from src.data import clean_data, to_discount
from src.security import load_uploaded_file


class FakeUpload(io.BytesIO):
    def __init__(self, data, name):
        super().__init__(data)
        self.name = name
        self.size = len(data)


def base_table(n=200):
    return pd.DataFrame({
        "Order Date": pd.date_range("2024-01-01", periods=n).strftime("%Y-%m-%d"),
        "Sales": [100.0 + i for i in range(n)],
        "Profit": [10.0 + (i % 7) - 2 for i in range(n)],
        "Discount": [0.1 * (i % 4) for i in range(n)],
        "Quantity": [1 + i % 5 for i in range(n)],
        "Category": ["Furniture", "Technology"] * (n // 2),
        "Sub-Category": ["Chairs", "Phones"] * (n // 2),
        "Region": ["West", "East", "South", "Central"] * (n // 4),
    }).astype(object)


def dirty_table():
    d = base_table()
    d.loc[0, "Category"] = "furniture "; d.loc[1, "Category"] = "FURNITURE"      # spelling variants
    d.loc[2, "Region"] = "N/A"; d.loc[3, "Region"] = "-"                          # placeholders in text
    d.loc[4, "Sales"] = "N/A"                                                     # placeholder in a number
    d.loc[5, "Quantity"] = 0; d.loc[6, "Discount"] = 150; d.loc[7, "Sales"] = -50  # impossible values
    d.loc[8, "Order Date"] = "1900-01-01"                                         # absurd date
    d.loc[9, "Order Date"] = 45292                                                # Excel date number
    total = pd.DataFrame([{"Category": "Total", "Sales": 99999, "Profit": 9999}])
    return pd.concat([d, d.iloc[10:13], total], ignore_index=True)               # 3 duplicates + total row


def test_dirty_table_is_cleaned_correctly():
    out, report = clean_data(dirty_table())
    assert len(out) == 195                                  # 204 - 3 dups - 1 total - 1 missing - 4 impossible
    assert sorted(out["Category"].unique()) == ["Furniture", "Technology"]
    assert out["Region"].value_counts()["Unknown"] == 2     # N/A and - are missing, not regions
    assert out["Sales"].min() > 0 and out["Quantity"].min() > 0
    assert out["Discount"].between(0, 1).all()
    assert out["Order Date"].min() == pd.Timestamp("2024-01-01")   # no 1900 dates, Excel number kept
    assert (out["Order Date"] == pd.Timestamp("2024-01-01")).sum() == 2
    assert out["Sales"].sum() < 99999 * 2                   # the total row is not counted
    assert report["summary_rows_removed"] == 1
    assert report["duplicate_rows_removed"] == 3
    assert report["rows_impossible_values"] == 4
    assert report["spelling_variants_unified"] == 2
    assert report["rows_removed_total"] == 204 - 195


def test_clean_table_is_not_changed():
    out, report = clean_data(base_table())
    assert len(out) == 200
    assert report["rows_removed_total"] == 0
    assert out["Sales"].sum() == sum(100.0 + i for i in range(200))


def test_arabic_dirty_values():
    d = base_table(40)
    d["Category"] = ["أثاث", "اثاث"] * 20                  # same word, different letter shapes
    d["Region"] = ["غير متوفر", "الشرق"] * 20               # "not available" placeholder
    d = pd.concat([d, pd.DataFrame([{"Category": "الإجمالي", "Sales": 12345}])], ignore_index=True)
    out, report = clean_data(d)
    assert len(out) == 40 and report["summary_rows_removed"] == 1
    assert out["Category"].nunique() == 1
    assert set(out["Region"]) == {"غير محدد", "الشرق"}


def test_mixed_discount_formats():
    values, converted = to_discount(pd.Series(["20%", "0.1", "5", "10"], dtype="string"))
    assert converted is True
    # "20%" -> 0.2; the other values are percents too (the column mostly holds 5, 10, ...)
    assert values.round(4).tolist() == [0.2, 0.001, 0.05, 0.1]
    fractions, converted = to_discount(pd.Series([0.0, 0.1, 0.2, 0.0]))
    assert converted is False and fractions.tolist() == [0.0, 0.1, 0.2, 0.0]
    percents, converted = to_discount(pd.Series([0, 10, 20, 50]))
    assert converted is True and percents.tolist() == [0.0, 0.1, 0.2, 0.5]


def test_title_rows_above_the_header_excel():
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer) as writer:
        pd.DataFrame([["تقرير المبيعات 2024"], ["شركة الأمل"], [None]]).to_excel(writer, index=False, header=False)
        base_table(20).to_excel(writer, index=False, startrow=3)
    table = load_uploaded_file(FakeUpload(buffer.getvalue(), "report.xlsx"))
    assert len(table) == 20 and "Sales" in table.columns


def test_title_lines_above_the_header_csv():
    text = "Sales report\nCompany X\n\n" + base_table(20).to_csv(index=False)
    table = load_uploaded_file(FakeUpload(text.encode("utf-8"), "report.csv"))
    assert len(table) == 20 and "Sales" in table.columns


def test_all_rows_invalid_gives_a_clear_error():
    d = base_table(8)
    d["Sales"] = "N/A"
    with pytest.raises(ValueError, match="No valid rows"):
        clean_data(d)
