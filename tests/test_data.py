import pandas as pd
from src.data import clean_data

def test_clean_data():
    df = pd.DataFrame({
        "Sales": [100, 50, 20],
        "Profit": [20, -5, 2],
        "Discount": [0.1, 0.5, 0.0],
        "Quantity": [2, 1, 3],
        "Order Date": ["2024-01-01", "2024-01-02", "2024-01-03"],
        "Ship Date": ["2024-01-03", "2024-01-05", "2024-01-04"]
    })
    out = clean_data(df)
    assert "Profitable" in out.columns
    assert len(out) == 3
    assert out["Profitable"].tolist() == [1, 0, 1]
