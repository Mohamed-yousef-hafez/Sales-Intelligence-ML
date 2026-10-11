import io

import pandas as pd

from src.data import clean_data
from src.i18n import TEXT
from src.model import train_and_evaluate
from src.security import load_uploaded_file


class FakeUpload(io.BytesIO):
    def __init__(self, data, name):
        super().__init__(data)
        self.name = name
        self.size = len(data)


def messy_arabic_frame(rows=60):
    """What a real Arabic company file often looks like."""
    months = ["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو"]
    data = []
    for i in range(rows):
        data.append({
            "التاريخ": f"{(i % 27) + 1} {months[i % 6]} 2024",
            "إجمالي المبيعات": f"{1000 + i * 10:,}.50 ج.م".replace(",", "٬").replace(".", "٫"),
            "الأرباح": "(120)" if i % 4 == 0 else str(200 + i),
            "نسبة الخصم": "40%" if i % 4 == 0 else "5%",
            "الكمية": str(i % 5 + 1),
            "التصنيف": "أثاث" if i % 2 else "تقنية",
            "الصنف": "كراسي" if i % 2 else "هواتف",
            "المحافظة": ["القاهرة", "الجيزة", "الإسكندرية"][i % 3],
        })
    return pd.DataFrame(data)


def test_messy_arabic_excel_file_end_to_end():
    buffer = io.BytesIO()
    messy_arabic_frame().to_excel(buffer, index=False)
    raw = load_uploaded_file(FakeUpload(buffer.getvalue(), "مبيعات.xlsx"))
    df, report = clean_data(raw)
    assert len(df) == 60
    assert df["Sales"].iloc[0] == 1000.5          # ١٬٠٠٠٫٥٠ ج.م
    assert df["Profit"].iloc[0] == -120           # accounting negative (120)
    assert df["Discount"].iloc[0] == 0.4          # "40%"
    assert df["Order Date"].iloc[0].month == 1    # يناير
    assert report["discount_converted_from_percent"] is True
    _, _, metrics = train_and_evaluate(df)
    assert metrics["accuracy"] > 0.8


def test_arabic_csv_with_semicolon_and_windows_encoding():
    text = messy_arabic_frame().to_csv(index=False, sep=";")
    raw = load_uploaded_file(FakeUpload(text.encode("cp1256", errors="replace"), "data.csv"))
    assert {"Sales", "Profit", "Category", "Region"} <= set(raw.columns)


def test_day_first_dates_are_detected():
    df = pd.DataFrame({
        "Sales": [10, 20, 30], "Profit": [1, 2, 3], "Discount": [0, 0, 0], "Quantity": [1, 1, 1],
        "Order Date": ["03/01/2024", "25/01/2024", "04/02/2024"],
    })
    out, report = clean_data(df)
    assert report["date_order"] == "day-first"
    assert out["Order Date"].dt.month.tolist() == [1, 1, 2]


def test_both_languages_have_the_same_text_keys():
    assert set(TEXT["en"]) == set(TEXT["ar"])
