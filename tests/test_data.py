import pandas as pd
from src.data import clean_data


def make_df(**overrides):
    data = {
        "Sales": [100, 50, 20],
        "Profit": [20, -5, 2],
        "Discount": [0.1, 0.5, 0.0],
        "Quantity": [2, 1, 3],
        "Order Date": ["2024-01-01", "2024-01-02", "2024-01-03"],
        "Ship Date": ["2024-01-03", "2024-01-05", "2024-01-04"],
    }
    data.update(overrides)
    return pd.DataFrame(data)


def test_clean_data():
    out, report = clean_data(make_df())
    assert "Profitable" in out.columns
    assert len(out) == 3
    assert out["Profitable"].tolist() == [1, 0, 1]
    assert report["rows_after_cleaning"] == 3


def test_duplicates_are_removed():
    df = pd.concat([make_df(), make_df().head(1)], ignore_index=True)
    out, report = clean_data(df)
    assert len(out) == 3
    assert report["duplicate_rows_removed"] == 1


def test_arabic_digits_and_separators():
    df = make_df(Sales=["١٢٣٫٥", "١٬٢٣٤٫٥", "20"])
    out, _ = clean_data(df)
    assert out["Sales"].tolist() == [123.5, 1234.5, 20.0]


def test_negative_ship_days_become_missing():
    df = make_df(**{"Ship Date": ["2023-12-01", "2024-01-05", "2024-01-04"]})
    out, _ = clean_data(df)
    assert pd.isna(out.loc[0, "Ship Days"])
    assert out.loc[1, "Ship Days"] == 3


def test_discount_percent_is_converted():
    out, report = clean_data(make_df(Discount=[10, 50, 0]))
    assert out["Discount"].tolist() == [0.1, 0.5, 0.0]
    assert report["discount_converted_from_percent"] is True


def test_arabic_text_cells_are_cleaned():
    out, _ = clean_data(make_df(Region=["  الشَّرق ", "الغرب\u200f", "الشرق"]))
    assert out["Region"].tolist() == ["الشرق", "الغرب", "الشرق"]
