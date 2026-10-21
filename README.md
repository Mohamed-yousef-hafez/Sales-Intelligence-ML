# Sales Intelligence — End-to-End Machine Learning

A simple company-oriented Sales ML project covering:

- Data validation and cleaning
- Exploratory/business analytics
- Profitability classification
- Model evaluation
- Streamlit deployment UI
- Lightweight local RAG
- Simple agent/tool routing
- Basic upload security
- Application monitoring/logging

## Arabic and English support

The company can upload a sales file in **Arabic or English** (CSV or XLSX) and the application works the same way.

- **Interface:** switch between العربية and English from the sidebar (right-to-left layout for Arabic).
- **Column names:** many Arabic and English names are recognised, for example `المبيعات`, `إجمالي المبيعات`,
  `الأرباح`, `نسبة الخصم %`, `التصنيف`, `المحافظة`, `Total Sales`, `Net Profit`, `Disc`, `Units`.
  See `COLUMN_ALIASES` in `src/security.py` to add your company's names.
  **Required:** Order Date, Sales, and Profit (or Cost: Profit = Sales - Cost).
  **Optional** (more analysis when present, skipped when missing): Discount, Quantity, Category, Sub-Category,
  Product, Customer, Region, Segment, Ship Mode, Ship Date.
- **Values:** Arabic/Persian digits (`١٢٣`), Arabic separators (`٫` `٬`), currency text (`1,200 ج.م`, `$5`, `EGP 10`),
  percentages (`20%`), accounting negatives (`(500)`), diacritics and hidden characters are cleaned automatically.
- **Dates:** `25/03/2024`, `2024-03-25`, `25 مارس 2024`, `15 كانون الأول 2023`. The application detects whether the file is
  day/month/year or month/day/year and shows the result in the Data Quality Report.
- **Files:** Excel (`.xlsx` `.xlsm` `.xls`) and CSV/TSV/TXT, max 50 MB and 1,000,000 rows. Excel files with several sheets:
  the sheet that looks most like sales data is used. CSV: UTF-8 or Arabic Windows encoding (`cp1256`);
  the separator (`,` `;` tab `|`) is detected automatically.
- **Number formats:** `1,234.50`, `1.234,50`, decimal comma `12,5` (common in Arabic Excel with `;` files), `1,200`.
- **Assistant:** ask in Arabic or English. The answer comes in the language of the question, and names from your data
  (for example `أثاث` or `Furniture`) are recognised: "كم ربح الأثاث؟" / "What is the profit of Furniture?".
- **Demo data:** `data/sample_superstore.csv` (English) and `data/sample_arabic_sales.csv` (Arabic).
  Both give almost the same results (same totals, about 94% accuracy).

## 1. Project Idea

Sales Intelligence combines business analytics, ML profitability prediction, a local RAG assistant and monitoring.
The target is `Profitable = 1` when Profit > 0, otherwise `0`.

## 2. Data cleaning and preprocessing (`src/security.py`, `src/data.py`)

The application cleans the file automatically and reports every step in the **Data Quality Report**:

1. Validates the upload (CSV/XLSX, max 10 MB) and finds the real header row, even below a report title.
2. Maps Arabic/English column names to standard names.
3. Cleans text: Arabic/Persian digits, diacritics, extra spaces, hidden characters.
4. Converts placeholders (`N/A`, `null`, `-`, `?`, `غير متوفر`, `لا يوجد` ...) to real missing values.
5. Removes total / summary rows (`Total`, `Grand Total`, `الإجمالي`, `المجموع`).
6. Unifies spelling variants of categories, regions, segments (`furniture ` = `FURNITURE` = `Furniture`, `أثاث` = `اثاث`).
7. Removes exact duplicate rows.
8. Converts numbers (`$1,200`, `1200 ج.م`, `20%`, `(500)`, `١٬٢٣٤٫٥`), discounts (`0.2`, `20`, `20%`, even mixed)
   and dates (ISO, `25/03/2024`, `25 مارس 2024`, Excel date numbers such as `45292`).
9. Removes rows with a missing required value or an impossible value:
   Sales <= 0, Quantity <= 0, Discount outside 0-100%, order dates before 1990 or after 2100.
10. Fills missing category names with `Unknown` / `غير محدد`.
11. Creates `Ship Days` (invalid negative values become missing), `Order Month`, `Order Year` and the target `Profitable`.
12. Counts extreme Sales/Profit values (10 x IQR). They are **kept** and only reported for your review.

Inside the model pipeline, missing numbers are imputed (median) and categories are one-hot encoded.

Tested with a real-size file (10,000 rows) damaged in many ways at once (about 25% of rows affected): the cleaned result
matched the original (same row count, same totals, same category counts). See `tests/test_cleaning.py`.

Note: returns (negative sales/quantity) are removed by rule 9. The report shows how many rows were removed, so compare with your file.

## 3. ML model (`src/model.py`)

- RandomForest inside a scikit-learn Pipeline (imputation + one-hot encoding), class balancing, fixed random seed.
- Extra feature `Unit Price = Sales / Quantity` (calculated automatically).
- Chronological 80/20 split by order date (train on the past, test on the most recent sales);
  falls back to a stratified random split if the date split does not contain both classes.
- Metrics: Accuracy, Precision, Recall, F1, ROC-AUC, confusion matrix, a **baseline** accuracy for comparison
  and **feature importance** (what drives profitability).
- Take the metrics from the actual run on the final dataset. Do not copy demo numbers blindly.

## 4. Assistant (`src/agent.py`, `src/rag.py`)

A simple rule-based router understands Arabic and English:

- Discount questions → average profit by discount level
- A name from your data (category, sub-category, region, segment, ship mode) → summary of that item
- Category / sub-category / region / segment questions → ranking by profit or sales (respects highest vs lowest)
- Profit / sales questions → business summary
- Anything else → local RAG (TF-IDF over facts built from your data in both languages)

No external LLM is used and no data leaves the application.

## 5. Application features for the company

- Data Quality Report (opened by default) with every cleaning step, and download of the **cleaned data** and the **report** (CSV).
- **Excel template** to download (English or Arabic) with example rows and a notes sheet.
- Dashboard with **filters** (date range, category, region, segment) and charts for every column that exists,
  including the best/worst 10 products and customers.
- ML model with clear messages when the data is not enough (needs 30+ rows, at least 5 profitable and 5 loss-making).
- Optional **password**: set the environment variable `APP_PASSWORD`.
- Exported CSV files are protected against Excel formula injection.

## 5a. Forecast, reliability check and Power BI (`src/forecast.py`, `src/powerbi.py`, `src/pipeline.py`, `powerbi/`)

- **Forecast tab:** next 1-6 months of Sales or Profit (optionally for one category/region). Five simple methods
  (repeat last month, 3-month average, same month last year, recent level x seasonal strength, trend + seasonality) are
  **tested on the last months of the company's own data**; the most accurate is used and compared with "repeat last month".
  The result shows the typical past error (WAPE), the baseline error, an approximate 80% range and a verdict
  (reliable / moderate / weak). Needs 9 complete months. An unfinished last month is detected and not used for learning.
  Honest limits: the future is assumed to behave like the past, and the past error is slightly optimistic because the
  method was chosen on the same months. The assistant also answers "next month forecast" questions.
- **Reliability check (ML tab):** trains on the past and tests on the following period five times in a row
  (time-based cross-validation) and compares every period with the best constant guess. Verdict: strong / moderate / weak.
  **Accuracy on one company's data is not guaranteed on another's**: always run this check on the company's own file.
- **Predictions per sale:** download the data with `Profit Probability`, `Predicted Profitable`, `Risk Level` and `In Training Set`
  (rows used for training have optimistic probabilities; judge the model on rows with 0).
- **Power BI tab:** **`power_bi_data.xlsx` - ONE Excel file with every table** (Excel Tables named Sales, Forecast, Monthly,
  Quality, ModelMetrics, Status, so Power BI lists them by the names used in the DAX; up to 100,000 rows, above that only CSV),
  plus a ZIP with the same tables as CSV, `STEP_BY_STEP.md` (click-by-click setup, three report pages, checklist, troubleshooting),
  and the cleaned data, scored data, forecast, monthly summary, quality report, model metrics,
  `measures.dax`, `load_sales.pq` and `README_POWERBI.md` (setup, KPIs, Date table, Sales LY).
  The DAX and Power Query code could not be run inside Power BI in the build environment; a test checks that every
  column they use exists in the exported files.
- **Automatic refresh:** `python refresh_exports.py` reads the newest file (or all files with `--combine`) from `inbox/`,
  cleans, trains, forecasts and writes the Power BI files to `exports/` (atomic writes; if a run fails the old files stay
  and `refresh_status.csv` says why). `--watch 300` keeps running; `run_refresh_windows.bat` is for Windows Task Scheduler;
  `docker compose up` also starts a `refresh` service. In Power BI Service the dataset refresh must be scheduled
  (Pro: up to 8 per day; files on a local computer/server need an on-premises data gateway; Power BI Desktop does not refresh by itself).

## 5c. Model export, ready dashboard, cleaning status and free link

- **Model as a file:** after training, the ML tab offers the model as `profit_model.joblib` and as a ZIP package
  (`model_card.json` with the input columns and metrics, `use_model.py` that scores a CSV/Excel file with only pandas+scikit-learn+joblib,
  and a guide). A test runs the script in an isolated process and checks it gives the same probabilities as the app.
  Warning: .joblib files can run code when loaded; use the same scikit-learn version. `refresh_exports.py` writes these files too.
- **Ready Power BI dashboard:** `power_bi_dashboard.zip` is a Power BI Project (`Sales Dashboard.pbip`: data model in TMDL with
  tables, a Date table, relationship and the DAX measures; report in PBIR with 4 pages: Overview, Forecast, Loss risk, Data quality).
  It reads `power_bi_data.xlsx` (path parameter `DataFile`) and adapts to the columns that exist. The JSON files are checked against
  Microsoft's published schemas (`python tools/validate_pbip.py <folder>`) and tests check that every field a visual uses exists in the model.
  It could **not** be opened in Power BI Desktop while building the app: if it shows an error, use `powerbi/STEP_BY_STEP.md` and send me the error.
  Only for data up to 100,000 rows (it needs the Excel file).
- **Cleaning status:** every file goes through the same checks. A banner says "already clean" (0 corrections) or "N corrections made".
- **Free public link:** see `DEPLOY_FREE.md` (Streamlit Community Cloud, `APP_DEMO_ONLY` mode, tunnel, own server).
  Settings (`APP_PASSWORD`, `APP_DEMO_ONLY`) can come from environment variables or Streamlit Secrets.
- Install for tests: `pip install -r requirements-dev.txt` (`requirements.txt` is the runtime only).

## 5b. Security and monitoring

Upload validation (extension, size, rows), no uploaded file is executed, logs in `logs/app.log`
(processing time, errors, predictions, assistant tools).
For real company data deploy inside the company's private infrastructure and use HTTPS if it is opened outside the network.

## 6. Run

- Windows: double-click `run_windows.bat`. Linux/Mac: `./run_linux_mac.sh`.
- Manual: `python -m venv .venv`, activate it, `pip install -r requirements.txt`, `streamlit run app.py`.
- Docker: `docker compose up --build` (set `APP_PASSWORD` in `docker-compose.yml`). Open http://localhost:8501.
- Tests: `pytest`.
- Staff guide (Arabic + English): `USER_GUIDE.md`.

Streamlit usage statistics are switched off (`.streamlit/config.toml`).

Verified: the Streamlit server starts and answers its health check; all tests pass.
The Docker files and the `.bat`/`.sh` scripts were written but not run in the build environment, so test them once on your machine.

## 7. Known limitations

- Dates where every value is ambiguous (for example all days are 12 or less) cannot be classified;
  the application then reads them month-first and the Data Quality Report says "unknown".
- Only one sheet is analysed per Excel file (the one that looks most like sales data).
- Cleaning rules are fixed (see section 2). If your business needs to keep returns (negative sales), change the rule in `clean_data` (`src/data.py`).
- Duplicate detection is exact-row only. If the file has no ID column, two truly identical sales lines are treated as duplicates.
- Question understanding is rule-based (keywords), not a language model. Very free-form questions fall back to RAG retrieval.
- Arabic text is displayed with right-to-left styling; please check the layout in your browser.
