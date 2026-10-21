# ربط Sales Intelligence بـ Power BI | Power BI guide

> **الأسرع:** نزّل **`power_bi_dashboard.zip`** من تاب Power BI: مشروع لوحة جاهزة (`Sales Dashboard.pbip`) بـ 4 صفحات، افتحه ببرنامج Power BI Desktop واضغط Refresh (التعليمات داخل `README_DASHBOARD.md`).
> لو ظهر خطأ، أو أردت بناء اللوحة بنفسك، فاستخدم ملف Excel الواحد `power_bi_data.xlsx` واتبع الدليل المفصّل **`STEP_BY_STEP.md`** (خطوة بخطوة مع قائمة تأكد وحل مشاكل).
> هذا الملف الحالي ملخّص ومرجع.

## 1) الملفات اللي بيطلّعها البرنامج
تحصل عليها بطريقتين: زرار **Download Power BI pack (ZIP)** في تاب Power BI بالتطبيق، أو تلقائياً من `refresh_exports.py` (القسم 5).

| الملف | المحتوى | يتحمّل في Power BI كجدول |
|---|---|---|
| **`power_bi_data.xlsx`** | **ملف واحد فيه كل الجداول التالية، كل جدول Excel Table باسمه** (حتى 100,000 صف) | يظهر Sales وForecast وMonthly وQuality وModelMetrics وStatus |
| `sales_scored.csv` | البيانات النضيفة + احتمال الربح لكل عملية (بعد تدريب النموذج) | **Sales** (الأفضل) |
| `cleaned_sales.csv` | البيانات النضيفة بدون توقعات | **Sales** (لو مفيش نموذج) |
| `forecast.csv` | توقع المبيعات والربح للشهور الجاية + المدى + درجة الموثوقية | **Forecast** |
| `monthly_summary.csv` | المبيعات والربح والطلبات لكل شهر (وهل الشهر كامل) | **Monthly** |
| `quality_report.csv` | تقرير جودة البيانات | **Quality** |
| `model_metrics.csv` | دقة النموذج وخط الأساس وحكم الموثوقية | **ModelMetrics** |
| `refresh_status.csv` | وقت آخر تحديث ونجاحه | **Status** |
| `measures.dax` | كل الـ Measures جاهزة | — |
| `load_sales.pq` | كود Power Query لتحميل الملف | — |

أسماء الأعمدة في الملفات **إنجليزية ثابتة دائماً** (حتى لو ملفك الأصلي عربي)، عشان الـ Measures ما تتكسرش.
أعمدة التوقعات الإضافية في `sales_scored.csv`: `Profit Probability` و`Predicted Profitable` و`Risk Level` (Low / Medium / High) و`In Training Set`.

> ⚠️ `In Training Set = 1` معناها إن النموذج اتعلّم من الصف ده، فاحتماله متفائل. احكم على النموذج من الصفوف اللي قيمتها `0` فقط.

## 2) الإعداد في Power BI Desktop (مرة واحدة)
1. **Get data ▸ Text/CSV** وحمّل `sales_scored.csv`، أو استخدم `load_sales.pq` (Blank query ▸ Advanced editor) وغيّر مسار المجلد.
   سمّي الجدول **Sales**. كرّر مع `forecast.csv` (سمّيه **Forecast**) و`monthly_summary.csv`.
2. **جدول التواريخ:** Modeling ▸ New table ▸ الصق أول كتلة في `measures.dax` (اسمها `Date`). ثم Table tools ▸ **Mark as date table**.
3. **العلاقة:** اسحب `'Date'[Date]` على `Sales[Order Date]` (واحد إلى متعدد).
4. **الـ Measures:** الصق كل كتلة في `measures.dax` **واحدة واحدة** (Modeling ▸ New measure).
5. رتّب `Month Name` بـ `Month Number` (Sort by column).

## 3) الـ KPIs المقترحة وكيف تعملها
| KPI | Measure / طريقة العمل |
|---|---|
| إجمالي المبيعات | `[Total Sales]` (Card) |
| إجمالي الربح | `[Total Profit]` (Card) |
| هامش الربح | `[Profit Margin %]` (Card) |
| نسبة الطلبات الخاسرة | `[Loss Rate %]` (Card) |
| متوسط الخصم | `[Avg Discount]` (Card) |
| المبيعات مقارنة بالعام الماضي | `[Sales LY]` و `[Sales YoY %]` (يحتاجوا جدول التواريخ) |
| أفضل / أسوأ فئة | `[Best Category]` / `[Worst Category]` (Card) |
| أفضل / أسوأ منتج | `[Best Product]` / `[Worst Product]` أو Table بفلتر Top N |
| الربح الشهري | Line chart: المحور `'Date'[Year-Month]` والقيمة `[Total Profit]` |
| متوسط الربح عند كل مستوى خصم | Column chart: المحور `Sales[Discount]` (أو `Discount Band`) والقيمة `[Avg Profit per Order]` |
| توقع الشهور الجاية | Line chart من جدول Forecast: `[Forecast Sales]` مع `[Forecast Sales Low]` و`[Forecast Sales High]` |
| عمليات عالية المخاطرة | `[High Risk Orders]` و `[High Risk Sales Amount]` |

## 4) ملاحظات صريحة
- **الـ Measures والـ M script ما اتجرّبوش داخل Power BI** (مفيش Power BI في بيئة بناء المشروع). اتكتبوا بصيغ DAX و M القياسية، وأي رسالة خطأ عندك ابعتها وتتصلّح.
- التوقعات إحصائية: راجع `Reliability` و`Backtest WAPE` (متوسط الخطأ على شهور فاتت) قبل الاعتماد عليها.

## 5) التحديث التلقائي
Power BI Desktop نفسه **ما بيحدّثش تلقائياً** (بتدوس Refresh). التحديث التلقائي بيكون من **Power BI Service** بعد النشر. المطلوب خطوتين:

**أ) تجديد الملفات تلقائياً (من ناحية البرنامج)**
حطّ ملف المبيعات الجديد في مجلد `inbox/` وشغّل:
```
python refresh_exports.py --input inbox --output exports
```
بينضّف البيانات ويدرّب النموذج ويكتب كل ملفات القسم 1 في `exports/` (بكتابة آمنة: الملف ما بيتقراش نصف مكتوب).
- مراقبة مستمرة (يعيد التشغيل لما ملف جديد ينزل في `inbox/`): `python refresh_exports.py --watch 300`
- أكتر من ملف شهري في المجلد: أضف `--combine` (يجمعهم، والمكرر بيتشال).
- جدولة على Windows: Task Scheduler ▸ Create task ▸ Action: شغّل `run_refresh_windows.bat`.
- جدولة على Linux: `crontab -e` ثم `0 * * * * cd /path/to/project && .venv/bin/python refresh_exports.py`
- Docker: خدمة `refresh` في `docker-compose.yml` بتعمل نفس الشيء.

**ب) تحديث Power BI من الملفات**
حسب توثيق Microsoft: التحديث المجدول بيحصل في Power BI Service، وحده الأقصى **8 مرات يومياً مع Pro و48 مع Premium Per User/Premium**،
والملفات الموجودة على جهاز أو سيرفر داخلي محتاجة **On-premises data gateway** مثبّت ويعمل، ولازم مسار الملف يفضل ثابت.
لذلك: انشر التقرير ▸ Dataset settings ▸ اختر الـ Gateway ▸ فعّل Scheduled refresh ▸ حدّد الأوقات (اجعلها بعد وقت تشغيل `refresh_exports.py`).
بديل بدون Gateway: ضع مجلد `exports/` على OneDrive for Business / SharePoint واتصل به من Power BI (اتأكد من قسم الـ IT عندك).
