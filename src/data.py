import re

import numpy as np
import pandas as pd

from .i18n import COLUMN_LABELS_AR
from .text_utils import ARABIC_DIGITS, PERSIAN_DIGITS, ARABIC_LETTERS, has_arabic, normalize_text, remove_marks

NUMERIC_COLUMNS = ["Sales", "Profit", "Cost", "Quantity"]  # Discount has its own converter
CATEGORY_COLUMNS = ["Category", "Sub-Category", "Region", "Segment", "Ship Mode", "Product", "Customer"]
# Columns that are not needed, but give more analysis when they exist.
OPTIONAL_COLUMNS = ["Discount", "Quantity", "Category", "Sub-Category", "Region", "Segment", "Ship Mode", "Ship Date"]

# Text that means "no value" (compared in lowercase).
MISSING_TOKENS = {
    "n/a", "na", "n.a", "nan", "null", "none", "nil", "-", "--", "---", "?", "??", "unknown", "undefined",
    "not available", "missing", "blank", "#n/a", "#value!", "#div/0!", "#ref!",
    "غير متوفر", "غير متاح", "لا يوجد", "لايوجد", "بدون", "فارغ", "غير معروف", "غير محدد", "لا شيء",
}

# Labels of total/summary rows that Excel users often leave at the bottom of the table.
SUMMARY_LABELS = {
    normalize_text(label) for label in [
        "total", "totals", "grand total", "sub total", "subtotal", "sum",
        "الإجمالي", "إجمالي", "الاجمالي", "المجموع", "مجموع", "الإجمالي الكلي", "المجموع الكلي", "إجمالي كلي",
    ]
}

# Arabic month names (Gulf/Egypt names and Levant names) -> English, so pandas can read the date.
ARABIC_MONTHS = {
    "يناير": "January", "فبراير": "February", "مارس": "March", "أبريل": "April", "ابريل": "April",
    "مايو": "May", "يونيو": "June", "يوليو": "July", "أغسطس": "August", "اغسطس": "August",
    "سبتمبر": "September", "أكتوبر": "October", "اكتوبر": "October", "نوفمبر": "November",
    "ديسمبر": "December",
    "كانون الثاني": "January", "شباط": "February", "آذار": "March", "اذار": "March",
    "نيسان": "April", "أيار": "May", "ايار": "May", "حزيران": "June", "تموز": "July",
    "آب": "August", "أيلول": "September", "ايلول": "September", "تشرين الأول": "October",
    "تشرين الاول": "October", "تشرين الثاني": "November", "كانون الأول": "December",
    "كانون الاول": "December",
}


# ----------------------------------------------------------------------------- text
def clean_text(value):
    """Clean one text cell: Arabic/Persian digits -> 0-9, remove diacritics, extra spaces and hidden marks."""
    if isinstance(value, str):
        value = value.translate(ARABIC_DIGITS).translate(PERSIAN_DIGITS)
        value = re.sub("[\u200e\u200f\ufeff]", "", value).replace("\xa0", " ")
        value = " ".join(remove_marks(value).split())
        return value if value else np.nan
    return value


def unify_variants(series):
    """'furniture ', 'FURNITURE' and 'Furniture' become one value (the most common spelling).
    Arabic letter shapes are also ignored (أثاث = اثاث). Returns (series, number_of_variants_merged)."""
    counts = series.dropna().value_counts()          # most common spelling first
    best = {}
    for value in counts.index:
        best.setdefault(normalize_text(value), value)
    mapping = {value: best[normalize_text(value)] for value in counts.index}
    merged = sum(1 for value, chosen in mapping.items() if value != chosen)
    return series.map(mapping), merged


def fill_unknown(series):
    """Missing category names become 'Unknown' (or 'غير محدد' when the column is Arabic)."""
    missing = series.isna()
    if not missing.any() or missing.all():
        return series, 0
    arabic = series.dropna().map(has_arabic).mean() > 0.5
    return series.fillna("غير محدد" if arabic else "Unknown"), int(missing.sum())


# ----------------------------------------------------------------------------- numbers
def to_number(series):
    """Convert text like '1,234.5', '١٬٢٣٤٫٥', '$1,200', '20%', '(500)' or '1200 ج.م' to numbers."""
    if pd.api.types.is_numeric_dtype(series):
        return series.astype(float)
    text = (
        series.astype("string")
        .str.translate(ARABIC_DIGITS)
        .str.translate(PERSIAN_DIGITS)
        .str.replace("٬", "", regex=False)    # Arabic thousands separator
        .str.replace("٫", ".", regex=False)   # Arabic decimal separator
        .str.replace("−", "-", regex=False)   # unicode minus sign
        .str.replace(r"(?<=[^\W\d_])\.|\.(?=[^\W\d_])", "", regex=True)  # dots inside "ج.م" / "E.G.P"
        .str.replace(r"^\((.*)\)$", r"-\1", regex=True)  # accounting negative: (500) -> -500
        .str.replace(r"[^0-9.,\-]", "", regex=True)       # remove currency, %, spaces, letters
    )
    return pd.to_numeric(fix_separators(text), errors="coerce").astype(float)


def fix_separators(text):
    """Decide what , and . mean:  1,234.50 (US)   1.234,50 (European)   12,5 (decimal comma)   1,234 (thousands)."""
    has_comma = text.str.contains(",", regex=False).fillna(False).astype(bool)
    has_dot = text.str.contains(".", regex=False).fillna(False).astype(bool)

    # Both appear: the LAST one is the decimal separator.
    both = has_comma & has_dot
    last_comma = text.str.rfind(",").fillna(-1)
    last_dot = text.str.rfind(".").fillna(-1)
    european = both & (last_comma > last_dot)
    text = text.where(~european, text.str.replace(".", "", regex=False).str.replace(",", ".", regex=False))
    text = text.where(~(both & ~european), text.str.replace(",", "", regex=False))

    # Only commas: if some value has a tail that is not 3 digits ("3,54"), the column uses a decimal comma.
    only_comma = has_comma & ~has_dot
    if only_comma.any():
        tails = text[only_comma].str.split(",").str[-1].str.len()
        decimal_comma = bool((tails != 3).any())
        text = text.where(~only_comma, text.str.replace(",", "." if decimal_comma else "", regex=False))
    return text


def to_discount(series):
    """Discount as a fraction between 0 and 1, from 0.2, 20 or '20%' (also when they are mixed).
    Returns (fractions, True_if_percent_values_were_converted)."""
    if pd.api.types.is_numeric_dtype(series):
        has_percent_sign = pd.Series(False, index=series.index)
    else:
        has_percent_sign = series.astype("string").str.contains("%", regex=False).fillna(False).astype(bool)
    numbers = to_number(series)
    numbers[has_percent_sign] = numbers[has_percent_sign] / 100

    plain = numbers[~has_percent_sign & (numbers > 0)]
    percent_style = len(plain) > 0 and (plain > 1).mean() > 0.5   # most discounts look like 5, 10, 20 ...
    if percent_style:
        numbers[~has_percent_sign] = numbers[~has_percent_sign] / 100
    return numbers, bool(has_percent_sign.any() or percent_style)


# ----------------------------------------------------------------------------- dates
def _english_months(series):
    text = series.astype("string")
    if text.str.contains(ARABIC_LETTERS.pattern, regex=True).any():
        for name in sorted(ARABIC_MONTHS, key=len, reverse=True):
            text = text.str.replace(name, ARABIC_MONTHS[name], regex=False)
    return text


def detect_date_order(text_values):
    """Look at dates like 25/03/2024: a first part above 12 must be a day, a second part above 12 a month."""
    parts = text_values.astype("string").str.extract(r"^\s*(\d{1,2})[/\-.](\d{1,2})[/\-.]\d{2,4}")
    day_votes = int((pd.to_numeric(parts[0]) > 12).sum())
    month_votes = int((pd.to_numeric(parts[1]) > 12).sum())
    if day_votes > month_votes:
        return "day-first"
    if month_votes > day_votes:
        return "month-first"
    return "unknown"


def parse_dates(series, day_first):
    if pd.api.types.is_datetime64_any_dtype(series):
        return series
    text = _english_months(series)
    # 1) ISO dates (2024-03-25) are never ambiguous, so read them first.
    parsed = pd.to_datetime(text, errors="coerce", format="ISO8601")
    # 2) Excel stores dates as day numbers (45292 = 2024-01-01).
    numbers = pd.to_numeric(text, errors="coerce").astype(float)
    serial = parsed.isna() & numbers.between(20000, 80000)
    if serial.any():
        parsed = parsed.combine_first(pd.to_datetime(numbers[serial], unit="D", origin="1899-12-30"))
    # 3) Everything else (25/03/2024, 25 March 2024, ...) uses the detected day/month order.
    failed = parsed.isna() & text.notna() & ~serial
    if failed.any():
        fallback = pd.to_datetime(text[failed], errors="coerce", dayfirst=day_first, format="mixed")
        parsed = parsed.combine_first(fallback)
    return parsed


# ----------------------------------------------------------------------------- main
def count_extreme_values(df):
    """Rows with a very extreme Sales/Profit value (10 x the interquartile range). They are kept, only reported."""
    flagged = pd.Series(False, index=df.index)
    for col in ["Sales", "Profit"]:
        q1, q3 = df[col].quantile([0.25, 0.75])
        iqr = q3 - q1
        if iqr > 0:
            flagged |= (df[col] < q1 - 10 * iqr) | (df[col] > q3 + 10 * iqr)
    return int(flagged.sum())


def clean_data(df):
    """Clean sales data (Arabic or English) and return (cleaned_dataframe, quality_report)."""
    if df is None or df.empty:
        raise ValueError("The dataset is empty. | الملف فارغ.")

    df = df.copy()
    rows_before = len(df)
    columns_before = len(df.columns)
    missing_cells_before = int(df.isna().sum().sum())

    # 1) Text: digits, diacritics, spaces; placeholders such as N/A, null, "-" become real missing values.
    text_columns = list(df.select_dtypes(include=["object", "string"]).columns)
    placeholders = 0
    for col in text_columns:
        df[col] = df[col].map({value: clean_text(value) for value in df[col].dropna().unique()})  # each value once
        is_placeholder = df[col].astype("string").str.lower().isin(MISSING_TOKENS).fillna(False).astype(bool)
        placeholders += int(is_placeholder.sum())
        df[col] = df[col].mask(is_placeholder)

    # 2) Remove total / summary rows (for example "Total" or "الإجمالي" at the bottom of the sheet).
    summary_rows = pd.Series(False, index=df.index)
    for col in text_columns:
        labels = [v for v in df[col].dropna().unique()
                  if isinstance(v, str) and (normalize_text(v) in SUMMARY_LABELS or normalize_text(v).startswith("grand total"))]
        if labels:
            summary_rows |= df[col].isin(labels)
    summary_rows_removed = int(summary_rows.sum())
    df = df[~summary_rows].copy()

    # 3) One spelling for each category name.
    variants_merged = 0
    for col in CATEGORY_COLUMNS:
        if col in df.columns:
            df[col], merged = unify_variants(df[col])
            variants_merged += merged

    # 4) Exact duplicate rows.
    duplicate_count = int(df.duplicated().sum())
    df = df.drop_duplicates().copy()
    rows_after_duplicates = len(df)

    # 5) Numbers, discount and dates.
    for col in NUMERIC_COLUMNS:
        if col in df.columns:
            df[col] = to_number(df[col])
    discount_converted = False
    if "Discount" in df.columns:
        df["Discount"], discount_converted = to_discount(df["Discount"])

    date_columns = [col for col in ["Order Date", "Ship Date"] if col in df.columns]
    text_dates = [df[col] for col in date_columns if not pd.api.types.is_datetime64_any_dtype(df[col])]
    date_order = detect_date_order(pd.concat(text_dates)) if text_dates else "unknown"
    for col in date_columns:
        df[col] = parse_dates(df[col], day_first=(date_order == "day-first"))

    # Duplicates again: rows that looked different as text ("1,200" / "1200.00", a date as text / as an Excel number)
    # are identical now that numbers and dates are converted.
    duplicates_after_conversion = int(df.duplicated().sum())
    duplicate_count += duplicates_after_conversion
    df = df.drop_duplicates().copy()
    rows_after_duplicates = len(df)

    missing_columns = [col for col in ["Sales", "Order Date"] if col not in df.columns]
    if "Profit" not in df.columns and "Cost" not in df.columns:
        missing_columns.append("Profit")
    if missing_columns:
        names = ", ".join(f"{col} ({COLUMN_LABELS_AR[col]})" for col in missing_columns)
        raise ValueError("Required columns are missing | أعمدة مطلوبة غير موجودة: " + names)

    # Profit = Sales - Cost when the file has a cost column instead of a profit column.
    profit_from_cost = False
    if "Profit" not in df.columns:
        df["Profit"] = df["Sales"] - df["Cost"]
        profit_from_cost = True

    # 6) Rows without a required value, then rows with impossible values.
    required = ["Sales", "Profit", "Order Date"] + [col for col in ["Discount", "Quantity"] if col in df.columns]
    rows_with_missing_required = int(df[required].isna().any(axis=1).sum())
    df = df.dropna(subset=required).copy()

    year = df["Order Date"].dt.year
    impossible = (df["Sales"] <= 0) | (year < 1990) | (year > 2100)
    if "Quantity" in df.columns:
        impossible |= df["Quantity"] <= 0
    if "Discount" in df.columns:
        impossible |= (df["Discount"] < 0) | (df["Discount"] > 1)
    rows_impossible = int(impossible.sum())
    df = df[~impossible].copy()

    if df.empty:
        raise ValueError(
            "No valid rows remain after cleaning. Check numeric values and date formats. | "
            "لا توجد صفوف صالحة بعد التنظيف. راجع القيم الرقمية وصيغة التاريخ."
        )

    # 7) Missing category names become 'Unknown'.
    filled_unknown = 0
    for col in CATEGORY_COLUMNS:
        if col in df.columns:
            df[col], filled = fill_unknown(df[col])
            filled_unknown += filled

    # 8) Helper columns and the target.
    if "Ship Date" in df.columns:
        ship_days = (df["Ship Date"] - df["Order Date"]).dt.days
        ship_days = ship_days.where(ship_days >= 0)  # shipping before ordering is invalid -> missing
        if ship_days.notna().any():
            df["Ship Days"] = ship_days
    df["Order Month"] = df["Order Date"].dt.month
    df["Order Year"] = df["Order Date"].dt.year
    df["Profitable"] = (df["Profit"] > 0).astype(int)

    corrections = (placeholders + summary_rows_removed + variants_merged + duplicate_count
                   + rows_with_missing_required + rows_impossible + filled_unknown + int(discount_converted))
    report = {
        "cleaning_changes": corrections,           # 0 means the file was already clean
        "cleaning_needed": corrections > 0,
        "rows_before": rows_before,
        "columns_before": columns_before,
        "placeholders_converted": placeholders,
        "summary_rows_removed": summary_rows_removed,
        "spelling_variants_unified": variants_merged,
        "duplicate_rows_removed": duplicate_count,
        "rows_after_duplicates": rows_after_duplicates,
        "rows_missing_required_fields": rows_with_missing_required,
        "rows_impossible_values": rows_impossible,
        "categories_filled_unknown": filled_unknown,
        "possible_extreme_values_kept": count_extreme_values(df),
        "profit_calculated_from_cost": profit_from_cost,
        "optional_columns_missing": [col for col in OPTIONAL_COLUMNS if col not in df.columns],
        "rows_after_cleaning": len(df),
        "rows_removed_total": rows_before - len(df),
        "missing_cells_before_cleaning": missing_cells_before,
        "missing_cells_after_cleaning": int(df.isna().sum().sum()),
        "sales_total": float(df["Sales"].sum()),
        "profit_total": float(df["Profit"].sum()),
        "discount_converted_from_percent": discount_converted,
        "date_order": date_order,
        "date_min": df["Order Date"].min(),
        "date_max": df["Order Date"].max(),
    }
    return df.reset_index(drop=True), report
