import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
)
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


FEATURES = [
    "Sales",
    "Quantity",
    "Discount",
    "Ship Days",
    "Order Month",
    "Order Year",
    "Ship Mode",
    "Segment",
    "Region",
    "Category",
    "Sub-Category",
]


def build_model(df):
    available = [c for c in FEATURES if c in df.columns]

    X = df[available].copy()
    y = df["Profitable"]

    categorical = [
        c for c in available
        if not pd.api.types.is_numeric_dtype(X[c])
    ]

    numeric = [
        c for c in available
        if pd.api.types.is_numeric_dtype(X[c])
    ]

    numeric_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
    ])

    categorical_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        (
            "onehot",
            OneHotEncoder(
                handle_unknown="ignore",
                sparse_output=False,
            ),
        ),
    ])

    transformers = []

    if numeric:
        transformers.append(
            ("num", numeric_pipe, numeric)
        )

    if categorical:
        transformers.append(
            ("cat", categorical_pipe, categorical)
        )

    preprocessor = ColumnTransformer(
        transformers=transformers
    )

    clf = RandomForestClassifier(
        n_estimators=150,
        max_depth=10,
        random_state=42,
        class_weight="balanced",
    )

    pipe = Pipeline([
        ("preprocessor", preprocessor),
        ("classifier", clf),
    ])

    return pipe, available


def train_and_evaluate(df):
    pipe, features = build_model(df)

    X = df[features].copy()
    y = df["Profitable"]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=42,
        stratify=y,
    )

    pipe.fit(X_train, y_train)

    pred = pipe.predict(X_test)
    proba = pipe.predict_proba(X_test)[:, 1]

    metrics = {
        "accuracy": accuracy_score(y_test, pred),
        "precision": precision_score(
            y_test,
            pred,
            zero_division=0,
        ),
        "recall": recall_score(
            y_test,
            pred,
            zero_division=0,
        ),
        "f1": f1_score(
            y_test,
            pred,
            zero_division=0,
        ),
        "roc_auc": roc_auc_score(
            y_test,
            proba,
        ),
        "confusion_matrix": confusion_matrix(
            y_test,
            pred,
        ).tolist(),
        "test_size": len(y_test),
    }

    return pipe, features, metrics


def predict_one(model, row):
    x = pd.DataFrame([row])

    pred = int(model.predict(x)[0])

    probability = float(
        model.predict_proba(x)[0, 1]
    )

    return pred, probability