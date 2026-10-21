"""Monthly forecast of Sales or Profit.

Simple and explainable: several easy methods are tested on the PAST months of the company's own data
(backtest), the most accurate one is used, and it is compared with the simplest possible guess
("next month = last month"). The result says honestly how reliable the forecast is.
"""
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

from .i18n import TEXT

MIN_MONTHS = 9            # complete months needed (6 to learn from + at least 3 to test on)
MAX_BACKTEST = 6          # test on the last 6 months at most
PARTIAL_DAYS = 5          # a month that ends 5+ days before its last calendar day is "incomplete"


# Names shown to the user ("Sales", "المبيعات", ...) -> the column name used inside the program.
METRIC_NAMES = {"Sales": "Sales", "Profit": "Profit"}
for _lang in TEXT:
    METRIC_NAMES[TEXT[_lang]["fc_sales"]] = "Sales"
    METRIC_NAMES[TEXT[_lang]["fc_profit"]] = "Profit"


def normalize_metric(value):
    """'Sales' / 'Profit', whether we got the internal name or the label shown on the screen (in any language)."""
    return METRIC_NAMES.get(str(value).strip(), "Sales")


# ----------------------------------------------------------------------------- methods
# Each method gets the history `y` (numpy array of monthly values, oldest first), the calendar month number
# of every history value (1..12) and the number of months to forecast. It returns the forecast
# or None when there is not enough history for that method.
def naive(y, months, horizon):
    return np.repeat(y[-1], horizon)


def moving_average(y, months, horizon):
    return np.repeat(y[-3:].mean(), horizon)


def seasonal_naive(y, months, horizon):
    if len(y) < 12:
        return None
    return np.array([y[-12 + (step % 12)] for step in range(horizon)])


def seasonal_level(y, months, horizon):
    """Recent level (average of the last 12 months) x the usual strength of each calendar month."""
    if len(y) < 24 or y.mean() == 0:
        return None
    level = y[-12:].mean()
    factors = {m: y[months == m].mean() / y.mean() for m in range(1, 13) if (months == m).any()}
    future_months = [(months[-1] + step) % 12 + 1 for step in range(horizon)]
    return np.array([level * factors.get(m, 1.0) for m in future_months])


def trend_seasonal(y, months, horizon):
    if len(y) < 24:
        return None
    def features(t, month_numbers):
        dummies = np.array([[1.0 if m == k else 0.0 for k in range(2, 13)] for m in month_numbers])
        return np.column_stack([t, dummies])
    t = np.arange(len(y))
    model = LinearRegression().fit(features(t, months), y)
    future_t = np.arange(len(y), len(y) + horizon)
    future_months = [(months[-1] + step) % 12 + 1 for step in range(horizon)]
    return model.predict(features(future_t, future_months))


METHODS = {
    "naive": naive,
    "moving_average": moving_average,
    "seasonal_naive": seasonal_naive,
    "seasonal_level": seasonal_level,
    "trend_seasonal": trend_seasonal,
}


# ----------------------------------------------------------------------------- monthly history
def monthly_totals(df, metric):
    """Total per calendar month. Returns (series, notes). Incomplete first/last months are dropped."""
    dates = df["Order Date"]
    monthly = df.groupby(dates.dt.to_period("M"))[metric].sum()
    notes = {"dropped_first": None, "dropped_last": None, "gap_months": 0}

    last_period = dates.max().to_period("M")
    if (last_period.end_time.normalize() - dates.max().normalize()).days >= PARTIAL_DAYS and len(monthly) > 1:
        monthly = monthly.drop(last_period, errors="ignore")
        notes["dropped_last"] = last_period
    first_period = dates.min().to_period("M")
    if dates.min().day > PARTIAL_DAYS and len(monthly) > 1:
        monthly = monthly.drop(first_period, errors="ignore")
        notes["dropped_first"] = first_period

    full_range = pd.period_range(monthly.index.min(), monthly.index.max(), freq="M")
    notes["gap_months"] = len(full_range) - len(monthly)
    return monthly.reindex(full_range, fill_value=0.0), notes   # months without any sale count as 0


def wape(actual, predicted):
    """Total absolute error divided by the total actual value (works even when some months are near zero)."""
    total = np.abs(actual).sum()
    return float(np.abs(actual - predicted).sum() / total) if total > 0 else float("inf")


def forecast_monthly(df, metric="Sales", horizon=3):
    """Forecast `metric` for the next `horizon` months. Always returns a dict; check result['status']."""
    metric = normalize_metric(metric)
    if metric not in df.columns:
        raise ValueError(f"The data has no '{metric}' column. | لا يوجد عمود '{metric}' في البيانات.")
    series, notes = monthly_totals(df, metric)
    result = {"metric": metric, "status": "ok", "history": series, "notes": notes, "n_months": len(series), "needed": MIN_MONTHS}
    if len(series) < MIN_MONTHS:
        result["status"] = "not_enough"
        return result

    y = series.to_numpy(dtype=float)
    months = np.array([p.month for p in series.index])

    # Backtest: for each of the last months, pretend we do not know it, forecast it, and compare.
    backtest_months = min(MAX_BACKTEST, len(y) - 6)
    origins = range(len(y) - backtest_months, len(y))
    errors = {}
    for name, method in METHODS.items():
        predictions = []
        for t in origins:
            forecast = method(y[:t], months[:t], 1)
            if forecast is None:
                predictions = None
                break
            predictions.append(forecast[0])
        if predictions is not None:
            errors[name] = (y[list(origins)], np.array(predictions))

    scores = {name: wape(actual, predicted) for name, (actual, predicted) in errors.items()}
    best = min(scores, key=scores.get)   # dict keeps the order of METHODS, so ties go to the simpler method
    baseline = scores["naive"]
    gain = baseline - scores[best]

    # Final forecast with the winner, and an approximate range from its own past mistakes.
    point = METHODS[best](y, months, horizon)
    actual, predicted = errors[best]
    spread = float(np.sqrt(np.mean((actual - predicted) ** 2)))
    steps = np.arange(1, horizon + 1)
    margin = 1.28 * spread * np.sqrt(steps)                    # about 80% of past mistakes fit inside
    lower, upper = point - margin, point + margin
    if metric == "Sales":
        lower = np.maximum(lower, 0)                           # sales cannot be negative
        point = np.maximum(point, 0)

    next_months = pd.period_range(series.index[-1] + 1, periods=horizon, freq="M")
    result["forecast"] = pd.DataFrame({"forecast": point, "lower": lower, "upper": upper}, index=next_months)
    result.update({
        "method": best,
        "scores": pd.Series(scores),
        "wape": scores[best],
        "baseline_wape": baseline,
        "gain": gain,
        "backtest_months": backtest_months,
    })

    # Rules of thumb for the verdict (shown to the user with the numbers behind them).
    if scores[best] > 0.35 or (gain < 0.01 and scores[best] > 0.20):
        result["verdict"] = "weak"
    elif scores[best] <= 0.15 and gain >= 0.03:   # strict: the best of 5 methods looks slightly better in the past than in the future
        result["verdict"] = "good"
    else:
        result["verdict"] = "ok"
    return result


def forecast_table(result):
    """Forecast as a flat table (for CSV / Power BI). One row per future month."""
    if result["status"] != "ok":
        return pd.DataFrame(columns=["Metric", "Month", "Forecast", "Lower", "Upper", "Method", "Backtest WAPE", "Baseline WAPE", "Reliability"])
    table = result["forecast"].copy()
    return pd.DataFrame({
        "Metric": result["metric"],
        "Month": table.index.to_timestamp(),
        "Forecast": table["forecast"].round(2).to_numpy(),
        "Lower": table["lower"].round(2).to_numpy(),
        "Upper": table["upper"].round(2).to_numpy(),
        "Method": result["method"],
        "Backtest WAPE": round(result["wape"], 4),
        "Baseline WAPE": round(result["baseline_wape"], 4),
        "Reliability": result["verdict"],
    })


def monthly_summary(df):
    """History per month for Power BI: sales, profit, orders and whether the month is complete."""
    dates = df["Order Date"]
    grouped = df.groupby(dates.dt.to_period("M")).agg(Sales=("Sales", "sum"), Profit=("Profit", "sum"), Orders=("Sales", "size"))
    complete_sales, notes = monthly_totals(df, "Sales")
    grouped["Month Complete"] = [int(period in complete_sales.index) for period in grouped.index]
    grouped["Margin"] = (grouped["Profit"] / grouped["Sales"].where(grouped["Sales"] != 0)).round(4)
    grouped[["Sales", "Profit"]] = grouped[["Sales", "Profit"]].round(2)
    grouped.insert(0, "Month", grouped.index.to_timestamp())
    return grouped.reset_index(drop=True)
