import pandas as pd

ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
PERSIAN_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")


def _normalize_text_digits(value):
    if isinstance(value, str):
        return value.translate(ARABIC_DIGITS).translate(PERSIAN_DIGITS).strip()
    return value


def _parse_dates(series):
    # Prefer pandas' normal parsing first (works well for ISO dates), then day-first fallback.
    parsed = pd.to_datetime(series, errors="coerce")
    failed = parsed.isna() & series.notna()
    if failed.any():
        fallback = pd.to_datetime(series[failed], errors="coerce", dayfirst=True)
        parsed.loc[failed] = fallback
    return parsed


def clean_data(df):
    """Clean sales data and return (cleaned_dataframe, quality_report)."""
    if df is None or df.empty:
        raise ValueError("The dataset is empty.")

    df = df.copy()
    rows_before = len(df)
    columns_before = len(df.columns)
    missing_cells_before = int(df.isna().sum().sum())

    for col in df.select_dtypes(include=["object", "string"]).columns:
        df[col] = df[col].map(_normalize_text_digits)

    duplicate_count = int(df.duplicated().sum())
    df = df.drop_duplicates().copy()
    rows_after_duplicates = len(df)

    for col in ["Sales", "Profit", "Discount", "Quantity"]:
        if col in df.columns:
            cleaned = df[col].astype("string").str.replace(",", "", regex=False)
            df[col] = pd.to_numeric(cleaned, errors="coerce")

    for col in ["Order Date", "Ship Date"]:
        if col in df.columns:
            df[col] = _parse_dates(df[col])

    required = ["Sales", "Profit", "Discount", "Quantity", "Order Date"]
    missing_columns = [col for col in required if col not in df.columns]
    if missing_columns:
        raise ValueError("Required columns are missing: " + ", ".join(missing_columns))

    rows_with_invalid_required = int(df[required].isna().any(axis=1).sum())
    df = df.dropna(subset=required).copy()
    if df.empty:
        raise ValueError("No valid rows remain after cleaning. Check numeric values and date formats.")

    if "Ship Date" in df.columns:
        df["Ship Days"] = (df["Ship Date"] - df["Order Date"]).dt.days
        df.loc[df["Ship Days"] < 0, "Ship Days"] = pd.NA

    df["Order Month"] = df["Order Date"].dt.month
    df["Order Year"] = df["Order Date"].dt.year
    df["Profitable"] = (df["Profit"] > 0).astype(int)

    report = {
        "rows_before": rows_before,
        "columns_before": columns_before,
        "duplicate_rows_removed": duplicate_count,
        "rows_after_duplicates": rows_after_duplicates,
        "rows_missing_required_fields": rows_with_invalid_required,
        "rows_after_cleaning": len(df),
        "rows_removed_total": rows_before - len(df),
        "missing_cells_before_cleaning": missing_cells_before,
        "missing_cells_after_cleaning": int(df.isna().sum().sum()),
        "sales_total": float(df["Sales"].sum()),
        "profit_total": float(df["Profit"].sum()),
        "date_min": df["Order Date"].min(),
        "date_max": df["Order Date"].max(),
    }
    cleaned_df = df.reset_index(drop=True)
    cleaned_df.attrs["quality_report"] = report
    return cleaned_df
