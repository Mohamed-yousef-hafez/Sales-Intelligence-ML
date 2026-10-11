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
        "err_empty": "الملف فارغ.",
    },
}


def t(lang, key, **kwargs):
    """Return the text for `key` in `lang` ('ar' or 'en'), filling {placeholders}."""
    text = TEXT[lang][key]
    return text.format(**kwargs) if kwargs else text
