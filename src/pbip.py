"""Builds a ready Power BI dashboard as a Power BI Project (PBIP).

A PBIP is a folder of plain text files that Power BI Desktop opens directly:
    Sales Dashboard.pbip
    Sales Dashboard.SemanticModel/   the data model in TMDL (tables, relationships, DAX measures)
    Sales Dashboard.Report/          the report in PBIR (pages and visuals as JSON)
The data model reads the tables of power_bi_data.xlsx (the single Excel file made by the app).
The dashboard adapts to the columns that exist: no Discount column -> no discount visuals, and so on.

Formats: https://learn.microsoft.com/power-bi/developer/projects/projects-report (PBIR),
         https://learn.microsoft.com/analysis-services/tmdl/tmdl-overview (TMDL).
The JSON files follow Microsoft's published JSON schemas (tools/validate_pbip.py checks this).
"""
import json
import re
import textwrap
import uuid

import pandas as pd

PROJECT_NAME = "Sales Dashboard"
DEFAULT_DATA_FILE = r"C:\SalesIntelligence\power_bi_data.xlsx"

SCHEMA = "https://developer.microsoft.com/json-schemas/fabric"
SCHEMAS = {
    "pbip": f"{SCHEMA}/pbip/pbipProperties/1.0.0/schema.json",
    "platform": f"{SCHEMA}/gitIntegration/platformProperties/2.0.0/schema.json",
    "pbir": f"{SCHEMA}/item/report/definitionProperties/2.0.0/schema.json",
    "pbism": f"{SCHEMA}/item/semanticModel/definitionProperties/1.0.0/schema.json",
    "version": f"{SCHEMA}/item/report/definition/versionMetadata/1.0.0/schema.json",
    "report": f"{SCHEMA}/item/report/definition/report/2.1.0/schema.json",
    "pages": f"{SCHEMA}/item/report/definition/pagesMetadata/1.0.0/schema.json",
    "page": f"{SCHEMA}/item/report/definition/page/2.0.0/schema.json",
    "visual": f"{SCHEMA}/item/report/definition/visualContainer/2.1.0/schema.json",
}


def guid(name):
    """The same name always gives the same id, so regenerating a project does not change it."""
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "sales-intelligence/" + name))


def quote(name):
    """TMDL names that contain spaces or symbols need single quotes."""
    return name if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name) else "'" + name.replace("'", "''") + "'"


def text_value(value):
    return '"' + value.replace('"', '""') + '"'


# =============================================================================== texts of the dashboard
DASH_TEXT = {
    "en": {
        "overview": "Overview", "forecast": "Forecast", "risk": "Loss risk", "quality": "Data quality",
        "monthly": "Sales and profit by month", "by_category": "Profit by category", "by_region": "Profit by region",
        "by_discount": "Average profit per order by discount level", "products": "Products ranked by profit",
        "fc_sales": "Sales forecast (with likely range)", "fc_profit": "Profit forecast", "fc_table": "Forecast details",
        "risk_levels": "Orders by risk level", "risk_category": "Average profit probability by category",
        "risk_matrix": "Orders by region and risk level", "risk_products": "Products with the most high-risk orders",
        "quality_table": "Data quality report", "model_table": "Model quality", "status_table": "Last refresh",
    },
    "ar": {
        "overview": "نظرة عامة", "forecast": "التوقعات", "risk": "مخاطر الخسارة", "quality": "جودة البيانات",
        "monthly": "المبيعات والربح شهرياً", "by_category": "الربح حسب الفئة", "by_region": "الربح حسب المنطقة",
        "by_discount": "متوسط ربح الطلب حسب مستوى الخصم", "products": "المنتجات مرتبة حسب الربح",
        "fc_sales": "توقع المبيعات (مع المدى المحتمل)", "fc_profit": "توقع الربح", "fc_table": "تفاصيل التوقع",
        "risk_levels": "الطلبات حسب مستوى المخاطرة", "risk_category": "متوسط احتمال الربح حسب الفئة",
        "risk_matrix": "الطلبات حسب المنطقة ومستوى المخاطرة", "risk_products": "المنتجات الأكثر طلبات عالية المخاطرة",
        "quality_table": "تقرير جودة البيانات", "model_table": "جودة النموذج", "status_table": "آخر تحديث",
    },
}


# =============================================================================== data model (TMDL)
# kind -> (TMDL dataType, Power Query type, TMDL formatString)
TYPES = {
    "text": ("string", "type text", None),
    "int": ("int64", "Int64.Type", "0"),
    "number": ("double", "type number", "#,0.00"),
    "date": ("dateTime", "type date", "yyyy-mm-dd"),
}


class Col:
    def __init__(self, name, kind, hidden=False, sort_by=None, key=False, in_source=True):
        self.name, self.kind, self.hidden, self.sort_by, self.key, self.in_source = name, kind, hidden, sort_by, key, in_source


def kind_of(series):
    if pd.api.types.is_datetime64_any_dtype(series):
        return "date"
    if pd.api.types.is_bool_dtype(series):
        return "int"
    if pd.api.types.is_integer_dtype(series):
        return "int"
    if pd.api.types.is_float_dtype(series):
        return "number"
    return "text"


# The small tables have fixed columns (see src/powerbi.py), so their types do not depend on the data.
FORECAST_COLUMNS = [Col("Metric", "text"), Col("Month", "date"), Col("Forecast", "number"), Col("Lower", "number"),
                    Col("Upper", "number"), Col("Method", "text"), Col("Backtest WAPE", "number"),
                    Col("Baseline WAPE", "number"), Col("Reliability", "text")]
MONTHLY_COLUMNS = [Col("Month", "date"), Col("Sales", "number"), Col("Profit", "number"), Col("Orders", "int"),
                   Col("Month Complete", "int"), Col("Margin", "number")]
QUALITY_COLUMNS = [Col("Metric", "text"), Col("Value", "text")]
MODEL_COLUMNS = [Col("Metric", "text"), Col("Value", "number"), Col("Note", "text")]
STATUS_COLUMNS = [Col("Last Refresh", "text"), Col("Status", "text"), Col("Source", "text"),
                  Col("Rows Loaded", "int"), Col("Rows After Cleaning", "int"), Col("Message", "text")]
DATE_COLUMNS = [Col("Date", "date", key=True, in_source=True), Col("Year", "int"), Col("Month Number", "int"),
                Col("Month Name", "text", sort_by="Month Number"), Col("Year-Month", "text")]

DISCOUNT_BANDS = [(0, "0%"), (0.1, "1-10%"), (0.2, "11-20%"), (0.3, "21-30%"), (0.5, "31-50%")]


def sales_columns(sales_frame):
    columns = [Col(str(name), kind_of(sales_frame[name])) for name in sales_frame.columns]
    if "Discount" in sales_frame.columns:
        columns.append(Col("Discount Band", "text", sort_by="Discount Band Order", in_source=False))
        columns.append(Col("Discount Band Order", "int", hidden=True, in_source=False))
    return columns


def excel_query(table, columns, extra_steps=""):
    """Power Query (M): read one Excel Table of the workbook and set the column types."""
    typed = ", ".join(f'{{"{c.name}", {TYPES[c.kind][1]}}}' for c in columns if c.in_source)
    lines = [
        "let",
        "\tSource = Excel.Workbook(File.Contents(DataFile), null, true),",
        f'\tTableData = Source{{[Item="{table}",Kind="Table"]}}[Data],',
        f"\tTyped = Table.TransformColumnTypes(TableData, {{{typed}}})" + ("," if extra_steps else ""),
    ]
    if extra_steps:
        lines += ["\t" + step for step in extra_steps.splitlines()]
    lines += ["in", "\t" + ("Final" if extra_steps else "Typed")]
    return lines


def discount_steps():
    band = "if [Discount] = null then \"Unknown\""
    order = "if [Discount] = null then 7"
    for index, (limit, label) in enumerate(DISCOUNT_BANDS, start=1):
        band += f' else if [Discount] <= {limit} then "{label}"'
        order += f" else if [Discount] <= {limit} then {index}"
    band += ' else "Above 50%"'
    order += " else 6"
    return (f'WithBand = Table.AddColumn(Typed, "Discount Band", each {band}, type text),\n'
            f'Final = Table.AddColumn(WithBand, "Discount Band Order", each {order}, Int64.Type)')


def date_query():
    return [
        "let",
        "\tSource = Excel.Workbook(File.Contents(DataFile), null, true),",
        '\tSalesData = Source{[Item="Sales",Kind="Table"]}[Data],',
        '\tOrderDates = List.Transform(SalesData[#"Order Date"], each Date.From(_)),',
        "\tFirstYear = Date.Year(List.Min(OrderDates)),",
        "\tLastYear = Date.Year(List.Max(OrderDates)) + 1,",
        "\tAllDates = List.Dates(#date(FirstYear, 1, 1), Duration.Days(#date(LastYear, 12, 31) - #date(FirstYear, 1, 1)) + 1, #duration(1, 0, 0, 0)),",
        '\tAsTable = Table.FromList(AllDates, Splitter.SplitByNothing(), {"Date"}, null, ExtraValues.Error),',
        '\tTyped = Table.TransformColumnTypes(AsTable, {{"Date", type date}}),',
        '\tWithYear = Table.AddColumn(Typed, "Year", each Date.Year([Date]), Int64.Type),',
        '\tWithMonth = Table.AddColumn(WithYear, "Month Number", each Date.Month([Date]), Int64.Type),',
        '\tWithName = Table.AddColumn(WithMonth, "Month Name", each Text.Start(Date.MonthName([Date], "en-US"), 3), type text),',
        '\tWithYearMonth = Table.AddColumn(WithName, "Year-Month", each Date.ToText([Date], [Format = "yyyy-MM", Culture = "en-US"]), type text)',
        "in",
        "\tWithYearMonth",
    ]


def column_tmdl(table, column):
    data_type, _, fmt = TYPES[column.kind]
    lines = [f"\tcolumn {quote(column.name)}", f"\t\tdataType: {data_type}"]
    if fmt:
        lines.append(f"\t\tformatString: {fmt}")
    if column.hidden:
        lines.append("\t\tisHidden")
    if column.key:
        lines.append("\t\tisKey")
    lines += [f"\t\tlineageTag: {guid(table + '.' + column.name)}", "\t\tsummarizeBy: none",
              f"\t\tsourceColumn: {text_value(column.name)}"]
    if column.sort_by:
        lines.append(f"\t\tsortByColumn: {quote(column.sort_by)}")
    lines += ["", "\t\tannotation SummarizationSetBy = Automatic"]
    if column.kind == "date":
        lines += ["", "\t\tannotation UnderlyingDateTimeDataType = Date"]
    return lines


def measure_tmdl(table, name, expression, fmt=None, folder=None):
    expression = textwrap.dedent(expression).strip("\n")
    if "\n" in expression:
        lines = [f"\tmeasure {quote(name)} ="] + ["\t\t\t" + line for line in expression.splitlines()]
    else:
        lines = [f"\tmeasure {quote(name)} = {expression}"]
    if fmt:
        lines.append(f"\t\tformatString: {fmt}")
    if folder:
        lines.append(f"\t\tdisplayFolder: {folder}")
    lines.append(f"\t\tlineageTag: {guid(table + '.' + name)}")
    return lines


def table_tmdl(name, columns, query_lines, measures=(), data_category=None):
    lines = [f"table {quote(name)}", f"\tlineageTag: {guid('table.' + name)}"]
    if data_category:
        lines.append(f"\tdataCategory: {data_category}")
    for column in columns:
        lines += [""] + column_tmdl(name, column)
    for measure in measures:
        lines += [""] + measure_tmdl(name, *measure)
    lines += ["", f"\tpartition {quote(name)} = m", "\t\tmode: import", "\t\tsource ="]
    lines += ["\t\t\t" + line for line in query_lines]
    return "\n".join(lines) + "\n"


# ------------------------------------------------------------------------------- measures (the same as powerbi/measures.dax)
def top_or_bottom(column, direction):
    name = "Top1" if direction == "DESC" else "Bottom1"
    return f"""
        VAR {name} = TOPN ( 1, ALLSELECTED ( Sales[{column}] ), [Total Profit], {direction} )
        RETURN MAXX ( {name}, Sales[{column}] )"""


def sales_measures(have, scored):
    """(name, DAX, formatString, displayFolder) for the Sales table. Only measures whose columns exist."""
    m = [
        ("Total Sales", "SUM ( Sales[Sales] )", "#,0", "KPIs"),
        ("Total Profit", "SUM ( Sales[Profit] )", "#,0", "KPIs"),
        ("Profit Margin %", "DIVIDE ( [Total Profit], [Total Sales] )", "0.00%", "KPIs"),
        ("Orders", "COUNTROWS ( Sales )", "#,0", "KPIs"),
        ("Loss Orders", "CALCULATE ( COUNTROWS ( Sales ), Sales[Profit] <= 0 )", "#,0", "KPIs"),
        ("Loss Rate %", "DIVIDE ( [Loss Orders], [Orders] )", "0.00%", "KPIs"),
        ("Avg Profit per Order", "DIVIDE ( [Total Profit], [Orders] )", "#,0.00", "KPIs"),
        ("Sales LY", "CALCULATE ( [Total Sales], SAMEPERIODLASTYEAR ( 'Date'[Date] ) )", "#,0", "Last year"),
        ("Sales YoY %", "DIVIDE ( [Total Sales] - [Sales LY], [Sales LY] )", "0.0%", "Last year"),
        ("Profit LY", "CALCULATE ( [Total Profit], SAMEPERIODLASTYEAR ( 'Date'[Date] ) )", "#,0", "Last year"),
        ("Profit YoY %", "DIVIDE ( [Total Profit] - [Profit LY], ABS ( [Profit LY] ) )", "0.0%", "Last year"),
        ("Profit Prev Month", "CALCULATE ( [Total Profit], DATEADD ( 'Date'[Date], -1, MONTH ) )", "#,0", "Last year"),
        ("Profit MoM Change", "[Total Profit] - [Profit Prev Month]", "#,0", "Last year"),
    ]
    if "Discount" in have:
        m.append(("Avg Discount", "AVERAGE ( Sales[Discount] )", "0.0%", "KPIs"))
    for column, label in (("Category", "Category"), ("Product", "Product"), ("Region", "Region")):
        if column in have:
            m.append((f"Best {label}", top_or_bottom(column, "DESC"), None, "Best and worst"))
            m.append((f"Worst {label}", top_or_bottom(column, "ASC"), None, "Best and worst"))
    if scored:
        m += [
            ("High Risk Orders", 'CALCULATE ( COUNTROWS ( Sales ), Sales[Risk Level] = "High" )', "#,0", "Model"),
            ("High Risk Sales Amount", 'CALCULATE ( [Total Sales], Sales[Risk Level] = "High" )', "#,0", "Model"),
            ("Predicted Loss Orders", "CALCULATE ( COUNTROWS ( Sales ), Sales[Predicted Profitable] = 0 )", "#,0", "Model"),
            ("Avg Profit Probability", "AVERAGE ( Sales[Profit Probability] )", "0.0%", "Model"),
            ("Model Accuracy Unseen", """
                VAR Unseen = FILTER ( Sales, Sales[In Training Set] = 0 )
                RETURN
                    DIVIDE (
                        COUNTROWS ( FILTER ( Unseen, Sales[Predicted Profitable] = Sales[Profitable] ) ),
                        COUNTROWS ( Unseen )
                    )""", "0.0%", "Model"),
        ]
    return m


def forecast_measures():
    return [
        ("Forecast Sales", 'CALCULATE ( SUM ( Forecast[Forecast] ), Forecast[Metric] = "Sales" )', "#,0", None),
        ("Forecast Sales Low", 'CALCULATE ( SUM ( Forecast[Lower] ), Forecast[Metric] = "Sales" )', "#,0", None),
        ("Forecast Sales High", 'CALCULATE ( SUM ( Forecast[Upper] ), Forecast[Metric] = "Sales" )', "#,0", None),
        ("Forecast Profit", 'CALCULATE ( SUM ( Forecast[Forecast] ), Forecast[Metric] = "Profit" )', "#,0", None),
    ]


class Model:
    """The data model: tables, measures and the files that describe them."""

    def __init__(self, sales_frame, scored, forecast_rows):
        self.have = set(map(str, sales_frame.columns))
        self.scored = scored
        self.forecast_rows = forecast_rows
        self.sales_columns = sales_columns(sales_frame)
        self.tables = {}   # table -> {"columns": [...], "measures": [...]}
        sales_measure_list = sales_measures(self.have, scored)
        extra = discount_steps() if "Discount" in self.have else ""
        self.tables["Sales"] = {"columns": self.sales_columns, "measures": sales_measure_list,
                                "query": excel_query("Sales", self.sales_columns, extra)}
        self.tables["Date"] = {"columns": DATE_COLUMNS, "measures": [], "query": date_query(), "category": "Time"}
        self.tables["Forecast"] = {"columns": FORECAST_COLUMNS, "measures": forecast_measures(),
                                   "query": excel_query("Forecast", FORECAST_COLUMNS)}
        self.tables["Monthly"] = {"columns": MONTHLY_COLUMNS, "measures": [], "query": excel_query("Monthly", MONTHLY_COLUMNS)}
        self.tables["Quality"] = {"columns": QUALITY_COLUMNS, "measures": [], "query": excel_query("Quality", QUALITY_COLUMNS)}
        if scored:
            self.tables["ModelMetrics"] = {"columns": MODEL_COLUMNS, "measures": [],
                                           "query": excel_query("ModelMetrics", MODEL_COLUMNS)}
        self.tables["Status"] = {"columns": STATUS_COLUMNS, "measures": [], "query": excel_query("Status", STATUS_COLUMNS)}

    def measure_names(self):
        return {t: {m[0] for m in spec["measures"]} for t, spec in self.tables.items()}

    def column_names(self):
        return {t: {c.name for c in spec["columns"]} for t, spec in self.tables.items()}

    def files(self, data_file):
        files = {
            "database.tmdl": "database\n\tcompatibilityLevel: 1567\n",
            "model.tmdl": self.model_tmdl(),
            "expressions.tmdl": (
                f"expression DataFile = {text_value(data_file)} meta "
                f'[IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]\n\tlineageTag: {guid("expression.DataFile")}\n'),
            "relationships.tmdl": (
                f"relationship {guid('relationship.sales-date')}\n\tfromColumn: Sales.{quote('Order Date')}\n\ttoColumn: Date.Date\n"),
        }
        for name, spec in self.tables.items():
            files[f"tables/{name}.tmdl"] = table_tmdl(name, spec["columns"], spec["query"], spec["measures"], spec.get("category"))
        return files

    def model_tmdl(self):
        order = json.dumps(["DataFile"] + list(self.tables))
        lines = ["model Model", "\tculture: en-US", "\tdefaultPowerBIDataSourceVersion: powerBI_V3", "\tsourceQueryCulture: en-US", ""]
        lines += [f"annotation PBI_QueryOrder = {order}", ""]
        lines += [f"ref table {quote(name)}" for name in self.tables]
        return "\n".join(lines) + "\n"


# =============================================================================== report (PBIR)
def field(kind, table, name):
    return {kind: {"Expression": {"SourceRef": {"Entity": table}}, "Property": name}}


def projection(kind, table, name):
    return {"field": field(kind, table, name), "queryRef": f"{table}.{name}", "nativeQueryRef": name}


def literal(value):
    return {"expr": {"Literal": {"Value": value}}}


class Page:
    def __init__(self, key, title):
        self.key, self.title, self.visuals = key, title, []

    def add(self, kind, x, y, w, h, roles, title=None, sort_measure=None, dropdown=False):
        """roles: {'Values': [('Measure', 'Sales', 'Total Sales'), ...]}"""
        z = len(self.visuals)
        name = f"v{z:02d}_{kind}"
        query = {"queryState": {role: {"projections": [projection(*item) for item in items]} for role, items in roles.items()}}
        if sort_measure:
            query["sortDefinition"] = {"sort": [{"field": field("Measure", *sort_measure), "direction": "Descending"}], "isDefaultSort": True}
        visual = {"visualType": kind, "query": query, "drillFilterOtherVisuals": True}
        if title:
            visual["visualContainerObjects"] = {"title": [{"properties": {
                "show": literal("true"), "text": literal("'" + title.replace("'", "''") + "'")}}]}
        if dropdown:
            visual["objects"] = {"data": [{"properties": {"mode": literal("'Dropdown'")}}]}
        self.visuals.append({
            "$schema": SCHEMAS["visual"], "name": name,
            "position": {"x": x, "y": y, "z": z, "height": h, "width": w, "tabOrder": z},
            "visual": visual})


def split_width(total, weights, gap=12):
    """Divide a row into columns with the given weights."""
    usable = total - gap * (len(weights) - 1)
    widths = [int(usable * w / sum(weights)) for w in weights]
    xs, x = [], 20
    for width in widths:
        xs.append(x)
        x += width + gap
    return list(zip(xs, widths))


def build_pages(model, texts):
    have, scored = model.have, model.scored
    column = lambda table, name: ("Column", table, name)
    measure = lambda name, table="Sales": ("Measure", table, name)
    pages = []

    # ---- page 1: overview
    page = Page("p_overview", texts["overview"])
    slicers = [("Date", "Year")] + [("Sales", c) for c in ("Region", "Category", "Segment") if c in have]
    for i, (table, name) in enumerate(slicers):
        page.add("slicer", 20 + i * 232, 10, 220, 56, {"Values": [column(table, name)]}, dropdown=True)
    cards = ["Total Sales", "Total Profit", "Profit Margin %", "Loss Rate %"] + (["Avg Discount"] if "Discount" in have else []) + ["Sales YoY %"]
    for (x, w), name in zip(split_width(1240, [1] * len(cards)), cards):
        page.add("card", x, 76, w, 92, {"Values": [measure(name)]})
    row_c = [("lineChart", 6, texts["monthly"], {"Category": [column("Date", "Year-Month")], "Y": [measure("Total Sales"), measure("Total Profit")]})]
    if "Category" in have:
        row_c.append(("clusteredColumnChart", 3, texts["by_category"], {"Category": [column("Sales", "Category")], "Y": [measure("Total Profit")]}))
    if "Region" in have:
        row_c.append(("clusteredColumnChart", 3, texts["by_region"], {"Category": [column("Sales", "Region")], "Y": [measure("Total Profit")]}))
    for (x, w), (kind, _, title, roles) in zip(split_width(1240, [r[1] for r in row_c]), row_c):
        page.add(kind, x, 180, w, 250, roles, title=title)
    row_d = []
    if "Discount" in have:
        row_d.append(("discount", 4))
    stack = [name for name in ("Best Category", "Worst Category", "Best Region", "Worst Region") if name in model.measure_names()["Sales"]]
    if stack:
        row_d.append(("stack", 2))
    if "Product" in have:
        row_d.append(("products", 6))
    for (x, w), (what, _) in zip(split_width(1240, [r[1] for r in row_d]), row_d):
        if what == "discount":
            page.add("clusteredColumnChart", x, 442, w, 268, {"Category": [column("Sales", "Discount Band")], "Y": [measure("Avg Profit per Order")]}, title=texts["by_discount"])
        elif what == "stack":
            height = int((268 - 8 * (len(stack) - 1)) / len(stack))
            for i, name in enumerate(stack):
                page.add("card", x, 442 + i * (height + 8), w, height, {"Values": [measure(name)]})
        else:
            page.add("tableEx", x, 442, w, 268, {"Values": [column("Sales", "Product"), measure("Total Sales"), measure("Total Profit")]},
                     title=texts["products"], sort_measure=("Sales", "Total Profit"))
    pages.append(page)

    # ---- page 2: forecast
    if model.forecast_rows:
        page = Page("p_forecast", texts["forecast"])
        page.add("lineChart", 20, 20, 1240, 260, {"Category": [column("Forecast", "Month")],
                 "Y": [measure("Forecast Sales", "Forecast"), measure("Forecast Sales Low", "Forecast"), measure("Forecast Sales High", "Forecast")]},
                 title=texts["fc_sales"])
        page.add("lineChart", 20, 292, 1240, 200, {"Category": [column("Forecast", "Month")], "Y": [measure("Forecast Profit", "Forecast")]},
                 title=texts["fc_profit"])
        page.add("tableEx", 20, 504, 1240, 206, {"Values": [column("Forecast", name) for name in
                 ("Metric", "Month", "Forecast", "Lower", "Upper", "Method", "Reliability", "Backtest WAPE")]}, title=texts["fc_table"])
        pages.append(page)

    # ---- page 3: loss risk (only when the model was trained)
    if scored:
        page = Page("p_risk", texts["risk"])
        cards = ["High Risk Orders", "High Risk Sales Amount", "Predicted Loss Orders", "Avg Profit Probability", "Model Accuracy Unseen"]
        for (x, w), name in zip(split_width(1240, [1] * len(cards)), cards):
            page.add("card", x, 20, w, 100, {"Values": [measure(name)]})
        row = [("levels", 3)] + ([("category", 3)] if "Category" in have else []) + ([("matrix", 4)] if "Region" in have else [])
        for (x, w), (what, _) in zip(split_width(1240, [r[1] for r in row]), row):
            if what == "levels":
                page.add("clusteredColumnChart", x, 136, w, 290, {"Category": [column("Sales", "Risk Level")], "Y": [measure("Orders")]}, title=texts["risk_levels"])
            elif what == "category":
                page.add("clusteredColumnChart", x, 136, w, 290, {"Category": [column("Sales", "Category")], "Y": [measure("Avg Profit Probability")]}, title=texts["risk_category"])
            else:
                page.add("pivotTable", x, 136, w, 290, {"Rows": [column("Sales", "Region")], "Columns": [column("Sales", "Risk Level")],
                         "Values": [measure("Orders")]}, title=texts["risk_matrix"])
        if "Product" in have:
            page.add("tableEx", 20, 440, 1240, 270, {"Values": [column("Sales", "Product"), measure("High Risk Orders"), measure("Orders"), measure("Total Profit")]},
                     title=texts["risk_products"], sort_measure=("Sales", "High Risk Orders"))
        pages.append(page)

    # ---- page 4: data quality
    page = Page("p_quality", texts["quality"])
    page.add("tableEx", 20, 20, 620, 690, {"Values": [column("Quality", "Metric"), column("Quality", "Value")]}, title=texts["quality_table"])
    if scored:
        page.add("tableEx", 652, 20, 608, 400, {"Values": [column("ModelMetrics", "Metric"), column("ModelMetrics", "Value"), column("ModelMetrics", "Note")]},
                 title=texts["model_table"])
    page.add("tableEx", 652, 432 if scored else 20, 608, 278 if scored else 200, {"Values": [column("Status", name) for name in ("Last Refresh", "Status", "Source", "Rows After Cleaning", "Message")]},
             title=texts["status_table"])
    pages.append(page)
    return pages


def report_files(pages):
    files = {
        "version.json": {"$schema": SCHEMAS["version"], "version": "2.0.0"},
        "report.json": {
            "$schema": SCHEMAS["report"],
            "themeCollection": {"baseTheme": {"name": "CY24SU06", "reportVersionAtImport": "5.55", "type": "SharedResources"}},
            "resourcePackages": [{"name": "SharedResources", "type": "SharedResources",
                                  "items": [{"name": "CY24SU06", "path": "BaseThemes/CY24SU06.json", "type": "BaseTheme"}]}],
        },
        "pages/pages.json": {"$schema": SCHEMAS["pages"], "pageOrder": [p.key for p in pages], "activePageName": pages[0].key},
    }
    for page in pages:
        files[f"pages/{page.key}/page.json"] = {"$schema": SCHEMAS["page"], "name": page.key, "displayName": page.title,
                                                "displayOption": "FitToPage", "height": 720, "width": 1280}
        for visual in page.visuals:
            files[f"pages/{page.key}/visuals/{visual['name']}/visual.json"] = visual
    return files


# =============================================================================== the whole project
README_DASHBOARD = {
    "en": """# Sales Dashboard (Power BI project)

1. Unzip this folder, for example to `C:\\SalesIntelligence\\`, and put `power_bi_data.xlsx` (from the app) in the same place.
2. Open `Sales Dashboard.pbip` with **Power BI Desktop** (a recent version).
3. If the data does not load: **Home > Transform data > Edit parameters**, set **DataFile** to the full path of `power_bi_data.xlsx`, then **Close & Apply**.
4. **Home > Refresh**. Check that `[Total Sales]` (Overview page) equals "Total sales after cleaning" on the *Data quality* page.
5. Save it as a normal `.pbix` (File > Save as) and publish it if you want.

New data: replace `power_bi_data.xlsx` (same path) and press **Refresh**.

Note: this project was generated by a program. It follows Microsoft's published formats and was checked against Microsoft's JSON schemas,
but it could not be opened in Power BI Desktop while building the app. If Power BI shows an error, send its text and follow
`STEP_BY_STEP.md` (the manual way) in the meantime.
""",
    "ar": """# لوحة المبيعات (مشروع Power BI)

1. فك الضغط عن هذا المجلد، مثلاً في `C:\\SalesIntelligence\\`، وضع فيه الملف `power_bi_data.xlsx` (من التطبيق).
2. افتح الملف `Sales Dashboard.pbip` ببرنامج **Power BI Desktop** (إصدار حديث).
3. لو لم تُحمَّل البيانات: **Home > Transform data > Edit parameters** وضع في **DataFile** المسار الكامل للملف `power_bi_data.xlsx`، ثم **Close & Apply**.
4. **Home > Refresh**. تأكد أن `[Total Sales]` في صفحة «نظرة عامة» يساوي «Total sales after cleaning» في صفحة «جودة البيانات».
5. احفظه كملف `.pbix` عادي (File > Save as) وانشره لو أردت.

بيانات جديدة: استبدل `power_bi_data.xlsx` (بنفس المسار) واضغط **Refresh**.

ملاحظة: المشروع مولَّد ببرنامج. يتبع صيغ Microsoft المنشورة وتم فحصه مقابل JSON schemas الخاصة بها، لكن لم يمكن فتحه داخل Power BI Desktop
أثناء بناء التطبيق. لو ظهر خطأ أرسل نصه، واستخدم `STEP_BY_STEP.md` (الطريقة اليدوية) في الأثناء.
""",
}


def build_project(sales_frame, scored, forecast_rows, lang="en", data_file=DEFAULT_DATA_FILE, project=PROJECT_NAME):
    """Returns {path inside the project folder: text}. Write them to disk, or zip them."""
    model = Model(sales_frame, scored, forecast_rows)
    pages = build_pages(model, DASH_TEXT[lang])
    dump = lambda data: json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    report_dir, model_dir = f"{project}.Report", f"{project}.SemanticModel"

    files = {
        f"{project}.pbip": dump({"$schema": SCHEMAS["pbip"], "version": "1.0",
                                 "artifacts": [{"report": {"path": report_dir}}], "settings": {"enableAutoRecovery": True}}),
        f"{report_dir}/definition.pbir": dump({"$schema": SCHEMAS["pbir"], "version": "4.0",
                                               "datasetReference": {"byPath": {"path": f"../{model_dir}"}}}),
        f"{report_dir}/.platform": dump({"$schema": SCHEMAS["platform"], "metadata": {"type": "Report", "displayName": project},
                                         "config": {"version": "2.0", "logicalId": guid("report." + project)}}),
        f"{model_dir}/definition.pbism": dump({"$schema": SCHEMAS["pbism"], "version": "4.0"}),
        f"{model_dir}/.platform": dump({"$schema": SCHEMAS["platform"], "metadata": {"type": "SemanticModel", "displayName": project},
                                        "config": {"version": "2.0", "logicalId": guid("model." + project)}}),
        "README_DASHBOARD.md": README_DASHBOARD[lang],
    }
    for path, data in report_files(pages).items():
        files[f"{report_dir}/definition/{path}"] = dump(data)
    for path, text in model.files(data_file).items():
        files[f"{model_dir}/definition/{path}"] = text
    return files
