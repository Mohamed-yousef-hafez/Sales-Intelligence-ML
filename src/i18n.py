"""All user-facing texts in Arabic and English.

Use:  t("ar", "m_sales")   or   t("en", "ans_summary", sales="1,000.00", ...)
"""

# Arabic names of the standard columns (used in the Arabic interface and in error messages).
COLUMN_LABELS_AR = {
    "Sales": "المبيعات",
    "Profit": "الربح",
    "Discount": "الخصم",
    "Quantity": "الكمية",
    "Category": "الفئة",
    "Sub-Category": "الفئة الفرعية",
    "Order Date": "تاريخ الطلب",
    "Ship Date": "تاريخ الشحن",
    "Region": "المنطقة",
    "Segment": "الشريحة",
    "Ship Mode": "طريقة الشحن",
    "Ship Days": "أيام الشحن",
    "Order Month": "شهر الطلب",
    "Order Year": "سنة الطلب",
    "Unit Price": "سعر الوحدة",
    "Profitable": "مربح",
    "Cost": "التكلفة",
    "Product": "المنتج",
    "Customer": "العميل",
}

# Words used inside agent answers: dimension names and metric names.
DIMENSIONS = {
    "Category": {"en": "category", "ar": "فئة"},
    "Sub-Category": {"en": "sub-category", "ar": "فئة فرعية"},
    "Region": {"en": "region", "ar": "منطقة"},
    "Segment": {"en": "segment", "ar": "شريحة"},
    "Ship Mode": {"en": "ship mode", "ar": "طريقة شحن"},
    "Product": {"en": "product", "ar": "منتج"},
    "Customer": {"en": "customer", "ar": "عميل"},
}
METRICS = {
    "Profit": {"en": "profit", "ar": "الربح", "ar_adv": "ربحاً"},
    "Sales": {"en": "sales", "ar": "المبيعات", "ar_adv": "مبيعاً"},
}

TEXT = {
    "en": {
        # ---- general ----
        "app_title": "📊 Sales Intelligence — ML",
        "app_caption": "Sales analytics + profitability prediction + local RAG + agent routing + monitoring",
        "language": "Language / اللغة",
        "demo_label": "Demo dataset (used when no file is uploaded)",
        "demo_en": "English demo (Superstore)",
        "demo_ar": "Arabic demo (مبيعات عربية)",
        "uploader": "Upload your sales data (Excel or CSV) — Arabic or English",
        "uploader_help": "Excel (.xlsx .xlsm .xls) or CSV/TSV. Column names and values can be Arabic or English. Max 50 MB.",
        "download_template": "⬇️ Download the Excel template",
        "download_clean": "⬇️ Download the cleaned data (CSV)",
        "download_report": "⬇️ Download the quality report (CSV)",
        "login_title": "🔒 Sign in",
        "login_prompt": "Password",
        "login_button": "Sign in",
        "login_wrong": "Wrong password.",
        "dq_profit_from_cost": "Profit calculated as Sales − Cost",
        "dq_missing_optional": "Optional columns not found (related features are skipped)",
        "filters": "🔎 Filters (dashboard only)",
        "filter_dates": "Order date range",
        "filter_empty": "No rows match the selected filters.",
        "chart_by": "Profit by {dim}",
        "top10": "Top 10 {dim} by profit",
        "bottom10": "Bottom 10 {dim} by profit",
        "ans_no_discount": "The uploaded file has no discount column, so discount analysis is not available.",
        "upload_error": "Could not read the uploaded file: {error}",
        "process_error": "Could not process this dataset: {error}",
        "summary_error": "Could not calculate business metrics: {error}",
        "no_rows": "No valid rows remain after cleaning. Check the uploaded file and its columns.",
        "loaded": "Loaded {rows} rows from {source}. Processing time: {seconds}s",
        "demo_name": "Built-in demo dataset",
        # ---- quality report ----
        "quality_title": "🔎 Data Quality Report",
        "dq_changes": "Corrections made in total (0 = the file was already clean)",
        "clean_ok": "✅ The file was already clean: no corrections were needed. (Every file goes through the same checks; this one passed them all.)",
        "clean_fixed": "🧹 The file needed cleaning: {n} corrections were made. See the report below.",
        "demo_only_note": "This public demo uses the built-in demo data only. File upload is switched off.",
        "dq_before": "Rows before cleaning",
        "dq_after": "Rows after cleaning",
        "dq_removed": "Rows removed",
        "dq_columns": "Columns in source file",
        "dq_placeholders": "Placeholders (N/A, null, -, ...) converted to missing",
        "dq_summary_rows": "Total / summary rows removed",
        "dq_variants": "Spelling variants unified (e.g. furniture / Furniture)",
        "dq_duplicates": "Duplicate rows removed",
        "dq_invalid": "Rows missing a required value (removed)",
        "dq_impossible": "Rows with impossible values (removed)",
        "dq_filled": "Missing category names filled with 'Unknown'",
        "dq_extreme": "Extreme Sales/Profit values kept for your review",
        "cleaning_steps_title": "What the application does automatically",
        "cleaning_steps": (
            "1. Finds the real header row (even below a report title) and maps Arabic/English column names.\n"
            "2. Cleans text: Arabic digits, diacritics, extra spaces, hidden characters.\n"
            "3. Converts placeholders (`N/A`, `null`, `-`, `غير متوفر` ...) to real missing values.\n"
            "4. Removes total / summary rows (`Total`, `الإجمالي`).\n"
            "5. Unifies spelling variants of categories, regions and segments.\n"
            "6. Removes exact duplicate rows.\n"
            "7. Converts numbers (currency, `%`, Arabic separators, `(500)`), discounts and dates "
            "(including Arabic month names and Excel date numbers).\n"
            "8. Removes rows with a missing required value or an impossible value "
            "(Sales ≤ 0, Quantity ≤ 0, Discount outside 0–100%, dates before 1990 or after 2100).\n"
            "9. Fills missing category names with `Unknown`; the model also imputes missing numbers and "
            "one-hot encodes categories automatically.\n"
            "10. Reports everything below, so you can compare with the original file."
        ),
        "dq_missing_before": "Missing cells before cleaning",
        "dq_missing_after": "Missing cells after cleaning",
        "dq_sales": "Total sales after cleaning",
        "dq_profit": "Total profit after cleaning",
        "dq_discount": "Discount converted from percent to fraction",
        "dq_date_order": "Detected date order",
        "dq_date_min": "Earliest order date",
        "dq_date_max": "Latest order date",
        "dq_metric": "Metric",
        "dq_value": "Value",
        "date_order_day-first": "day/month/year",
        "date_order_month-first": "month/day/year",
        "date_order_unknown": "unknown (all dates are ambiguous or ISO)",
        "yes": "Yes",
        "no": "No",
        "dq_note": (
            "A successful upload confirms that the file was read and processed. "
            "It does not by itself prove that the source values are business-correct. "
            "Compare totals with the original file."
        ),
        # ---- tabs ----
        "tab_dashboard": "📈 Business Dashboard",
        "tab_model": "🤖 ML Model",
        "tab_assistant": "🧠 AI Assistant",
        "tab_security": "🔐 Security & Monitoring",
        # ---- dashboard ----
        "overview": "Business Overview",
        "m_sales": "Total Sales",
        "m_profit": "Total Profit",
        "m_margin": "Profit Margin",
        "m_loss": "Loss Rate",
        "chart_discount": "Average profit per order by discount level",
        "chart_monthly": "Monthly Sales and Profit",
        "preview": "Data Preview",
        # ---- model ----
        "predict_title": "Profitability Prediction",
        "train_info": "The ML model is trained only when you click the button. This keeps the dashboard fast.",
        "train_button": "🚀 Train ML Model",
        "training": "Training profitability model...",
        "train_error": "Could not train the model: {error}",
        "accuracy": "Accuracy",
        "precision": "Precision",
        "recall": "Recall",
        "f1": "F1",
        "roc_auc": "ROC-AUC",
        "baseline_note": (
            "Baseline: always predicting the most common class gives {baseline} accuracy. "
            "The model was tested on {test} {split} rows after training on {train}."
        ),
        "split_chronological": "most recent",
        "split_stratified_random_fallback": "randomly selected",
        "target_note": "Target: `Profitable = 1` when Profit > 0, otherwise `0`.",
        "confusion": "Confusion Matrix",
        "actual_loss": "Actual Loss",
        "actual_profit": "Actual Profit",
        "pred_loss": "Predicted Loss",
        "pred_profit": "Predicted Profit",
        "importance_title": "What drives profitability? (feature importance)",
        "try_title": "Try a New Transaction",
        "predict_button": "Predict Profitability",
        "pred_yes": "PROFITABLE",
        "pred_no": "LOSS / NOT PROFITABLE",
        "pred_result": "Prediction: **{label}** — probability of profitability: **{probability}**",
        "pred_failed": "Prediction failed: {error}",
        "feature_missing": "Feature '{feature}' is missing from the cleaned data.",
        # ---- assistant ----
        "assistant_title": "Sales AI Assistant",
        "assistant_desc": (
            "Local RAG + agent routing. Ask in Arabic or English — the answer comes in the language of your question. "
            "No external LLM is used and company data stays inside the application."
        ),
        "examples_title": "Example questions",
        "examples": (
            "- Which region has the highest profit?\n"
            "- Which category has the lowest sales?\n"
            "- What is the profit of Furniture?\n"
            "- How does discount affect profit?\n"
            "- What is the total sales and margin?"
        ),
        "question_label": "Ask a sales question",
        "question_placeholder": "Example: Which region has the lowest profit?",
        "ask_button": "Ask Assistant",
        "analyzing": "Analyzing...",
        "agent_tool": "Agent tool",
        "assistant_failed": "Assistant failed: {error}",
        "assistant_init_failed": "Could not initialize the assistant: {error}",
        "tool_discount_profit": "discount analysis",
        "tool_entity_summary": "item summary",
        "tool_ranking": "ranking",
        "tool_business_summary": "business summary",
        "tool_rag_retrieval": "document retrieval (RAG)",
        # ---- security ----
        "security_title": "Security",
        "security_points": (
            "- Accepts only Excel/CSV/TSV uploads (.xlsx .xlsm .xls .csv .tsv .txt).\n"
            "- Upload size is limited to 50 MB and 1,000,000 rows (`.streamlit/config.toml` and `src/security.py`).\n"
            "- Required business columns are validated by the upload loader (Arabic or English names).\n"
            "- Optional password protection: set the environment variable `APP_PASSWORD`.\n"
            "- Exported CSV files are protected against Excel formula injection.\n"
            "- No uploaded file is executed as code.\n"
            "- No external LLM is used.\n"
            "- Uploaded company data stays inside the running application process."
        ),
        "monitoring_title": "Monitoring",
        "monitoring_points": (
            "- Data processing time is logged.\n"
            "- Upload/pipeline errors are logged.\n"
            "- Model training errors are logged.\n"
            "- Prediction events are logged.\n"
            "- Assistant questions and selected tools are logged.\n"
            "- Logs are stored in `logs/app.log` (see `src/monitoring.py`)."
        ),
        "deploy_note": (
            "Demo note: for real company data, deploy this application inside the company's "
            "private infrastructure/VPC rather than using a public demo server."
        ),
        # ---- agent answers ----
        "ans_summary": "Sales: {sales} | Profit: {profit} | Margin: {margin}% | Loss rate: {loss_rate}%.",
        "ans_total": "Total {metric}: {total}.",
        "ans_best": "Highest-{metric} {dim}: {items}.",
        "ans_worst": "Lowest-{metric} {dim}: {items}.",
        "ans_entity": (
            "{name} ({dim}): sales {sales}, profit {profit}, margin {margin}%, "
            "loss rate {loss_rate}% across {orders} orders."
        ),
        "ans_discount_none": "Average profit with no discount: {value}.",
        "ans_discount_positive": "Average profit stays positive at every discount level.",
        "ans_discount_negative": "Average profit becomes negative starting at a {discount} discount ({value} per order).",
        # ---- RAG ----
        "rag_header": "Based on the uploaded data:",
        "rag_none": (
            "I could not find a matching fact in the uploaded data. "
            "Try asking about profit, sales, category, region or discount."
        ),
        "doc_overall": "Overall sales are {sales}. Overall profit is {profit}. Profit margin is {margin} percent.",
        "doc_entity": (
            "{dim} {name}: sales {sales}, profit {profit}, margin {margin} percent, "
            "loss rate {loss_rate} percent, {orders} orders."
        ),
        "doc_discount": "Average profit for discount {discount} is {value}.",
        "doc_year": "In {year}, sales were {sales} and profit was {profit}.",
        # ---- bilingual data errors (shown as-is) ----
        # ---- forecast / reliability / power bi ----
        "tab_forecast": "🔮 Forecast",
        "tab_powerbi": "📤 Power BI",
        "fc_title": "Forecast for the coming months",
        "fc_desc": (
            "A statistical forecast from your monthly history. Several simple methods are tested on the past months "
            "of YOUR data, the most accurate one is used, and it is compared with the simplest guess "
            "(next month = last month)."
        ),
        "fc_what": "What to forecast",
        "fc_sales": "Sales",
        "fc_profit": "Profit",
        "fc_horizon": "Months ahead",
        "all_values": "All",
        "fc_failed": "The forecast could not be calculated: {error}",
        "fc_not_enough": "Not enough history: at least {needed} complete months are needed (found {found}).",
        "fc_partial_last": "The last month ({month}) looks incomplete, so it was not used for learning. The forecast starts from it.",
        "fc_partial_first": "The first month ({month}) starts late in the month, so it was not used.",
        "fc_gap": "{n} month(s) without any sales were counted as zero.",
        "fc_next": "Forecast for {month}",
        "fc_range_label": "Likely range",
        "fc_method_line": "Method chosen by testing on past months: **{method}**",
        "fc_error_line": "Typical error on past months: **{wape}** — simple baseline (repeat last month): **{base}**",
        "fc_chart": "History and forecast",
        "fc_history_label": "Actual",
        "fc_forecast_label": "Forecast",
        "fc_table": "Forecast table",
        "fc_col_month": "Month",
        "fc_col_forecast": "Forecast",
        "fc_col_low": "Low",
        "fc_col_high": "High",
        "fc_backtest": "How accurate was each method on the last {n} months? (typical error, lower is better)",
        "fc_col_method": "Method",
        "fc_col_error": "Typical error",
        "fcm_naive": "Repeat last month",
        "fcm_moving_average": "Average of the last 3 months",
        "fcm_seasonal_naive": "Same month last year",
        "fcm_seasonal_level": "Recent level x usual strength of each month",
        "fcm_trend_seasonal": "Trend + seasonality",
        "fc_verdict_good": "Reliable: the chosen method beat the baseline by {gain} points on past months (typical error {wape}).",
        "fc_verdict_ok": "Moderate: use it as a rough guide. Typical error on past months was {wape} (baseline gain: {gain} points).",
        "fc_verdict_weak": "Weak: the forecast is not clearly better than repeating last month, or its typical error is high ({wape}). Do not rely on it.",
        "fc_naive_note": "No method was better than repeating last month, so this forecast simply equals last month's value.",
        "fc_disclaimer": (
            "A forecast assumes the future behaves like the past. Promotions, price changes, new products or "
            "economic events are unknown to it. The past error is measured on the same months used to choose the method, "
            "so real errors can be a little higher."
        ),
        "rel_button": "🧪 Check reliability on my data",
        "rel_running": "Testing the model on several past periods...",
        "rel_title": "Reliability check on your data",
        "rel_desc": (
            "The model learns from the past and is tested on the following period, several times in a row "
            "(time-based cross-validation), and compared with the best constant guess."
        ),
        "rel_period": "Test period",
        "rel_train": "Training rows",
        "rel_test": "Test rows",
        "rel_baseline": "Baseline accuracy",
        "rel_summary": (
            "Average accuracy **{accuracy}** vs baseline **{baseline}** (gain **{gain}** points) — "
            "average ROC-AUC **{auc}** — spread between periods about ±{spread} points."
        ),
        "rel_verdict_strong": "Strong: the model beats the baseline clearly in every tested period. Still check it on new data before relying on it.",
        "rel_verdict_moderate": "Moderate: better than the baseline, but the gain is modest or changes between periods. Use predictions as a guide only.",
        "rel_verdict_weak": "Weak: the model is not clearly better than the baseline on your data. Do not use its predictions for decisions.",
        "rel_not_enough": "Not enough data for a reliable check: several periods with both profitable and loss-making sales are needed.",
        "rel_note": "These numbers are measured on YOUR data. Performance on future data can be lower if business conditions change.",
        "download_scored": "⬇️ Download data with profit probability (CSV)",
        "scored_note": (
            "Every row gets the probability that the sale is profitable and a risk level (Low / Medium / High). "
            "Rows with `In Training Set = 1` were used to train the model, so their probabilities are optimistic; "
            "judge the model on rows with `In Training Set = 0`."
        ),
        "pbi_title": "Export for Power BI",
        "pbi_desc": (
            "One pack with the cleaned data, the model predictions, the forecast, a monthly summary, the quality report, "
            "ready-made DAX measures and the setup guide."
        ),
        "pbi_download": "⬇️ Download Power BI pack (ZIP)",
        "pbi_model_missing": "Predictions are added to the pack after you train the model in the ML tab.",
        "pbi_prepare": "Prepare the Power BI pack",
        "pbi_preparing": "Building the files (cleaned data, forecast, predictions)...",
        "pbi_ready": "The pack is ready: {files} files.",
        "pbi_files": (
            "- **`power_bi_data.xlsx` — ONE Excel file with every table** (Sales, Forecast, Monthly, Quality, ModelMetrics, Status). "
            "In Power BI: Get data ▸ Excel workbook ▸ tick all tables.\n"
            "- CSV files of the same tables (`sales_scored.csv` when the model is trained, `cleaned_sales.csv`, `forecast.csv`, ...)\n"
            "- `measures.dax`, `load_sales.pq`, `README_POWERBI.md` and **`STEP_BY_STEP.md`** (the full setup guide)"
        ),
        "pbi_download_xlsx": "⬇️ Download ONE Excel file for Power BI",
        "pbi_download_dashboard": "⬇️ Download the READY Power BI dashboard (.pbip project)",
        "pbi_dashboard_note": (
            "Unzip it into `C:\\SalesIntelligence\\` (the Excel file is inside), open `Sales Dashboard.pbip` with Power BI Desktop and press Refresh. "
            "It has 4 pages: Overview, Forecast, Loss risk, Data quality. It was built with Microsoft's published project format and "
            "checked against Microsoft's JSON schemas, but it has not been opened in Power BI Desktop yet. If Power BI shows an error, "
            "use `STEP_BY_STEP.md` (the manual way) and send me the error."
        ),
        "download_model": "⬇️ Download the trained model (.joblib)",
        "download_model_package": "⬇️ Download the model package (ZIP: model + card + script + guide)",
        "model_export_note": (
            "To use the model in your own system. Load a .joblib file only from a source you trust (it can run code) "
            "and use the same scikit-learn version as in `model_card.json`."
        ),
        "pbi_too_big": "The data has more than {limit} rows, which is too many for one Excel file. Use the ZIP (CSV files).",
        "pbi_steps": "Setup guide: open `STEP_BY_STEP.md` inside the ZIP. The first setup takes about an hour; later refreshes take a minute.",
        "pbi_dax_title": "DAX measures (also inside the pack)",
        "pbi_refresh_title": "Automatic refresh",
        "pbi_refresh_text": (
            "1. Put each new sales file in the `inbox` folder.\n"
            "2. `python refresh_exports.py` refreshes the files in `exports` once; add `--watch 300` to keep watching the folder.\n"
            "3. Schedule it with Windows Task Scheduler (`run_refresh_windows.bat`) or cron.\n"
            "4. In Power BI Service, schedule the dataset refresh. Power BI Desktop does not refresh by itself. "
            "Files on a local computer or server need an on-premises data gateway, and Pro allows 8 scheduled refreshes per day."
        ),
        "ans_forecast": "Forecast for {month}: {metric} {value} (likely range {low} to {high}). {verdict}",
        "tool_forecast": "forecast",
        "err_empty": "The dataset is empty.",
    },
    "ar": {
        # ---- general ----
        "app_title": "📊 ذكاء المبيعات — تعلّم الآلة",
        "app_caption": "تحليل المبيعات + التنبؤ بالربحية + RAG محلي + وكيل ذكي + مراقبة",
        "language": "Language / اللغة",
        "demo_label": "بيانات تجريبية (تُستخدم عند عدم رفع ملف)",
        "demo_en": "بيانات إنجليزية (Superstore)",
        "demo_ar": "بيانات عربية (مبيعات عربية)",
        "uploader": "ارفع ملف المبيعات (Excel أو CSV) — عربي أو إنجليزي",
        "uploader_help": "Excel (‏.xlsx ‏.xlsm ‏.xls) أو CSV/TSV. أسماء الأعمدة والقيم يمكن أن تكون بالعربية أو الإنجليزية. الحد الأقصى 50 ميجابايت.",
        "download_template": "⬇️ حمّل قالب Excel",
        "download_clean": "⬇️ حمّل البيانات بعد التنظيف (CSV)",
        "download_report": "⬇️ حمّل تقرير الجودة (CSV)",
        "login_title": "🔒 تسجيل الدخول",
        "login_prompt": "كلمة المرور",
        "login_button": "دخول",
        "login_wrong": "كلمة المرور غير صحيحة.",
        "dq_profit_from_cost": "تم حساب الربح = المبيعات − التكلفة",
        "dq_missing_optional": "أعمدة اختيارية غير موجودة (يتم تخطي ما يعتمد عليها)",
        "filters": "🔎 الفلاتر (للوحة الأعمال فقط)",
        "filter_dates": "نطاق تاريخ الطلب",
        "filter_empty": "لا توجد صفوف مطابقة للفلاتر المختارة.",
        "chart_by": "الربح حسب {dim}",
        "top10": "أعلى 10 {dim} ربحاً",
        "bottom10": "أقل 10 {dim} ربحاً",
        "ans_no_discount": "الملف المرفوع لا يحتوي على عمود خصم، لذلك تحليل الخصم غير متاح.",
        "upload_error": "تعذّرت قراءة الملف المرفوع: {error}",
        "process_error": "تعذّرت معالجة البيانات: {error}",
        "summary_error": "تعذّر حساب مؤشرات الأعمال: {error}",
        "no_rows": "لا توجد صفوف صالحة بعد التنظيف. راجع الملف وأعمدته.",
        "loaded": "تم تحميل {rows} صف من {source}. زمن المعالجة: {seconds} ثانية",
        "demo_name": "البيانات التجريبية المدمجة",
        # ---- quality report ----
        "quality_title": "🔎 تقرير جودة البيانات",
        "dq_changes": "إجمالي التصحيحات (0 = الملف كان نظيفاً أصلاً)",
        "clean_ok": "✅ الملف كان نظيفاً أصلاً: لا حاجة لأي تصحيح. (كل ملف يمرّ على نفس الفحوصات، وهذا الملف اجتازها كلها.)",
        "clean_fixed": "🧹 الملف احتاج تنظيفاً. عدد التصحيحات: {n}. راجع التقرير بالأسفل.",
        "demo_only_note": "هذا العرض العام يستخدم البيانات التجريبية المدمجة فقط. رفع الملفات متوقف.",
        "dq_before": "عدد الصفوف قبل التنظيف",
        "dq_after": "عدد الصفوف بعد التنظيف",
        "dq_removed": "الصفوف المحذوفة",
        "dq_columns": "عدد الأعمدة في الملف",
        "dq_placeholders": "رموز القيم الناقصة (N/A, null, -, ...) تم تحويلها لقيم ناقصة",
        "dq_summary_rows": "صفوف الإجمالي / المجموع المحذوفة",
        "dq_variants": "اختلافات في كتابة الأسماء تم توحيدها (مثل furniture / Furniture)",
        "dq_duplicates": "الصفوف المكررة المحذوفة",
        "dq_invalid": "صفوف ينقصها حقل مطلوب (محذوفة)",
        "dq_impossible": "صفوف بقيم مستحيلة (محذوفة)",
        "dq_filled": "أسماء فئات ناقصة تم ملؤها بـ 'غير محدد'",
        "dq_extreme": "قيم مبيعات/ربح متطرفة تم الإبقاء عليها لمراجعتك",
        "cleaning_steps_title": "ما يفعله التطبيق تلقائياً",
        "cleaning_steps": (
            "1. يجد صف العناوين الحقيقي (حتى لو أسفل عنوان تقرير) ويربط أسماء الأعمدة العربية/الإنجليزية.\n"
            "2. ينظّف النصوص: الأرقام العربية والتشكيل والمسافات الزائدة والرموز المخفية.\n"
            "3. يحوّل رموز القيم الناقصة (`N/A` و`null` و`-` و`غير متوفر` ...) إلى قيم ناقصة حقيقية.\n"
            "4. يحذف صفوف الإجمالي والمجموع (`Total` و`الإجمالي`).\n"
            "5. يوحّد اختلاف كتابة أسماء الفئات والمناطق والشرائح.\n"
            "6. يحذف الصفوف المكررة تماماً.\n"
            "7. يحوّل الأرقام (العملة و`%` والفواصل العربية و`(500)`) والخصومات والتواريخ "
            "(بما فيها أسماء الشهور العربية وأرقام تواريخ Excel).\n"
            "8. يحذف الصفوف التي ينقصها حقل مطلوب أو بها قيمة مستحيلة "
            "(المبيعات ≤ 0 أو الكمية ≤ 0 أو الخصم خارج 0–100% أو تواريخ قبل 1990 أو بعد 2100).\n"
            "9. يملأ أسماء الفئات الناقصة بـ `غير محدد`؛ والنموذج يعالج الأرقام الناقصة ويرمّز الفئات تلقائياً.\n"
            "10. يعرض كل ما سبق في التقرير بالأسفل لتقارنه بالملف الأصلي."
        ),
        "dq_missing_before": "الخلايا الفارغة قبل التنظيف",
        "dq_missing_after": "الخلايا الفارغة بعد التنظيف",
        "dq_sales": "إجمالي المبيعات بعد التنظيف",
        "dq_profit": "إجمالي الربح بعد التنظيف",
        "dq_discount": "تم تحويل الخصم من نسبة مئوية إلى كسر",
        "dq_date_order": "ترتيب التاريخ المكتشف",
        "dq_date_min": "أقدم تاريخ طلب",
        "dq_date_max": "أحدث تاريخ طلب",
        "dq_metric": "المؤشر",
        "dq_value": "القيمة",
        "date_order_day-first": "يوم/شهر/سنة",
        "date_order_month-first": "شهر/يوم/سنة",
        "date_order_unknown": "غير معروف (كل التواريخ ملتبسة أو بصيغة ISO)",
        "yes": "نعم",
        "no": "لا",
        "dq_note": (
            "نجاح الرفع يعني أن الملف قُرئ وعولج فقط، ولا يثبت أن القيم صحيحة من ناحية الأعمال. "
            "قارن الإجماليات بالملف الأصلي."
        ),
        # ---- tabs ----
        "tab_dashboard": "📈 لوحة الأعمال",
        "tab_model": "🤖 نموذج التعلّم الآلي",
        "tab_assistant": "🧠 المساعد الذكي",
        "tab_security": "🔐 الأمان والمراقبة",
        # ---- dashboard ----
        "overview": "نظرة عامة على الأعمال",
        "m_sales": "إجمالي المبيعات",
        "m_profit": "إجمالي الربح",
        "m_margin": "هامش الربح",
        "m_loss": "نسبة الطلبات الخاسرة",
        "chart_discount": "متوسط ربح الطلب حسب مستوى الخصم",
        "chart_monthly": "المبيعات والربح شهرياً",
        "preview": "معاينة البيانات",
        # ---- model ----
        "predict_title": "التنبؤ بالربحية",
        "train_info": "يتم تدريب النموذج عند الضغط على الزر فقط، لتبقى اللوحة سريعة.",
        "train_button": "🚀 درّب النموذج",
        "training": "جاري تدريب نموذج الربحية...",
        "train_error": "تعذّر تدريب النموذج: {error}",
        "accuracy": "الدقة (Accuracy)",
        "precision": "Precision",
        "recall": "Recall",
        "f1": "F1",
        "roc_auc": "ROC-AUC",
        "baseline_note": (
            "خط الأساس: لو توقّعنا دائماً الحالة الأكثر شيوعاً تكون الدقة {baseline}. "
            "اختُبر النموذج على {test} صف ({split}) بعد التدريب على {train} صف."
        ),
        "split_chronological": "الأحدث تاريخاً",
        "split_stratified_random_fallback": "مختارة عشوائياً",
        "target_note": "الهدف: `مربح = 1` عندما يكون الربح > 0، وإلا `0`.",
        "confusion": "مصفوفة الالتباس",
        "actual_loss": "خسارة فعلية",
        "actual_profit": "ربح فعلي",
        "pred_loss": "متوقّع: خسارة",
        "pred_profit": "متوقّع: ربح",
        "importance_title": "ما العوامل التي تحدد الربحية؟ (أهمية المتغيرات)",
        "try_title": "جرّب عملية بيع جديدة",
        "predict_button": "توقّع الربحية",
        "pred_yes": "مربحة",
        "pred_no": "خسارة / غير مربحة",
        "pred_result": "التوقع: **{label}** — احتمال الربحية: **{probability}**",
        "pred_failed": "فشل التوقع: {error}",
        "feature_missing": "العمود '{feature}' غير موجود في البيانات بعد التنظيف.",
        # ---- assistant ----
        "assistant_title": "مساعد المبيعات الذكي",
        "assistant_desc": (
            "RAG محلي + توجيه ذكي للأسئلة. اسأل بالعربية أو بالإنجليزية — يأتي الرد بلغة سؤالك. "
            "لا يُستخدم أي نموذج لغوي خارجي وتبقى بيانات الشركة داخل التطبيق."
        ),
        "examples_title": "أمثلة على الأسئلة",
        "examples": (
            "- ما هي المنطقة الأعلى ربحاً؟\n"
            "- ما هي أقل فئة من حيث المبيعات؟\n"
            "- كم ربح فئة الأثاث؟ (استخدم اسم الفئة كما في ملفك)\n"
            "- كيف يؤثر الخصم على الربح؟\n"
            "- كم إجمالي المبيعات وهامش الربح؟"
        ),
        "question_label": "اسأل سؤالاً عن المبيعات",
        "question_placeholder": "مثال: ما هي المنطقة الأقل ربحاً؟",
        "ask_button": "اسأل المساعد",
        "analyzing": "جاري التحليل...",
        "agent_tool": "أداة الوكيل",
        "assistant_failed": "فشل المساعد: {error}",
        "assistant_init_failed": "تعذّر تشغيل المساعد: {error}",
        "tool_discount_profit": "تحليل الخصم",
        "tool_entity_summary": "ملخص عنصر",
        "tool_ranking": "ترتيب",
        "tool_business_summary": "ملخص الأعمال",
        "tool_rag_retrieval": "استرجاع من البيانات (RAG)",
        # ---- security ----
        "security_title": "الأمان",
        "security_points": (
            "- يقبل ملفات Excel/CSV/TSV فقط (.xlsx ‏.xlsm ‏.xls ‏.csv ‏.tsv ‏.txt).\n"
            "- حجم الملف محدود بـ 50 ميجابايت و1,000,000 صف (`.streamlit/config.toml` و `src/security.py`).\n"
            "- يتم التحقق من الأعمدة المطلوبة عند الرفع (بأسماء عربية أو إنجليزية).\n"
            "- حماية اختيارية بكلمة مرور: عيّن متغير البيئة `APP_PASSWORD`.\n"
            "- ملفات CSV المصدَّرة محمية من حقن المعادلات في Excel.\n"
            "- لا يتم تنفيذ أي ملف مرفوع كأكواد.\n"
            "- لا يُستخدم أي نموذج لغوي خارجي.\n"
            "- تبقى بيانات الشركة داخل عملية التطبيق أثناء تشغيله."
        ),
        "monitoring_title": "المراقبة",
        "monitoring_points": (
            "- يُسجَّل زمن معالجة البيانات.\n"
            "- تُسجَّل أخطاء الرفع والمعالجة.\n"
            "- تُسجَّل أخطاء تدريب النموذج.\n"
            "- تُسجَّل عمليات التوقع.\n"
            "- تُسجَّل أسئلة المساعد والأداة المستخدمة.\n"
            "- السجلات في الملف `logs/app.log` (انظر `src/monitoring.py`)."
        ),
        "deploy_note": (
            "ملاحظة: عند استخدام بيانات شركة حقيقية، شغّل التطبيق داخل البنية الخاصة بالشركة (VPC) "
            "وليس على خادم عرض عام."
        ),
        # ---- agent answers ----
        "ans_summary": "المبيعات: {sales} | الربح: {profit} | هامش الربح: {margin}% | نسبة الطلبات الخاسرة: {loss_rate}%.",
        "ans_total": "إجمالي {metric}: {total}.",
        "ans_best": "أعلى {dim} {metric}: {items}.",
        "ans_worst": "أقل {dim} {metric}: {items}.",
        "ans_entity": (
            "{name} ({dim}): المبيعات {sales}، الربح {profit}، هامش الربح {margin}%، "
            "نسبة الطلبات الخاسرة {loss_rate}% من {orders} طلب."
        ),
        "ans_discount_none": "متوسط الربح بدون خصم: {value}.",
        "ans_discount_positive": "متوسط الربح يظل موجباً عند كل مستويات الخصم.",
        "ans_discount_negative": "يصبح متوسط الربح سالباً بدءاً من خصم {discount} ({value} للطلب).",
        # ---- RAG ----
        "rag_header": "بناءً على البيانات المرفوعة:",
        "rag_none": "لم أجد معلومة مطابقة في البيانات المرفوعة. جرّب السؤال عن الربح أو المبيعات أو الفئة أو المنطقة أو الخصم.",
        "doc_overall": "إجمالي المبيعات {sales}. إجمالي الربح {profit}. هامش الربح {margin} بالمئة.",
        "doc_entity": (
            "{dim} {name}: المبيعات {sales}، الربح {profit}، هامش الربح {margin} بالمئة، "
            "نسبة الطلبات الخاسرة {loss_rate} بالمئة، عدد الطلبات {orders}."
        ),
        "doc_discount": "متوسط الربح عند خصم {discount} هو {value}.",
        "doc_year": "في سنة {year} بلغت المبيعات {sales} وبلغ الربح {profit}.",
        # ---- bilingual data errors ----
        # ---- forecast / reliability / power bi ----
        "tab_forecast": "🔮 التوقعات",
        "tab_powerbi": "📤 Power BI",
        "fc_title": "توقع الشهور القادمة",
        "fc_desc": (
            "توقع إحصائي من تاريخ مبيعاتك الشهري. تُختبر عدة طرق بسيطة على الشهور الماضية في بياناتك أنت، "
            "وتُستخدم الأدق منها، وتُقارن بأبسط تخمين (الشهر القادم = الشهر الماضي)."
        ),
        "fc_what": "ماذا تريد أن تتوقع؟",
        "fc_sales": "المبيعات",
        "fc_profit": "الربح",
        "fc_horizon": "عدد الشهور القادمة",
        "all_values": "الكل",
        "fc_failed": "تعذّر حساب التوقع: {error}",
        "fc_not_enough": "التاريخ غير كافٍ: يلزم {needed} شهور كاملة على الأقل (الموجود {found}).",
        "fc_partial_last": "الشهر الأخير ({month}) يبدو غير مكتمل، لذلك لم يُستخدم في التعلّم، ويبدأ التوقع منه.",
        "fc_partial_first": "الشهر الأول ({month}) يبدأ متأخراً في الشهر، لذلك لم يُستخدم.",
        "fc_gap": "{n} شهر بلا أي مبيعات تم احتسابها صفراً.",
        "fc_next": "توقع {month}",
        "fc_range_label": "المدى المحتمل",
        "fc_method_line": "الطريقة المختارة بعد اختبارها على الشهور الماضية: **{method}**",
        "fc_error_line": "متوسط الخطأ على الشهور الماضية: **{wape}** — خط الأساس البسيط (تكرار الشهر الماضي): **{base}**",
        "fc_chart": "التاريخ والتوقع",
        "fc_history_label": "الفعلي",
        "fc_forecast_label": "التوقع",
        "fc_table": "جدول التوقعات",
        "fc_col_month": "الشهر",
        "fc_col_forecast": "التوقع",
        "fc_col_low": "الأدنى",
        "fc_col_high": "الأعلى",
        "fc_backtest": "ما دقة كل طريقة على آخر {n} شهور؟ (متوسط الخطأ، الأقل أفضل)",
        "fc_col_method": "الطريقة",
        "fc_col_error": "متوسط الخطأ",
        "fcm_naive": "تكرار الشهر الماضي",
        "fcm_moving_average": "متوسط آخر 3 شهور",
        "fcm_seasonal_naive": "نفس الشهر في العام الماضي",
        "fcm_seasonal_level": "المستوى الحديث × قوة كل شهر المعتادة",
        "fcm_trend_seasonal": "الاتجاه + الموسمية",
        "fc_verdict_good": "موثوق: الطريقة المختارة تفوّقت على خط الأساس بـ {gain} نقطة في الشهور الماضية (متوسط الخطأ {wape}).",
        "fc_verdict_ok": "متوسط الموثوقية: استخدمه كتقدير تقريبي. متوسط الخطأ في الشهور الماضية {wape} (التفوق على خط الأساس: {gain} نقطة).",
        "fc_verdict_weak": "ضعيف: التوقع ليس أفضل بوضوح من تكرار الشهر الماضي، أو خطؤه كبير ({wape}). لا تعتمد عليه.",
        "fc_naive_note": "لم تتفوق أي طريقة على تكرار الشهر الماضي، لذلك التوقع هو نفس قيمة الشهر الماضي.",
        "fc_disclaimer": (
            "التوقع يفترض أن المستقبل يشبه الماضي. العروض وتغيّر الأسعار والمنتجات الجديدة والأحداث الاقتصادية غير معروفة له. "
            "ويُقاس الخطأ الماضي على نفس الشهور التي اختيرت بها الطريقة، لذلك قد يكون الخطأ الفعلي أعلى قليلاً."
        ),
        "rel_button": "🧪 افحص موثوقية النموذج على بياناتي",
        "rel_running": "جاري اختبار النموذج على عدة فترات ماضية...",
        "rel_title": "فحص الموثوقية على بياناتك",
        "rel_desc": (
            "يتعلّم النموذج من الماضي ثم يُختبر على الفترة التالية، عدة مرات متتالية "
            "(تحقق متقاطع زمني)، ويُقارن بأفضل تخمين ثابت."
        ),
        "rel_period": "فترة الاختبار",
        "rel_train": "صفوف التدريب",
        "rel_test": "صفوف الاختبار",
        "rel_baseline": "دقة خط الأساس",
        "rel_summary": (
            "متوسط الدقة **{accuracy}** مقابل خط الأساس **{baseline}** (تفوّق **{gain}** نقطة) — "
            "متوسط ROC-AUC **{auc}** — التفاوت بين الفترات حوالي ±{spread} نقطة."
        ),
        "rel_verdict_strong": "قوي: النموذج يتفوّق بوضوح على خط الأساس في كل الفترات المختبرة. ومع ذلك تحقق منه على بيانات جديدة قبل الاعتماد عليه.",
        "rel_verdict_moderate": "متوسط: أفضل من خط الأساس، لكن التفوق محدود أو يتغيّر بين الفترات. استخدم التوقعات للاسترشاد فقط.",
        "rel_verdict_weak": "ضعيف: النموذج ليس أفضل بوضوح من خط الأساس على بياناتك. لا تستخدم توقعاته في القرارات.",
        "rel_not_enough": "البيانات غير كافية لفحص موثوق: يلزم عدة فترات فيها عمليات رابحة وخاسرة.",
        "rel_note": "هذه الأرقام مقاسة على بياناتك أنت. قد يقل الأداء على بيانات المستقبل إذا تغيّرت ظروف العمل.",
        "download_scored": "⬇️ حمّل البيانات مع احتمال الربح (CSV)",
        "scored_note": (
            "كل صف يحصل على احتمال أن تكون العملية رابحة ومستوى مخاطرة (Low / Medium / High). "
            "الصفوف التي قيمة `In Training Set` فيها 1 استُخدمت لتدريب النموذج، فاحتمالاتها متفائلة؛ "
            "احكم على النموذج من الصفوف التي قيمتها 0."
        ),
        "pbi_title": "التصدير إلى Power BI",
        "pbi_desc": (
            "حزمة واحدة فيها البيانات النضيفة وتوقعات النموذج والتوقع المستقبلي وملخص شهري وتقرير الجودة "
            "ومعادلات DAX جاهزة ودليل الإعداد."
        ),
        "pbi_download": "⬇️ حمّل حزمة Power BI (ZIP)",
        "pbi_model_missing": "تُضاف توقعات النموذج للحزمة بعد تدريبه من تاب النموذج.",
        "pbi_prepare": "جهّز حزمة Power BI",
        "pbi_preparing": "جاري بناء الملفات (البيانات النضيفة والتوقع والتنبؤات)...",
        "pbi_ready": "الحزمة جاهزة: {files} ملفات.",
        "pbi_files": (
            "- **`power_bi_data.xlsx` — ملف Excel واحد فيه كل الجداول** (Sales وForecast وMonthly وQuality وModelMetrics وStatus). "
            "في Power BI: Get data ▸ Excel workbook ▸ علّم كل الجداول.\n"
            "- ملفات CSV لنفس الجداول (`sales_scored.csv` بعد تدريب النموذج، و`cleaned_sales.csv`، و`forecast.csv`، ...)\n"
            "- `measures.dax` و`load_sales.pq` و`README_POWERBI.md` و**`STEP_BY_STEP.md`** (دليل الإعداد الكامل)"
        ),
        "pbi_download_xlsx": "⬇️ حمّل ملف Excel واحد لـ Power BI",
        "pbi_download_dashboard": "⬇️ حمّل لوحة Power BI الجاهزة (مشروع .pbip)",
        "pbi_dashboard_note": (
            "فك الضغط في `C:\\SalesIntelligence\\` (ملف Excel بداخله)، وافتح `Sales Dashboard.pbip` ببرنامج Power BI Desktop واضغط Refresh. "
            "فيها 4 صفحات: نظرة عامة، التوقعات، مخاطر الخسارة، جودة البيانات. بُنيت بصيغة المشاريع المنشورة من Microsoft "
            "وفُحصت مقابل JSON schemas الخاصة بها، لكنها لم تُفتح بعد داخل Power BI Desktop. لو ظهر خطأ "
            "استخدم `STEP_BY_STEP.md` (الطريقة اليدوية) وأرسل لي الخطأ."
        ),
        "download_model": "⬇️ حمّل النموذج المدرَّب (.joblib)",
        "download_model_package": "⬇️ حمّل حزمة النموذج (ZIP: النموذج + البطاقة + السكربت + الدليل)",
        "model_export_note": (
            "لاستخدام النموذج داخل نظامكم. لا تحمّل ملف .joblib إلا من مصدر موثوق (قد ينفّذ كوداً) "
            "واستخدم نفس إصدار scikit-learn المذكور في `model_card.json`."
        ),
        "pbi_too_big": "البيانات أكثر من {limit} صف، وهذا كثير على ملف Excel واحد. استخدم الحزمة (ملفات CSV).",
        "pbi_steps": "دليل الإعداد: افتح `STEP_BY_STEP.md` داخل الحزمة. الإعداد الأول يستغرق نحو ساعة، والتحديثات بعده دقيقة.",
        "pbi_dax_title": "معادلات DAX (موجودة أيضاً داخل الحزمة)",
        "pbi_refresh_title": "التحديث التلقائي",
        "pbi_refresh_text": (
            "1. ضع كل ملف مبيعات جديد في مجلد `inbox`.\n"
            "2. الأمر `python refresh_exports.py` يحدّث الملفات في `exports` مرة واحدة؛ أضف `--watch 300` لمراقبة المجلد باستمرار.\n"
            "3. جدوله بـ Windows Task Scheduler (الملف `run_refresh_windows.bat`) أو cron.\n"
            "4. في Power BI Service اضبط التحديث المجدول للـ Dataset. برنامج Power BI Desktop لا يحدّث نفسه. "
            "الملفات على جهاز أو سيرفر محلي تحتاج On-premises data gateway، وحساب Pro يسمح بـ 8 تحديثات مجدولة يومياً."
        ),
        "ans_forecast": "توقع {month}: {metric} {value} (المدى المحتمل من {low} إلى {high}). {verdict}",
        "tool_forecast": "توقع",
        "err_empty": "الملف فارغ.",
    },
}


def t(lang, key, **kwargs):
    """Return the text for `key` in `lang` ('ar' or 'en'), filling {placeholders}."""
    text = TEXT[lang][key]
    return text.format(**kwargs) if kwargs else text
