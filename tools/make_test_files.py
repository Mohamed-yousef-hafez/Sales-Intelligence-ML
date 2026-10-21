"""Creates test files for manual testing, plus expected.json with the correct result of each file.

    python tools/make_test_files.py            -> writes the files to  test_files/
    python tools/make_test_files.py my_folder  -> writes them to my_folder/

Dirty files are made from the demo data, so the CORRECT result is known: it is the clean data minus the rows that
were damaged on purpose (bad rows). The expected values come from the clean data, not from the cleaning code.
"""
import json
from pathlib import Path
import shutil
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.data import clean_data          # noqa: E402  (only used to compute the expected result of the clean data)
from src.security import prepare_table    # noqa: E402

MONTHS_AR = {1: "يناير", 2: "فبراير", 3: "مارس", 4: "أبريل", 5: "مايو", 6: "يونيو",
             7: "يوليو", 8: "أغسطس", 9: "سبتمبر", 10: "أكتوبر", 11: "نوفمبر", 12: "ديسمبر"}


def truth(frame):
    """What the cleaned file must contain (computed from clean data)."""
    cleaned, _ = clean_data(prepare_table(frame))
    return {"rows_after_cleaning": len(cleaned), "sales_total": round(float(cleaned["Sales"].sum()), 2),
            "profit_total": round(float(cleaned["Profit"].sum()), 2)}


def english():
    return pd.read_csv(ROOT / "data" / "sample_superstore.csv")


def arabic():
    return pd.read_csv(ROOT / "data" / "sample_arabic_sales.csv", encoding="utf-8-sig")


def unique_rows(frame):
    """Without identical rows: if two identical rows were damaged in different ways they would stop being duplicates,
    which would make the expected row count uncertain."""
    return frame.drop_duplicates().reset_index(drop=True)


def damage(frame, names, seed, with_months=True):
    """Damages a copy in many ways. Returns (dirty frame, indexes of rows that are truly bad)."""
    rng = np.random.default_rng(seed)
    dirty = frame.copy().astype(object)
    n = len(dirty)

    def pick(share):
        return rng.choice(n, int(n * share), replace=False)

    bad = set()
    rows = pick(0.05)
    dirty.loc[rows, names["category"]] = dirty.loc[rows, names["category"]].map(lambda v: " " + str(v).replace("أ", "ا").upper() + "  ")
    rows = pick(0.03)
    dirty.loc[rows, names["region"]] = rng.choice(["N/A", "-", "null", "غير متوفر", ""], len(rows))        # placeholders
    rows = pick(0.02); dirty.loc[rows, names["sales"]] = "N/A"; bad |= set(rows)                          # missing sales
    rows = pick(0.01); dirty.loc[rows, names["quantity"]] = 0; bad |= set(rows)                           # impossible quantity
    rows = pick(0.01); dirty.loc[rows, names["discount"]] = "150%"; bad |= set(rows)                      # impossible discount
    rows = pick(0.10)                                                                                    # currency text
    dirty.loc[rows, names["sales"]] = dirty.loc[rows, names["sales"]].map(lambda v: f"{v:,.2f} ج.م" if not isinstance(v, str) else v)
    if with_months:                                                                                      # dates with month names
        rows = pick(0.10)
        dates = pd.to_datetime(dirty.loc[rows, names["date"]], dayfirst=True, format="mixed")
        dirty.loc[rows, names["date"]] = [f"{d.day} {MONTHS_AR[d.month]} {d.year}" for d in dates]
    dirty = pd.concat([dirty, dirty.sample(40, random_state=seed)], ignore_index=True)                   # duplicates
    dirty = pd.concat([dirty, pd.DataFrame([{names["category"]: "الإجمالي", names["sales"]: 9e9, names["profit"]: 9e8}])],
                      ignore_index=True)                                                                  # a total row
    return dirty, sorted(bad)


def build_all(out):
    out = Path(out)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    expected = {}

    # 01 clean English (the demo itself)
    shutil.copy(ROOT / "data" / "sample_superstore.csv", out / "01_clean_english.csv")
    expected["01_clean_english.csv"] = {**truth(english()), "note": "no cleaning needed: 0 rows removed"}

    # 02 very dirty Arabic CSV with title lines on top
    base = unique_rows(arabic())
    names = {"category": "الفئة", "region": "المنطقة", "sales": "المبيعات", "quantity": "الكمية", "discount": "الخصم",
             "date": "تاريخ الطلب", "profit": "الربح"}
    dirty, bad = damage(base, names, seed=7)
    text = "تقرير مبيعات الشركة\nالفترة: 2023-2026\n\n" + dirty.to_csv(index=False)
    (out / "02_dirty_arabic.csv").write_bytes(text.encode("utf-8-sig"))
    expected["02_dirty_arabic.csv"] = {**truth(base.drop(index=bad)),
                                      "note": "title lines, total row, duplicates, placeholders, impossible values, Arabic month names"}

    # 03 dirty English Excel: first sheet is notes, Excel date numbers, a total row
    base = unique_rows(english().head(3000))
    names = {"category": "Category", "region": "Region", "sales": "Sales", "quantity": "Quantity", "discount": "Discount",
             "date": "Order Date", "profit": "Profit"}
    dirty, bad = damage(base, names, seed=11, with_months=False)
    dirty["Category"] = dirty["Category"].map(lambda v: v.replace("الإجمالي", "Total") if isinstance(v, str) else v)
    serial_rows = [i for i in range(0, len(base), 97) if i not in bad][:10]
    dirty.loc[serial_rows, "Order Date"] = [(pd.to_datetime(base.loc[i, "Order Date"], format="%m/%d/%Y") - pd.Timestamp("1899-12-30")).days
                                            for i in serial_rows]   # Excel stores dates as numbers
    with pd.ExcelWriter(out / "03_dirty_english.xlsx") as writer:
        pd.DataFrame({"Notes": ["Internal use only", "Sales are in the next sheet"]}).to_excel(writer, sheet_name="Notes", index=False)
        dirty.to_excel(writer, sheet_name="Sales 2023", index=False)
    expected["03_dirty_english.xlsx"] = {**truth(base.drop(index=bad)),
                                         "note": "2 sheets (data on the second), Excel date numbers, 'Total' row, case variants"}

    # 04 semicolon CSV with decimal comma in Arabic Windows encoding
    base = english().head(2000)[["Order Date", "Sales", "Profit", "Discount", "Quantity", "Category", "Product Name"]].drop_duplicates()
    (out / "04_semicolon_decimal_comma.csv").write_bytes(base.to_csv(index=False, sep=";", decimal=",").encode("cp1256", errors="replace"))
    expected["04_semicolon_decimal_comma.csv"] = {**truth(base), "note": "separator ; and decimal comma (16,448 means 16.448)"}

    # 05 cost instead of profit
    base = english().head(2000)[["Order Date", "Sales", "Profit", "Quantity", "Discount", "Category"]].drop_duplicates()
    cost = base.assign(Cost=(base["Sales"] - base["Profit"]).round(6)).drop(columns=["Profit"])
    cost.to_excel(out / "05_cost_instead_of_profit.xlsx", index=False)
    expected["05_cost_instead_of_profit.xlsx"] = {**truth(base), "note": "profit is calculated as Sales - Cost (report says so)"}

    # 06 minimal columns
    base = english()[["Order Date", "Sales", "Profit"]].drop_duplicates()
    base.to_csv(out / "06_minimal_columns.csv", index=False)
    expected["06_minimal_columns.csv"] = {**truth(base), "note": "only date, sales, profit: optional columns are skipped"}

    # 07 too little data for a model; 08 every sale profitable; 09 no date column
    small = english().head(25)[["Order Date", "Sales", "Profit", "Discount", "Quantity", "Category"]]
    small.to_csv(out / "07_not_enough_data.csv", index=False)
    expected["07_not_enough_data.csv"] = {**truth(small), "model_error_contains": "At least 30", "note": "dashboard works, model says why not"}
    allprofit = english().head(400).copy()
    allprofit["Profit"] = allprofit["Profit"].abs() + 1
    allprofit.to_csv(out / "08_all_profitable.csv", index=False)
    expected["08_all_profitable.csv"] = {**truth(allprofit), "model_error_contains": "at least 5 profitable", "note": "model cannot learn from one outcome"}
    english().head(100).drop(columns=["Order Date"]).to_csv(out / "09_missing_order_date.csv", index=False)
    expected["09_missing_order_date.csv"] = {"load_error_contains": "Order Date", "note": "clear bilingual error naming the missing column"}

    # 10 old .xls (needs xlwt, which is in requirements.txt)
    try:
        import xlwt
        sheet_data = english().head(50)[["Order Date", "Sales", "Profit"]]
        book = xlwt.Workbook()
        sheet = book.add_sheet("Sales")
        for j, name in enumerate(sheet_data.columns):
            sheet.write(0, j, name)
        for i, row in enumerate(sheet_data.itertuples(index=False), start=1):
            for j, value in enumerate(row):
                sheet.write(i, j, value if isinstance(value, str) else float(value))
        book.save(str(out / "10_old_excel.xls"))
        expected["10_old_excel.xls"] = {**truth(sheet_data.drop_duplicates()), "note": "old .xls format"}
    except ImportError:
        pass

    # 11 short history: only 6 months, so no forecast
    data = english()
    dates = pd.to_datetime(data["Order Date"], format="%m/%d/%Y")
    short = data[dates < "2023-07-01"]
    short.to_csv(out / "11_short_history.csv", index=False)
    expected["11_short_history.csv"] = {**truth(short), "forecast_status": "not_enough", "note": "6 months only: forecast says it needs 9"}

    # 12 two overlapping monthly files for refresh_exports.py --combine
    folder = out / "12_two_files_for_refresh"
    folder.mkdir()
    full = english()
    full.iloc[:3000].to_csv(folder / "a_part1.csv", index=False)
    full.iloc[2000:5000].to_csv(folder / "b_part2.csv", index=False)
    expected["12_two_files_for_refresh"] = {**truth(full.iloc[:5000]), "note": "use --combine; the 1000 overlapping rows are counted once"}

    (out / "expected.json").write_text(json.dumps(expected, indent=2, ensure_ascii=False), encoding="utf-8")
    return expected


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "test_files"
    result = build_all(target)
    print(f"Created {len(result)} test cases in {target}/ (see {target}/expected.json)")
    for name, info in result.items():
        rows = info.get("rows_after_cleaning", "-")
        print(f"  {name:36s} expected rows: {rows}   {info.get('note', '')}")
