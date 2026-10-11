import pandas as pd
from src.data import clean_data
from src.model import train_and_evaluate, predict_one


def make_df():
    rows = []
    for i in range(30):
        rows.append({
            "Sales": 100 + i,
            "Profit": 10 if i % 3 else -5,
            "Discount": 0.1,
            "Quantity": 2,
            "Order Date": f"2024-01-{(i % 9) + 1:02d}",
            "Ship Date": f"2024-01-{(i % 9) + 3:02d}",
            "Ship Mode": "Standard Class",
            "Segment": "Consumer",
            "Region": "West",
            "Category": "Technology",
            "Sub-Category": "Phones",
        })
    return pd.DataFrame(rows)


def test_model_training():
    df, _ = clean_data(make_df())
    _, _, metrics = train_and_evaluate(df)
    assert 0 <= metrics["accuracy"] <= 1
    assert 0 <= metrics["roc_auc"] <= 1


def test_predict_one():
    df, _ = clean_data(make_df())
    model, features, _ = train_and_evaluate(df)
    row = df.iloc[0][features].to_dict()
    prediction, probability = predict_one(model, row)
    assert prediction in (0, 1)
    assert 0 <= probability <= 1
