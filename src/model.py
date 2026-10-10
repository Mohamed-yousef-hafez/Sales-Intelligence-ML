import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, roc_auc_score, confusion_matrix,
)
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

FEATURES = [
    "Sales", "Quantity", "Discount", "Ship Days",
    "Order Month", "Order Year", "Ship Mode", "Segment",
    "Region", "Category", "Sub-Category",
]


def build_model(df):
    available = [column for column in FEATURES if column in df.columns]
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
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ])
        transformers.append(("cat", categorical_pipe, categorical))

    preprocessor = ColumnTransformer(transformers=transformers)
    classifier = RandomForestClassifier(
        n_estimators=150,
        max_depth=10,
        random_state=42,
        class_weight="balanced",
        n_jobs=-1,
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


def train_and_evaluate(df):
    pipeline, features = build_model(df)
    X = df[features].copy()
    y = df["Profitable"].astype(int)
    X_train, X_test, y_train, y_test, split_strategy = _make_split(df, X, y)

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
        "test_size": len(y_test),
        "train_size": len(y_train),
        "split_strategy": split_strategy,
    }
    return pipeline, features, metrics


def predict_one(model, row):
    input_frame = pd.DataFrame([row])
    prediction = int(model.predict(input_frame)[0])
    probability = float(model.predict_proba(input_frame)[0, 1])
    return prediction, probability
