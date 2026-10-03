from pathlib import Path
import pandas as pd

ALLOWED_EXTENSIONS = {".csv", ".xlsx"}
MAX_FILE_SIZE_MB = 10
REQUIRED_COLUMNS = {
    "Sales", "Profit", "Discount", "Quantity",
    "Category", "Sub-Category", "Order Date"
}

def validate_upload(uploaded_file):
    name = uploaded_file.name.lower()
    ext = Path(name).suffix
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError("Only CSV and XLSX files are allowed.")
    if uploaded_file.size > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise ValueError(f"File is too large. Maximum size is {MAX_FILE_SIZE_MB} MB.")

def load_uploaded_file(uploaded_file):
    validate_upload(uploaded_file)
    ext = Path(uploaded_file.name.lower()).suffix
    if ext == ".csv":
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError("Missing required columns: " + ", ".join(sorted(missing)))
    return df
