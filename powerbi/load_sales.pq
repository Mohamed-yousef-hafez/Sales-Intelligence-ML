// Power Query (M) - loads sales_scored.csv (or cleaned_sales.csv) from the exports folder.
// Power BI Desktop: Home > Get data > Blank query > Advanced editor > paste this > change Folder and FileName.
// Columns that do not exist in your file are skipped automatically.
let
    Folder   = "C:\SalesIntelligence\exports\",
    FileName = "sales_scored.csv",
    Source   = Csv.Document(File.Contents(Folder & FileName), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Headers  = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    Wanted   = {
        {"Order Date", type date}, {"Ship Date", type date},
        {"Sales", type number}, {"Profit", type number}, {"Cost", type number},
        {"Discount", type number}, {"Quantity", type number}, {"Ship Days", type number},
        {"Order Month", Int64.Type}, {"Order Year", Int64.Type}, {"Profitable", Int64.Type},
        {"Profit Probability", type number}, {"Predicted Profitable", Int64.Type}, {"In Training Set", Int64.Type}
    },
    Existing = List.Select(Wanted, each List.Contains(Table.ColumnNames(Headers), _{0})),
    Typed    = Table.TransformColumnTypes(Headers, Existing, "en-US")
in
    Typed
