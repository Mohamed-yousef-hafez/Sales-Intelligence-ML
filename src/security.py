import io
from pathlib import Path
import re

import pandas as pd

from .i18n import COLUMN_LABELS_AR
from .text_utils import normalize_text

ALLOWED_EXTENSIONS = {".csv", ".tsv", ".txt", ".xlsx", ".xlsm", ".xls"}
EXCEL_EXTENSIONS = {".xlsx", ".xlsm", ".xls"}
MAX_FILE_SIZE_MB = 50   # keep equal to maxUploadSize in .streamlit/config.toml
MAX_ROWS = 1_000_000

# Accepted column names (English and Arabic). Matching ignores case, "_", "-", "%", brackets,
# Arabic diacritics and the shape of letters (أ/إ/ا, ة/ه, ى/ي), so "الأرباح" = "الارباح".
COLUMN_ALIASES = {
    "Sales": [
        "sales", "sale", "total sales", "net sales", "revenue", "amount", "sales amount", "total amount",
        "المبيعات", "قيمة المبيعات", "اجمالي المبيعات", "إجمالي المبيعات", "مبيعات", "الايرادات", "الإيرادات",
        "الايراد", "المبلغ", "اجمالي المبلغ", "قيمة البيع", "صافي المبيعات",
    ],
    "Profit": [
        "profit", "net profit", "gross profit",
        "الربح", "الأرباح", "الارباح", "صافي الربح", "صافي الأرباح", "ربح", "أرباح", "الربح الصافي", "اجمالي الربح",
    ],
    "Discount": [
        "discount", "discount rate", "disc", "discount percent",
        "الخصم", "نسبة الخصم", "خصم", "التخفيض", "نسبة التخفيض", "قيمة الخصم",
    ],
    "Quantity": [
        "quantity", "qty", "units", "units sold", "number of units",
        "الكمية", "كمية", "عدد الوحدات", "الكمية المباعة", "عدد القطع", "العدد",
    ],
    "Category": [
        "category", "product category", "department", "group",
        "الفئة", "التصنيف", "فئة المنتج", "القسم", "المجموعة", "تصنيف المنتج", "نوع المنتج",
    ],
    "Sub-Category": [
        "sub-category", "subcategory", "sub_category", "product sub category", "sub group",
        "الفئة الفرعية", "التصنيف الفرعي", "الفئة الفرعيه", "الصنف", "المجموعة الفرعية", "القسم الفرعي",
    ],
    "Order Date": [
        "order date", "order_date", "date", "invoice date", "sale date", "sales date", "transaction date",
        "تاريخ الطلب", "تاريخ البيع", "التاريخ", "تاريخ الفاتورة", "تاريخ العملية", "تاريخ المبيعات",
    ],
    "Ship Date": [
        "ship date", "ship_date", "delivery date", "shipping date",
        "تاريخ الشحن", "تاريخ التسليم", "تاريخ التوصيل",
    ],
    "Cost": [
        "cost", "total cost", "cogs", "cost of goods sold", "التكلفة", "تكلفة", "اجمالي التكلفة", "إجمالي التكلفة", "التكلفة الاجمالية",
    ],
    "Product": [
        "product", "product name", "item", "item name", "sku",
        "المنتج", "اسم المنتج", "المنتجات", "الصنف المباع", "اسم الصنف", "البند",
    ],
    "Customer": [
        "customer", "customer name", "client", "client name",
        "العميل", "اسم العميل", "الزبون", "اسم الزبون",
    ],
    "Region": [
        "region", "area", "zone", "governorate",
        "المنطقة", "الإقليم", "الاقليم", "المحافظة", "منطقة", "الفرع الجغرافي",
    ],
    "Segment": [
        "segment", "customer segment", "customer type",
        "الشريحة", "قطاع العملاء", "شريحة العملاء", "نوع العميل", "فئة العميل",
    ],
    "Ship Mode": [
        "ship mode", "ship_mode", "shipping method", "shipping mode", "delivery method",
        "طريقة الشحن", "نوع الشحن", "وسيلة الشحن", "طريقة التوصيل", "وسيلة التوصيل",
    ],
}

# Only these are needed. Profit can also come from Cost (Profit = Sales - Cost).
# Everything else (Discount, Quantity, Category, Region ...) is optional: related features are skipped.
REQUIRED_COLUMNS = {"Sales", "Order Date"}


def normalize_column_name(name):
    text = normalize_text(str(name).replace("\ufeff", ""))
    text = re.sub(r"[_\-/\\.()%]", " ", text)
    return " ".join(text.split())


def build_lookup():
    lookup = {}
    for standard, aliases in COLUMN_ALIASES.items():
        lookup[normalize_column_name(standard)] = standard
        for alias in aliases:
            lookup[normalize_column_name(alias)] = standard
    return lookup


LOOKUP = build_lookup()


def count_known_columns(names):
    return len({LOOKUP.get(normalize_column_name(name)) for name in names} - {None})


def find_header_row(df, max_rows=20):
    """Some files have a report title or empty lines above the real header.
    Look at the first rows and use the row that contains the most known column names."""
    best_row, best_count = None, count_known_columns(df.columns)
    for i in range(min(max_rows, len(df))):
        count = count_known_columns(df.iloc[i].dropna().astype(str))
        if count > best_count:
            best_row, best_count = i, count
    if best_row is None or best_count < 3:
        return df
    header = df.iloc[best_row].astype(str).tolist()
    df = df.iloc[best_row + 1:].copy()
    df.columns = header
    return df.dropna(how="all").dropna(axis=1, how="all")


def standardize_columns(df):
    """Rename Arabic/English column names to the standard English names used by the project."""
    df = df.copy()
    rename_map = {}
    for col in df.columns:
        standard = LOOKUP.get(normalize_column_name(col))
        if standard:
            rename_map[col] = standard
    df = df.rename(columns=rename_map)
    duplicates = df.columns[df.columns.duplicated()].tolist()
    if duplicates:
        raise ValueError(
            "Two or more columns map to the same field | أكثر من عمود يشير إلى نفس الحقل: "
            + ", ".join(map(str, sorted(set(duplicates))))
        )
    return df


def validate_upload(uploaded_file):
    ext = Path(uploaded_file.name.lower()).suffix
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError("Only Excel (.xlsx .xlsm .xls) and CSV/TSV files are allowed. | يُسمح بملفات Excel و CSV/TSV فقط.")
    if uploaded_file.size > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise ValueError(
            f"File is too large. Maximum size is {MAX_FILE_SIZE_MB} MB. | "
            f"حجم الملف كبير. الحد الأقصى {MAX_FILE_SIZE_MB} ميجابايت."
        )


def detect_delimiter(text):
    """Pick , ; tab or | by looking at the first lines: the right one splits most lines into the same number of columns."""
    lines = [line for line in text.splitlines() if line.strip()][:30]
    best, best_score = ",", 0
    for separator in [",", ";", "\t", "|"]:
        counts = [line.count(separator) for line in lines]
        if not counts:
            continue
        common = max(set(counts), key=counts.count)           # most common number of separators per line
        score = common * counts.count(common) if common > 0 else 0
        if score > best_score:
            best, best_score = separator, score
    return best


def read_csv(uploaded_file):
    """Read CSV/TSV/TXT in UTF-8 or Arabic Windows encoding (cp1256), with automatic separator detection."""
    uploaded_file.seek(0)
    data = uploaded_file.read()
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = data.decode("cp1256", errors="replace")   # Arabic Windows files
    separator = detect_delimiter(text[:20000])
    try:
        return pd.read_csv(io.StringIO(text), sep=separator)
    except pd.errors.ParserError:  # title lines with fewer columns above the table
        return pd.read_csv(io.StringIO(text), sep=separator, header=None, names=range(60), dtype=str)


def known_columns_in_header_area(sheet):
    """How many known column names appear in the column row or in the first rows (title rows)."""
    best = count_known_columns(sheet.columns)
    for i in range(min(20, len(sheet))):
        best = max(best, count_known_columns(sheet.iloc[i].dropna().astype(str)))
    return best


def read_excel_best_sheet(uploaded_file):
    """Excel files can have many sheets (notes, summary, data...). Use the sheet that looks most like sales data."""
    sheets = pd.read_excel(uploaded_file, sheet_name=None)
    best, best_score = None, (-1, -1)
    for sheet in sheets.values():
        sheet = sheet.dropna(how="all")
        score = (known_columns_in_header_area(sheet), len(sheet))
        if score > best_score:
            best, best_score = sheet, score
    if best is None:
        raise ValueError("The Excel file has no sheets. | ملف Excel لا يحتوي على أوراق.")
    return best


def prepare_table(df):
    """Drop empty rows/columns, map Arabic/English column names and check the required columns."""
    df = df.dropna(how="all").dropna(axis=1, how="all")
    if df.empty:
        raise ValueError("The uploaded file contains no rows. | الملف المرفوع لا يحتوي على صفوف.")
    if len(df) > MAX_ROWS:
        raise ValueError(
            f"The file has more than {MAX_ROWS:,} rows. | الملف يحتوي على أكثر من {MAX_ROWS:,} صف."
        )

    def missing_columns(table):
        missing = sorted(REQUIRED_COLUMNS - set(table.columns))
        if "Profit" not in table.columns and "Cost" not in table.columns:
            missing.append("Profit")
        return missing

    df = standardize_columns(df)
    if missing_columns(df):  # maybe the real header is a few rows down
        df = standardize_columns(find_header_row(df.rename(columns=str)))
    missing = missing_columns(df)
    if missing:
        names = ", ".join(
            f"{col} ({COLUMN_LABELS_AR[col]})" + (f" / Cost ({COLUMN_LABELS_AR['Cost']})" if col == "Profit" else "")
            for col in missing
        )
        raise ValueError("Missing required columns | أعمدة مطلوبة غير موجودة: " + names)
    return df


def load_uploaded_file(uploaded_file):
    validate_upload(uploaded_file)
    ext = Path(uploaded_file.name.lower()).suffix
    if ext in EXCEL_EXTENSIONS:
        df = read_excel_best_sheet(uploaded_file)
    else:
        df = read_csv(uploaded_file)
    return prepare_table(df)
