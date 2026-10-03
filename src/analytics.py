import pandas as pd

def business_summary(df):
    sales = df["Sales"].sum()
    profit = df["Profit"].sum()
    margin = (profit / sales * 100) if sales else 0
    loss_orders = int((df["Profit"] <= 0).sum())

    return {
        "rows": len(df),
        "sales": sales,
        "profit": profit,
        "margin": margin,
        "loss_orders": loss_orders,
        "loss_rate": loss_orders / len(df) * 100 if len(df) else 0
    }

def category_profit(df):
    return df.groupby("Category", dropna=False)["Profit"].sum().sort_values(ascending=False)

def region_profit(df):
    return df.groupby("Region", dropna=False)["Profit"].sum().sort_values(ascending=False)

def monthly_profit(df):
    return (
        df.groupby(["Order Year", "Order Month"], dropna=False)[["Sales", "Profit"]]
        .sum()
        .reset_index()
        .sort_values(["Order Year", "Order Month"])
    )

def discount_profit(df):
    return df.groupby("Discount", dropna=False)["Profit"].mean().reset_index()
