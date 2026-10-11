import pandas as pd
import pytest
from src.security import standardize_columns, validate_upload


class FakeUpload:
    def __init__(self, name, size):
        self.name = name
        self.size = size


def test_arabic_column_names_are_mapped():
    df = pd.DataFrame(columns=["المبيعات", "الربح", "الخصم", "الكمية", "تاريخ الطلب"])
    assert list(standardize_columns(df).columns) == ["Sales", "Profit", "Discount", "Quantity", "Order Date"]


def test_two_columns_for_same_field_are_rejected():
    with pytest.raises(ValueError):
        standardize_columns(pd.DataFrame(columns=["Sales", "المبيعات"]))


def test_bad_extension_and_big_file_are_rejected():
    with pytest.raises(ValueError):
        validate_upload(FakeUpload("virus.exe", 100))
    with pytest.raises(ValueError):
        validate_upload(FakeUpload("data.csv", 51 * 1024 * 1024))
    validate_upload(FakeUpload("data.csv", 1024))  # fine
