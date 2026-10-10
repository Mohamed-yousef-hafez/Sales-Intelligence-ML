from pathlib import Path
import pandas as pd

ALLOWED_EXTENSIONS = {".csv", ".xlsx"}
MAX_FILE_SIZE_MB = 10

COLUMN_ALIASES = {
    "Sales": ["sales", "sale", "المبيعات", "قيمة المبيعات", "اجمالي المبيعات", "إجمالي المبيعات"],
    "Profit": ["profit", "الربح", "الأرباح", "صافي الربح"],
    "Discount": ["discount", "الخصم", "نسبة الخصم"],
    "Quantity": ["quantity", "qty", "الكمية", "عدد الوحدات"],
    "Category": ["category", "الفئة", "التصنيف"],
    "Sub-Category": ["sub-category", "subcategory", "sub_category", "الفئة الفرعية", "التصنيف الفرعي"],
    "Order Date": ["order date", "order_date", "date", "تاريخ الطلب", "تاريخ البيع"],
    "Ship Date": ["ship date", "ship_date", "تاريخ الشحن"],
    "Region": ["region", "المنطقة", "الإقليم"],
    "Segment": ["segment", "الشريحة", "قطاع العملاء"],
    "Ship Mode": ["ship mode", "ship_mode", "طريقة الشحن", "نوع الشحن"],
}

REQUIRED_COLUMNS = {"Sales", "Profit", "Discount", "Quantity", "Category", "Sub-Category", "Order Date"}


def normalize_column_name(name):
    return " ".join(str(name).strip().lower().replace("_", " ").split())


def standardize_columns(df):
    df = df.copy()
    lookup = {}
    for standard, aliases in COLUMN_ALIASES.items():
        lookup[normalize_column_name(standard)] = standard
        for alias in aliases:
            lookup[normalize_column_name(alias)] = standard
    rename_map = {}
    for col in df.columns:
        standard = lookup.get(normalize_column_name(col))
        if standard:
            rename_map[col] = standard
    df = df.rename(columns=rename_map)
    duplicates = df.columns[df.columns.duplicated()].tolist()
    if duplicates:
        raise ValueError(
            "Two or more columns map to the same field: " + ", ".join(map(str, duplicates))
        )
    return df


def validate_upload(uploaded_file):
    ext = Path(uploaded_file.name.lower()).suffix
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError("Only CSV and XLSX files are allowed.")
    if uploaded_file.size > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise ValueError(f"File is too large. Maximum size is {MAX_FILE_SIZE_MB} MB.")


def load_uploaded_file(uploaded_file):
    validate_upload(uploaded_file)
    ext = Path(uploaded_file.name.lower()).suffix
    if ext == ".csv":
        last_error = None
        for encoding in ("utf-8-sig", "utf-8", "cp1256"):
            try:
                uploaded_file.seek(0)
                df = pd.read_csv(uploaded_file, encoding=encoding)
                break
            except UnicodeDecodeError as exc:
                last_error = exc
        else:
            raise ValueError("Could not decode CSV. Save it as UTF-8 and upload it again.") from last_error
    else:
        df = pd.read_excel(uploaded_file)
    if df.empty:
        raise ValueError("The uploaded file contains no rows.")
    df = standardize_columns(df)
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError("Missing required columns after Arabic/English name mapping: " + ", ".join(sorted(missing)))
    return df
