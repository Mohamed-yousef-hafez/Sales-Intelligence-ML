"""Files the user can download: cleaned data, quality report and an Excel template."""
import io

import pandas as pd

from .i18n import COLUMN_LABELS_AR

# Excel runs text that starts with one of these as a formula (CSV/formula injection).
FORMULA_STARTS = ("=", "+", "-", "@", "\t", "\r")


def protect_text(value):
    if isinstance(value, str) and value.startswith(FORMULA_STARTS):
        return "'" + value
    return value


def clean_csv_bytes(df):
    """UTF-8 with BOM, so Excel opens Arabic text correctly. Text cells are protected against formulas."""
    out = df.copy()
    for column in out.select_dtypes(include=["object", "string"]).columns:
        out[column] = out[column].map(protect_text)
    return out.to_csv(index=False).encode("utf-8-sig")


def report_csv_bytes(report_df):
    return clean_csv_bytes(report_df)


# ---------------------------------------------------------------------------- template
TEMPLATE_COLUMNS = [
    "Order Date", "Category", "Sub-Category", "Product", "Customer", "Region", "Segment",
    "Ship Mode", "Quantity", "Sales", "Discount", "Profit",
]

TEMPLATE_ROWS = {
    "en": [
        ["2024-03-25", "Furniture", "Chairs", "Office Chair", "Customer A", "West", "Corporate", "Standard Class", 2, 450.0, "10%", 80.0],
        ["2024-03-26", "Technology", "Phones", "Smartphone X", "Customer B", "East", "Consumer", "First Class", 1, 900.0, "0%", 150.0],
        ["2024-03-27", "Office Supplies", "Paper", "A4 Paper Box", "Customer C", "South", "Home Office", "Same Day", 10, 120.0, "30%", -15.0],
    ],
    "ar": [
        ["25/03/2024", "أثاث", "كراسي", "كرسي مكتب", "عميل أ", "الغرب", "شركات", "شحن عادي", 2, 450.0, "10%", 80.0],
        ["26/03/2024", "تكنولوجيا", "هواتف", "هاتف ذكي", "عميل ب", "الشرق", "أفراد", "شحن مميز", 1, 900.0, "0%", 150.0],
        ["27/03/2024", "مستلزمات مكتبية", "ورق", "علبة ورق A4", "عميل ج", "الجنوب", "مكتب منزلي", "نفس اليوم", 10, 120.0, "30%", -15.0],
    ],
}

# (column, required, description) in both languages.
TEMPLATE_NOTES = [
    ("Order Date", "yes", "Date of the sale (25/03/2024 or 2024-03-25 or 25 March 2024)", "تاريخ عملية البيع (25/03/2024 أو 2024-03-25 أو 25 مارس 2024)"),
    ("Sales", "yes", "Sales amount of the line", "قيمة المبيعات للسطر"),
    ("Profit", "yes*", "Profit of the line. *If you do not have it, add a Cost column instead (Profit = Sales - Cost)", "ربح السطر. *إن لم يتوفر أضف عمود التكلفة بدلاً منه (الربح = المبيعات − التكلفة)"),
    ("Discount", "no", "Discount as 0.1, 10 or 10%", "الخصم بصيغة 0.1 أو 10 أو 10%"),
    ("Quantity", "no", "Number of units sold", "عدد الوحدات المباعة"),
    ("Category", "no", "Product category", "فئة المنتج"),
    ("Sub-Category", "no", "Product sub-category", "الفئة الفرعية للمنتج"),
    ("Product", "no", "Product name", "اسم المنتج"),
    ("Customer", "no", "Customer name", "اسم العميل"),
    ("Region", "no", "Region / governorate", "المنطقة / المحافظة"),
    ("Segment", "no", "Customer segment", "شريحة العملاء"),
    ("Ship Mode", "no", "Shipping method", "طريقة الشحن"),
]


def template_xlsx_bytes(lang):
    """An Excel file with the right column names, three example rows and a notes sheet."""
    headers = [COLUMN_LABELS_AR[c] if lang == "ar" else c for c in TEMPLATE_COLUMNS]
    data_sheet = pd.DataFrame(TEMPLATE_ROWS[lang], columns=headers)
    if lang == "ar":
        notes = [
            (COLUMN_LABELS_AR[c], ("لا" if r == "no" else "نعم") + ("*" if r == "yes*" else ""), d_ar)
            for c, r, _, d_ar in TEMPLATE_NOTES
        ]
        notes_sheet = pd.DataFrame(notes, columns=["العمود", "مطلوب", "الوصف"])
        data_name, notes_name = "المبيعات", "ملاحظات"
    else:
        notes = [(c, "Yes*" if r == "yes*" else ("Yes" if r == "yes" else "No"), d_en) for c, r, d_en, _ in TEMPLATE_NOTES]
        notes_sheet = pd.DataFrame(notes, columns=["Column", "Required", "Description"])
        data_name, notes_name = "Sales", "Notes"
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        data_sheet.to_excel(writer, sheet_name=data_name, index=False)
        notes_sheet.to_excel(writer, sheet_name=notes_name, index=False)
        for sheet in writer.sheets.values():
            for column_cells in sheet.columns:
                width = max(len(str(cell.value)) if cell.value is not None else 0 for cell in column_cells)
                sheet.column_dimensions[column_cells[0].column_letter].width = min(max(width + 2, 12), 70)
    return buffer.getvalue()
