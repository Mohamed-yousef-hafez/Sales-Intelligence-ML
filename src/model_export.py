"""Export the trained profitability model so the company can use it in its own system.

Files made:
    profit_model.joblib   the scikit-learn Pipeline (cleaning of missing values + encoding + RandomForest) with its feature list
    model_card.json       what the model needs and how good it is (columns, allowed values, metrics, library versions)
    use_model.py          a small script that scores a sales file with the model (needs only pandas, scikit-learn, joblib)
    README_MODEL.md       how to use it, and the warnings
"""
import datetime
import io
import json
import platform
import zipfile

import joblib
import numpy as np
import pandas as pd
import sklearn

MODEL_FILE = "profit_model.joblib"


def model_card(model_bundle, df, source="app"):
    model, features, metrics = model_bundle
    columns = []
    for name in model.feature_names_in_:
        series = df[name] if name in df.columns else None
        if name == "Unit Price":
            columns.append({"name": name, "type": "number", "note": "calculated: Sales / Quantity (the script does it)"})
        elif series is not None and pd.api.types.is_numeric_dtype(series):
            columns.append({"name": name, "type": "number", "min": float(series.min()), "max": float(series.max())})
        elif series is not None:
            values = sorted(map(str, series.dropna().unique()))
            columns.append({"name": name, "type": "text", "values_seen_in_training": values[:100]})
    return {
        "created": datetime.datetime.now().isoformat(timespec="seconds"),
        "source": source,
        "rows_in_the_data": len(df),
        "target": "Profitable = 1 when Profit > 0, otherwise 0",
        "output": "probability of class 1 (profitable); Risk Level: High if the loss probability is 0.6 or more, Medium from 0.3, otherwise Low",
        "input_columns": columns,
        "metrics_on_the_most_recent_rows": {
            "accuracy": round(float(metrics["accuracy"]), 4),
            "baseline_accuracy": round(float(metrics["baseline_accuracy"]), 4),
            "precision": round(float(metrics["precision"]), 4),
            "recall": round(float(metrics["recall"]), 4),
            "f1": round(float(metrics["f1"]), 4),
            "roc_auc": round(float(metrics["roc_auc"]), 4),
            "test_rows": int(metrics["test_size"]),
            "split": metrics["split_strategy"],
        },
        "versions": {"python": platform.python_version(), "scikit-learn": sklearn.__version__,
                     "pandas": pd.__version__, "numpy": np.__version__, "joblib": joblib.__version__},
        "warnings": [
            "Load .joblib files only from sources you trust: they can run code when loaded.",
            "Use the same scikit-learn version (see versions) or the model may not load or may behave differently.",
            "The model learned from this company's past sales. Check its accuracy on new data before relying on it.",
        ],
    }


def joblib_bytes(model_bundle, df, source="app"):
    model, features, _metrics = model_bundle
    buffer = io.BytesIO()
    joblib.dump({"model": model, "features": list(features), "model_card": model_card(model_bundle, df, source)}, buffer, compress=3)
    return buffer.getvalue()


USE_MODEL = '''"""Score a sales file with the downloaded model.

    python use_model.py sales.csv            (or sales.xlsx)   ->  writes scored_sales.csv

Needs:  pip install pandas scikit-learn joblib openpyxl
The file needs the columns listed in model_card.json ("input_columns"), with these standard names:
Sales, Quantity, Discount, Order Date, Ship Date, Ship Mode, Segment, Region, Category, Sub-Category (only the ones listed).
A missing column is treated as unknown. Dates like 2024-03-25 are best.

SECURITY: .joblib files can run code when loaded. Load only a file you trust.
"""
import sys

import joblib
import numpy as np
import pandas as pd

package = joblib.load("profit_model.joblib")
model = package["model"]
needed = list(model.feature_names_in_)

path = sys.argv[1] if len(sys.argv) > 1 else "sales.csv"
data = pd.read_excel(path) if path.lower().endswith((".xlsx", ".xls", ".xlsm")) else pd.read_csv(path, encoding="utf-8-sig")

# columns the model calculates itself
if "Order Date" in data.columns:
    data["Order Date"] = pd.to_datetime(data["Order Date"], errors="coerce")
    if "Order Month" not in data.columns:
        data["Order Month"] = data["Order Date"].dt.month
    if "Order Year" not in data.columns:
        data["Order Year"] = data["Order Date"].dt.year
if "Ship Date" in data.columns and "Order Date" in data.columns and "Ship Days" not in data.columns:
    data["Ship Days"] = (pd.to_datetime(data["Ship Date"], errors="coerce") - data["Order Date"]).dt.days
if "Sales" in data.columns and "Quantity" in data.columns and "Unit Price" not in data.columns:
    quantity = pd.to_numeric(data["Quantity"], errors="coerce")
    data["Unit Price"] = pd.to_numeric(data["Sales"], errors="coerce") / quantity.where(quantity > 0)

for column in needed:
    if column not in data.columns:
        print(f"Warning: column '{column}' is missing, the model treats it as unknown.")
        data[column] = np.nan

probability = model.predict_proba(data[needed])[:, 1]
data["Profit Probability"] = probability.round(4)
data["Predicted Profitable"] = (probability >= 0.5).astype(int)
data["Risk Level"] = np.select([1 - probability >= 0.6, 1 - probability >= 0.3], ["High", "Medium"], default="Low")
data.to_csv("scored_sales.csv", index=False, encoding="utf-8-sig")
print(f"Done: {len(data)} rows -> scored_sales.csv")
'''

README_MODEL = """# Profit model | نموذج توقع الربحية

## English
1. Put `use_model.py` and `profit_model.joblib` in one folder, and install: `pip install pandas scikit-learn joblib openpyxl`.
2. Run `python use_model.py your_sales_file.csv` (or .xlsx). It writes `scored_sales.csv` with `Profit Probability`, `Predicted Profitable` and `Risk Level`.
3. To use the model inside your own code:
   ```python
   import joblib
   package = joblib.load("profit_model.joblib")      # only load files you trust
   model = package["model"]                          # a scikit-learn Pipeline
   probability = model.predict_proba(rows)[:, 1]     # rows = a DataFrame with the columns in model_card.json
   ```
4. `model_card.json` lists the input columns, the values seen in training, the accuracy and the library versions.

**Warnings:** a .joblib file can run code when it is loaded, so load it only from a source you trust. Use the same scikit-learn version as in `model_card.json`.
The model learned from one company's past sales. Always measure its accuracy on your newest data before using it for decisions.

## العربية
1. ضع `use_model.py` و`profit_model.joblib` في مجلد واحد وثبّت: `pip install pandas scikit-learn joblib openpyxl`.
2. شغّل `python use_model.py your_sales_file.csv` (أو xlsx). يكتب الملف `scored_sales.csv` فيه `Profit Probability` و`Predicted Profitable` و`Risk Level`.
3. للاستخدام داخل كودك: `joblib.load("profit_model.joblib")` ثم `package["model"].predict_proba(rows)[:, 1]` حيث `rows` جدول بالأعمدة المذكورة في `model_card.json`.
4. `model_card.json` يذكر الأعمدة المطلوبة والقيم التي رآها النموذج والدقة وإصدارات المكتبات.

**تحذيرات:** ملف joblib قد ينفّذ كوداً عند تحميله، فلا تحمّله إلا من مصدر موثوق. استخدم نفس إصدار scikit-learn المذكور في `model_card.json`.
النموذج تعلّم من مبيعات شركة واحدة في الماضي. قِس دقته على أحدث بياناتك قبل استخدامه في القرارات.
"""


def model_files(model_bundle, df, source="app"):
    """{file name: bytes} of the model package."""
    card = json.dumps(model_card(model_bundle, df, source), indent=2, ensure_ascii=False)
    return {
        MODEL_FILE: joblib_bytes(model_bundle, df, source),
        "model_card.json": card.encode("utf-8"),
        "use_model.py": USE_MODEL.encode("utf-8"),
        "README_MODEL.md": README_MODEL.encode("utf-8"),
    }


def model_package_zip(model_bundle, df, source="app"):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, content in model_files(model_bundle, df, source).items():
            archive.writestr(name, content)
    return buffer.getvalue()
