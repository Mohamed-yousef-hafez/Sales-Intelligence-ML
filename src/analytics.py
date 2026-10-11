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


def profit_by(df, column, metric="Profit"):
    """Total Profit (or Sales) for each value of `column`, sorted from highest to lowest."""
    return df.groupby(column, dropna=False)[metric].sum().sort_values(ascending=False)


def group_summary(df, column, value):
    """Sales, profit, margin and loss rate for one value, for example Category == 'Furniture'."""
    subset = df[df[column].astype(str) == str(value)]
    sales = subset["Sales"].sum()
    profit = subset["Profit"].sum()
    return {
        "orders": len(subset),
        "sales": sales,
        "profit": profit,
        "margin": profit / sales * 100 if sales else 0,
        "loss_rate": (subset["Profit"] <= 0).mean() * 100 if len(subset) else 0,
    }


def group_table(df, column):
    """Orders, sales, profit, margin and loss rate for every value of `column` (fast, one pass)."""
    grouped = df.assign(_loss=(df["Profit"] <= 0).astype(float)).groupby(column, dropna=True)
    table = grouped.agg(orders=("Profit", "size"), sales=("Sales", "sum"), profit=("Profit", "sum"), loss_rate=("_loss", "mean"))
    table["margin"] = (table["profit"] / table["sales"].where(table["sales"] != 0) * 100).fillna(0)
    table["loss_rate"] = table["loss_rate"] * 100
    return table
