import pandas as pd

def clean_data(df):
    df = df.copy()

    # Remove exact duplicate rows.
    df = df.drop_duplicates()

    # Convert dates safely.
    for col in ["Order Date", "Ship Date"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    # Convert numeric fields.
    for col in ["Sales", "Profit", "Discount", "Quantity"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Keep rows that contain the fields required by the ML/business logic.
    required = ["Sales", "Profit", "Discount", "Quantity", "Order Date"]
    df = df.dropna(subset=required)

    if "Ship Date" in df.columns:
        df["Ship Days"] = (df["Ship Date"] - df["Order Date"]).dt.days
        df["Ship Days"] = df["Ship Days"].clip(lower=0)

    df["Order Month"] = df["Order Date"].dt.month
    df["Order Year"] = df["Order Date"].dt.year
    df["Profitable"] = (df["Profit"] > 0).astype(int)

    return df.reset_index(drop=True)
