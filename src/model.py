import os
import warnings

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, roc_auc_score, confusion_matrix,
)
from sklearn.model_selection import TimeSeriesSplit, train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

FEATURES = [
    "Sales", "Quantity", "Discount", "Ship Days",
    "Order Month", "Order Year", "Ship Mode", "Segment",
    "Region", "Category", "Sub-Category",
]
# Unit Price = Sales / Quantity. It is calculated automatically (the user does not type it).
MODEL_FEATURES = FEATURES + ["Unit Price"]

# How many CPU cores the forest may use. -1 = all of them. If training feels slow on your computer, try 1:
#   PowerShell:  $env:SALES_ML_JOBS="1"     CMD:  set SALES_ML_JOBS=1     Linux/Mac:  export SALES_ML_JOBS=1
#   (then start the app again in the same window)
N_JOBS = int(os.environ.get("SALES_ML_JOBS", "-1"))

# Some scikit-learn/joblib version pairs print this warning for every tree batch. It does not change any result here
# (we use no custom scikit-learn settings), but it fills the screen, so it is hidden.
warnings.filterwarnings("ignore", message=".*sklearn.utils.parallel.delayed.*", category=UserWarning)


def add_unit_price(frame):
    frame = frame.copy()
    if "Sales" in frame.columns and "Quantity" in frame.columns:
        quantity = pd.to_numeric(frame["Quantity"], errors="coerce")
        frame["Unit Price"] = pd.to_numeric(frame["Sales"], errors="coerce") / quantity.where(quantity > 0)
    return frame


def build_model(df):
    available = [column for column in MODEL_FEATURES if column in df.columns]
    if not available:
        raise ValueError("No supported model features were found in the dataset.")
    if "Profitable" not in df.columns:
        raise ValueError("The target column 'Profitable' is missing. Run clean_data() first.")

    X = df[available].copy()
    y = df["Profitable"].astype(int)

    # Detect pandas object, string, category, and other non-numeric columns safely.
    categorical = [
        column for column in available
        if not pd.api.types.is_numeric_dtype(X[column].dtype)
    ]
    numeric = [column for column in available if column not in categorical]

    transformers = []
    if numeric:
        numeric_pipe = Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
        ])
        transformers.append(("num", numeric_pipe, numeric))

    if categorical:
        categorical_pipe = Pipeline([
            ("imputer", SimpleImputer(strategy="most_frequent")),
            # Many different values (for example 200 sub-categories): keep the 30 most common, group the rest.
            ("onehot", OneHotEncoder(handle_unknown="infrequent_if_exist", max_categories=30)),
        ])
        transformers.append(("cat", categorical_pipe, categorical))

    preprocessor = ColumnTransformer(transformers=transformers)
    classifier = RandomForestClassifier(
        n_estimators=150,
        max_depth=10,
        random_state=42,
        class_weight="balanced",
        n_jobs=N_JOBS,
    )
    pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("classifier", classifier),
    ])
    return pipeline, available


def _make_split(df, X, y):
    # Prefer a chronological holdout for a more realistic estimate on future sales.
    if "Order Date" in df.columns:
        dates = pd.to_datetime(df["Order Date"], errors="coerce")
        valid = dates.notna()
        if valid.all() and dates.nunique() >= 3:
            ordered_dates = dates.sort_values().drop_duplicates().reset_index(drop=True)
            cutoff_index = max(1, min(len(ordered_dates) - 1, int(len(ordered_dates) * 0.8)))
            cutoff_date = ordered_dates.iloc[cutoff_index]
            train_mask = dates < cutoff_date
            test_mask = dates >= cutoff_date
            if train_mask.sum() and test_mask.sum():
                y_train, y_test = y.loc[train_mask], y.loc[test_mask]
                if y_train.nunique() == 2 and y_test.nunique() == 2:
                    return X.loc[train_mask], X.loc[test_mask], y_train, y_test, "chronological"

    # Small/demo datasets may not contain both classes in a chronological holdout.
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )
    return X_train, X_test, y_train, y_test, "stratified_random_fallback"


MIN_ROWS = 30
MIN_PER_CLASS = 5


def check_data_is_enough(df):
    """Give a clear message instead of a technical crash when the data cannot train a model."""
    if len(df) < MIN_ROWS:
        raise ValueError(
            f"At least {MIN_ROWS} valid rows are needed to train the model (found {len(df)}). | "
            f"يلزم {MIN_ROWS} صفاً صالحاً على الأقل لتدريب النموذج (الموجود {len(df)})."
        )
    counts = df["Profitable"].value_counts()
    if len(counts) < 2 or counts.min() < MIN_PER_CLASS:
        raise ValueError(
            f"The model needs at least {MIN_PER_CLASS} profitable and {MIN_PER_CLASS} loss-making sales to learn the "
            "difference. The dashboard and the assistant still work. | "
            f"يحتاج النموذج {MIN_PER_CLASS} عمليات رابحة و{MIN_PER_CLASS} خاسرة على الأقل ليتعلّم الفرق. "
            "اللوحة والمساعد يعملان بشكل طبيعي."
        )


def train_and_evaluate(df):
    check_data_is_enough(df)
    df = add_unit_price(df)
    pipeline, model_columns = build_model(df)
    X = df[model_columns].copy()
    y = df["Profitable"].astype(int)
    X_train, X_test, y_train, y_test, split_strategy = _make_split(df, X, y)
    features = [column for column in model_columns if column != "Unit Price"]  # what the user can type

    pipeline.fit(X_train, y_train)
    predictions = pipeline.predict(X_test)
    probabilities = pipeline.predict_proba(X_test)[:, 1]

    metrics = {
        "accuracy": accuracy_score(y_test, predictions),
        "precision": precision_score(y_test, predictions, zero_division=0),
        "recall": recall_score(y_test, predictions, zero_division=0),
        "f1": f1_score(y_test, predictions, zero_division=0),
        "roc_auc": roc_auc_score(y_test, probabilities) if y_test.nunique() == 2 else float("nan"),
        "confusion_matrix": confusion_matrix(y_test, predictions, labels=[0, 1]).tolist(),
        "baseline_accuracy": float(max(y_test.mean(), 1 - y_test.mean())),  # always predict the common class
        "test_size": len(y_test),
        "train_size": len(y_train),
        "split_strategy": split_strategy,
        "train_index": X_train.index.to_numpy(),   # which rows were used for training (needed when scoring all rows)
    }
    return pipeline, features, metrics


def predict_one(model, row):
    input_frame = add_unit_price(pd.DataFrame([row]))
    input_frame = input_frame[list(model.feature_names_in_)]
    prediction = int(model.predict(input_frame)[0])
    probability = float(model.predict_proba(input_frame)[0, 1])
    return prediction, probability


def feature_importance(model):
    """Importance of each original column (one-hot columns are added back together), highest first."""
    names = model.named_steps["preprocessor"].get_feature_names_out()
    values = model.named_steps["classifier"].feature_importances_
    columns = list(model.feature_names_in_)
    totals = {}
    for name, value in zip(names, values):
        encoded_name = name.split("__", 1)[1]
        matches = [c for c in columns if encoded_name == c or encoded_name.startswith(c + "_")]
        column = max(matches, key=len) if matches else encoded_name
        totals[column] = totals.get(column, 0) + float(value)
    return pd.Series(totals).sort_values(ascending=False)


# ----------------------------------------------------------------------------- scoring
def score_dataframe(model, df, train_index=None):
    """Add the model's opinion to every row: profit probability, prediction and risk level.
    Column names are always English so Power BI reports keep working."""
    data = add_unit_price(df)
    probability = model.predict_proba(data[list(model.feature_names_in_)])[:, 1]
    loss_probability = 1 - probability
    scored = df.copy()
    scored["Profit Probability"] = probability.round(4)
    scored["Predicted Profitable"] = (probability >= 0.5).astype(int)
    scored["Risk Level"] = np.select([loss_probability >= 0.6, loss_probability >= 0.3], ["High", "Medium"], default="Low")
    if train_index is not None:
        # Rows the model learned from have optimistic predictions. Judge the model on rows with 0.
        scored["In Training Set"] = df.index.isin(train_index).astype(int)
    return scored


# ----------------------------------------------------------------------------- reliability check
def cross_validate_time(df, folds=5):
    """Train on the past and test on the next period, several times (expanding window).
    This shows how the model behaves on YOUR data, and compares it with the best constant guess."""
    check_data_is_enough(df)
    data = add_unit_price(df).sort_values("Order Date").reset_index(drop=True)
    pipeline, model_columns = build_model(data)
    X = data[model_columns]
    y = data["Profitable"].astype(int)
    if len(data) > 50_000:
        folds = min(folds, 3)  # keep it fast on very large files

    rows = []
    for number, (train_idx, test_idx) in enumerate(TimeSeriesSplit(n_splits=folds).split(X), start=1):
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
        if y_train.nunique() < 2 or y_test.nunique() < 2:
            continue  # a period with only one outcome cannot be judged
        fold_model = clone(pipeline).fit(X.iloc[train_idx], y_train)
        predictions = fold_model.predict(X.iloc[test_idx])
        probabilities = fold_model.predict_proba(X.iloc[test_idx])[:, 1]
        rows.append({
            "fold": number,
            "start": data["Order Date"].iloc[test_idx].min(),
            "end": data["Order Date"].iloc[test_idx].max(),
            "train_rows": len(train_idx),
            "test_rows": len(test_idx),
            "accuracy": accuracy_score(y_test, predictions),
            "baseline": float(max(y_test.mean(), 1 - y_test.mean())),   # best constant guess
            "f1": f1_score(y_test, predictions, zero_division=0),
            "roc_auc": roc_auc_score(y_test, probabilities),
        })
    return pd.DataFrame(rows)


def reliability_verdict(folds):
    """Turn the per-period results into one clear verdict: strong, moderate, weak or not_enough."""
    if len(folds) < 2:
        return {"verdict": "not_enough", "folds": len(folds)}
    gain = folds["accuracy"] - folds["baseline"]
    summary = {
        "folds": len(folds),
        "accuracy": float(folds["accuracy"].mean()),
        "baseline": float(folds["baseline"].mean()),
        "gain": float(gain.mean()),
        "min_gain": float(gain.min()),
        "roc_auc": float(folds["roc_auc"].mean()),
        "spread": float(folds["accuracy"].std(ddof=0)),
    }
    if summary["roc_auc"] < 0.65 or summary["gain"] < 0.02:
        summary["verdict"] = "weak"
    elif summary["roc_auc"] >= 0.80 and summary["gain"] >= 0.05 and summary["min_gain"] > 0:
        summary["verdict"] = "strong"
    else:
        summary["verdict"] = "moderate"
    return summary
