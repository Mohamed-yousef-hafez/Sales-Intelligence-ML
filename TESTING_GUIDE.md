# دليل اختبار البرنامج بالكامل | Full testing guide

كل خطوة فيها **الأمر أو الإجراء** و**النتيجة المتوقعة**. الأرقام المتوقعة اتحسبت من البيانات التجريبية نفسها.
> قد تختلف **دقة النموذج** بنحو ±1 نقطة و**قيمة التوقع** بنحو ±2% حسب إصدارات المكتبات عندك. باقي الأرقام ثابتة بالمليم.

افتح Terminal داخل فولدر المشروع وفعّل الـ venv (على Windows: `.venv\Scripts\activate`) ثم ثبّت أدوات الاختبار مرة واحدة: `pip install -r requirements-dev.txt`.

---

## المرحلة 1: الاختبارات الآلية (دقيقتان)
```
pytest -q
```
**المتوقع:** `100 passed` (نحو دقيقة ونصف). أي رقم مختلف أو `failed` ← ابعتلي آخر 30 سطر من الناتج.

| ملف الاختبار | بيغطي إيه |
|---|---|
| `test_cleaning.py` | التنظيف: متسخ، تكرار، تواريخ Excel، خصم، عناوين فوق الجدول |
| `test_data.py` / `test_bilingual.py` | الأرقام والتواريخ والأعمدة بالعربي والإنجليزي |
| `test_company_readiness.py` | أعمدة اختيارية، التكلفة، Excel متعدد الأوراق، `.xls`، الفواصل، الأخطاء الواضحة، كلمة السر، قالب Excel |
| `test_agent.py` | المساعد: أعلى/أقل، الخصم، أسماء من بياناتك، بالعربي والإنجليزي |
| `test_forecast_and_powerbi.py` | التوقع، فحص الموثوقية، ملفات Power BI، ملف Excel الواحد، الدليل مقابل DAX، التحديث التلقائي |
| `test_manual_test_files.py` | **ملفات الاختبار المولّدة (المرحلة 2) مقابل نتيجتها الصحيحة** |
| `test_app_source.py` | يمنع ظهور كلام زائد على الشاشة (خطأ `DeltaGenerator` القديم) |

لتشغيل مجموعة واحدة: `pytest tests/test_cleaning.py -q`

---

## المرحلة 2: توليد ملفات الاختبار (دقيقة)
```
python tools/make_test_files.py
```
بينشئ فولدر `test_files/` فيه 12 حالة، ومعاه `expected.json` بالنتيجة الصحيحة لكل ملف.
الملفات المتسخة اتعملت من البيانات النضيفة، فالنتيجة الصحيحة معروفة مسبقاً.

| الملف | اللي فيه | الصفوف المتوقعة بعد التنظيف |
|---|---|---|
| `01_clean_english.csv` | بيانات نضيفة (Superstore) | **10,194** (0 محذوف) |
| `02_dirty_arabic.csv` | عربي متسخ جداً: عناوين تقرير فوق، صف «الإجمالي»، 40 مكرر، `N/A` و`-` و`غير متوفر`، كمية 0، خصم 150%، مبيعات `ج.م`، شهور عربية، أسماء فئات بأشكال مختلفة | **9,790** |
| `03_dirty_english.xlsx` | Excel: أول ورقة ملاحظات والبيانات في الثانية، تواريخ كأرقام Excel، صف `Total`، مكرر، قيم مستحيلة | **2,881** |
| `04_semicolon_decimal_comma.csv` | فاصل `;` وفاصلة عشرية (`16,448` تعني 16.448) بترميز Windows العربي | **1,990** |
| `05_cost_instead_of_profit.xlsx` | فيه التكلفة بدل الربح | **1,989** |
| `06_minimal_columns.csv` | تاريخ ومبيعات وربح فقط | **10,118** |
| `07_not_enough_data.csv` | 25 صف فقط | **25** (والنموذج يرفض برسالة) |
| `08_all_profitable.csv` | كل العمليات رابحة | **400** (والنموذج يرفض برسالة) |
| `09_missing_order_date.csv` | بدون عمود تاريخ | رسالة خطأ تذكر `Order Date` |
| `10_old_excel.xls` | ملف Excel قديم | **50** |
| `11_short_history.csv` | 6 شهور فقط | **692** (والتوقع يرفض) |
| `12_two_files_for_refresh/` | ملفين متداخلين (للتحديث التلقائي) | **5,000** |

---

## المرحلة 3: اختبار الواجهة (30 دقيقة)
```
streamlit run app.py
```
يفتح على `http://localhost:8501`.

### 3.1 اللغة والبيانات التجريبية
1. القائمة الجانبية: بدّل **العربية ⇄ English**. المتوقع: كل النصوص تتغيّر، والاختيارات (البيانات التجريبية، الموديل لو دُرّب) **ما بتتصفّرش**.
2. اختر **English demo** ثم **Arabic demo**. بعد كل اختيار شوف تقرير الجودة:

| | English demo | Arabic demo |
|---|---|---|
| صفوف قبل ← بعد | 10,194 ← **10,194** | 10,194 ← **10,192** (مكرران) |
| إجمالي المبيعات | **2,326,534** | **2,326,154** |
| إجمالي الربح | **292,297** | **292,273** |
| هامش الربح / نسبة الخاسر | 12.56% / 19.29% | 12.56% / 19.28% |
| ترتيب التاريخ المكتشف | شهر/يوم/سنة | **يوم/شهر/سنة** |
| الخصم اتحوّل من نسبة مئوية | لا | **نعم** |

> ⏱️ **زمن المعالجة:** «Processing time» للبيانات التجريبية لازم يكون **أقل من 5 ثواني** (عندي 0.5 ثانية). لو طلع أكتر من 20 ثانية، شغّل `python tools/diagnose_speed.py` وابعتلي الناتج (بيقيس كمان هل الموديل أسرع بكل الأنوية ولا بنواة واحدة، ولو أبطأ اضبط `SALES_ML_JOBS=1` في نفس النافذة قبل تشغيل التطبيق: PowerShell `$env:SALES_ML_JOBS="1"` — CMD `set SALES_ML_JOBS=1`)، وافحص Task Manager (أكتر من نسخة python/streamlit شغّالة، أو الرام/المعالج مشغولين).

### 3.2 رفع الملفات المولّدة
ارفع كل ملف من `test_files/` (زرار Upload) وتحقق:

| الملف | اللي لازم تشوفه |
|---|---|
| `02_dirty_arabic.csv` | «Rows after cleaning» = **9,790**. في التقرير: صف إجمالي محذوف = 1، مكرر ≈ 40، قيم مستحيلة > 0، المناطق **4 + «غير محدد»** (مفيش منطقة اسمها `N/A` أو `-`)، والفئات في الرسم **3 فقط** |
| `03_dirty_english.xlsx` | **2,881** صف، والفئات `Furniture` و`Office Supplies` و`Technology` فقط (مفيش `furniture ` أو `FURNITURE`) |
| `04_semicolon_decimal_comma.csv` | **1,990** صف، والمبيعات منطقية (مش ملايين) — إجمالي **≈ 481,932** |
| `05_cost_instead_of_profit.xlsx` | «Profit calculated as Sales − Cost» = **نعم** |
| `06_minimal_columns.csv` | يفتح عادي. في التقرير «Optional columns not found» يذكر الخصم والكمية والفئة... والرسوم المرتبطة بيهم **مش ظاهرة** والباقي شغال |
| `07_not_enough_data.csv` | اللوحة تشتغل. في تاب النموذج اضغط Train ← رسالة **«At least 30 valid rows…»** |
| `08_all_profitable.csv` | Train ← رسالة **«needs at least 5 profitable and 5 loss-making»** |
| `09_missing_order_date.csv` | رسالة خطأ بالعربي والإنجليزي فيها **Order Date (تاريخ الطلب)** والتطبيق ما يقعش |
| `10_old_excel.xls` | **50** صف |
| `11_short_history.csv` | تاب التوقعات: «at least 9 complete months» |

### 3.3 لوحة الأعمال (English demo)
- المؤشرات: 2,326,534 / 292,297 / 12.56% / 19.29%.
- «Profit by Category»: Technology ≈ **146,543**، Office Supplies ≈ **126,023**، Furniture ≈ **19,730**.
- الفلاتر (Filters): اختر Region = West ← المبيعات تقل، ورجّعها ← ترجع الأرقام الأصلية. اختر فترة تواريخ لا فيها بيانات ← رسالة «No rows match».
- أعلى 10 / أسوأ 10 منتجات: أعلى منتج **Canon imageCLASS 2200 Advanced Copier** (≈ 25,200)، وأسوأ **Cubify CubeX 3D Printer Double Head Print** (≈ −8,880). عمود الربح ظاهر من غير Scroll.
- معاينة البيانات: التواريخ من غير `00:00:00`.

### 3.4 تاب النموذج
1. اضغط **Train ML Model**. المتوقع (English demo): الدقة **≈ 94%**، Precision ≈ 97%، ROC-AUC ≈ **98.4%**، وتحتها: «Baseline … **80.4%**».
2. «What drives profitability»: أطول عمود **Discount** (≈ 0.52).
3. اضغط **Check reliability on my data**. المتوقع (طابق لقطتك): جدول 5 فترات، متوسط الدقة ≈ **94.1%** مقابل خط الأساس ≈ **80.6%**، تفوق ≈ **13.5 نقطة**، ROC-AUC ≈ 0.983، التفاوت ±0.5، والحكم **Strong** (أخضر).
4. حمّل **«data with profit probability»** وافتحه: لازم تلاقي `Profit Probability` و`Predicted Profitable` و`Risk Level` و`In Training Set`. افلتر `In Training Set = 0` وقارن `Predicted Profitable` مع `Profitable`: الدقة تقارب رقم الدقة في الواجهة.
5. «Try a New Transaction»: اترك القيم الافتراضية واضغط Predict ← نتيجة بدون أي كتلة نص إضافية تحتها (PROFITABLE بنسبة ≈ **90%**). غيّر Discount إلى **0.5** ← الاحتمال ينزل إلى ≈ **17%** (وتظهر «LOSS»).

### 3.5 تاب التوقعات
- English demo، Sales (الأرقام دي مطابقة للقطتك بالمليم): **توقع 2027-01 = 42,674**، المدى **18,483 — 66,866**، الطريقة **Trend + seasonality**، الخطأ **18.8%** مقابل خط الأساس **25.1%**، والحكم **Moderate** (تفوق 6.3 نقطة). الجدول تحت: 2027-02 = 33,595 و2027-03 = 71,325، وترتيب الطرق الخمس بنفس الأرقام (18.8 / 21.7 / 24.6 / 25.1 / 26.3%).
- غيّر إلى **Profit** ← **8,656** (المدى 6,822 — 10,490)، الطريقة **Repeat last month**، والحكم **Moderate** بتفوق 0.0 نقطة، **وتحتها ملاحظة** أن التوقع مجرد قيمة الشهر الماضي.
- ثم **Months ahead = 6** ← 6 صفوف في الجدول وبدون أخطاء.
- اختر الفئات واحدة واحدة: **Furniture ← Reliable (خطأ ≈ 15%)**، **Office Supplies ← Weak**، **Technology ← Moderate**. (الاختلاف طبيعي: مبيعات كل فئة لها سلوك مختلف.)
- ملف `11_short_history.csv` ← «not enough».

### 3.6 المساعد (اسأل بالنص بالظبط)
| السؤال | الإجابة المتوقعة (English demo) |
|---|---|
| Which region has the highest profit? | `Highest-profit region: West (110,798.82)` |
| Which region has the lowest profit? | `Lowest-profit region: Central (39,865.31)` |
| What is the profit of Furniture? | `Furniture (category): sales 754,747.76, profit 19,730.00, margin 2.61%, loss rate 34.76% across 2201 orders` |
| How does discount affect profit? | `Average profit with no discount: 66.34 … negative starting at a 30% discount (-45.71 per order)` |
| What is the sales forecast for next month? | `Forecast for 2027-01: sales 42,674 (likely range 18,483 to 66,866). Moderate: …` |

وبالعربي مع **Arabic demo**:
| السؤال | المتوقع |
|---|---|
| ما هي المنطقة الأعلى ربحاً؟ | `أعلى منطقة ربحاً: الغرب (110,798.82)` |
| كم ربح فئة أثاث؟ | `أثاث (فئة): المبيعات 754,367.27، الربح 19,706.64 …` |
| كيف يؤثر الخصم على الربح؟ | `… يصبح متوسط الربح سالباً بدءاً من خصم 30%` |
| ما هي أقل فئة من حيث المبيعات؟ | `أقل فئة مبيعاً: مستلزمات مكتبية (731,893.31)` |
| توقع مبيعات الشهر الجاي | `توقع 2027-01: المبيعات ≈ 42,7xx …` |

> سؤال خارج النطاق (مثلاً `hello`) ← رسالة «could not find a matching fact» مش خطأ.

### 3.7 التحميلات
- **Download the Excel template** (عربي وإنجليزي): افتحه، ثم ارفعه تاني في البرنامج ← 3 صفوف بدون أخطاء.
- **Download the cleaned data (CSV)**: افتحه في Excel ← العربي سليم.
- **Download the quality report (CSV)**: نفس أرقام الشاشة.

---

## المرحلة 3.8: ملفات جديدة (الموديل والداشبورد ومؤشر التنظيف)
| الاختبار | الخطوات | المتوقع |
|---|---|---|
| مؤشر التنظيف | غيّر بين English demo وArabic demo | English: رسالة خضراء «**already clean**» (0 تصحيح). Arabic: رسالة زرقاء «**needed cleaning: 3 corrections**» |
| تحميل الموديل | تاب ML Model ← Train ← زرارين تحت: `.joblib` وحزمة ZIP | الـ ZIP فيه `profit_model.joblib` و`model_card.json` و`use_model.py` و`README_MODEL.md` |
| الموديل خارج البرنامج | فك الـ ZIP في فولدر، حط ملف مبيعات فيه الأعمدة (انسخ `cleaned_sales.csv`)، ثم `python use_model.py cleaned_sales.csv` | يكتب `scored_sales.csv` ومعاه `Profit Probability` و`Risk Level` |
| الداشبورد الجاهزة | تاب Power BI ← Prepare ← **Download the READY Power BI dashboard** | ملف `power_bi_dashboard.zip` فيه `Sales Dashboard.pbip` و`power_bi_data.xlsx` |
| فحص الداشبورد | فك الـ ZIP في فولدر ثم `python tools/validate_pbip.py "المسار"` | `0 problems` (يحمّل schemas Microsoft أول مرة، ويحتاج git وإنترنت) |
| وضع العرض العام | `$env:APP_DEMO_ONLY="1"` (PowerShell) أو `set APP_DEMO_ONLY=1` (CMD) ثم `streamlit run app.py` | مفيش زرار Upload، وتظهر رسالة «public demo» |

## المرحلة 4: Power BI (ساعة)
1. تاب **Power BI** ← **Prepare the Power BI pack** ← حمّل **ملف Excel الواحد** وافتحه في Excel: الأوراق `Sales` و`Forecast` و`Monthly` و`Quality` و`ModelMetrics` و`Status` و`README`، والتواريخ بدون `00:00:00`.
2. **الطريقة الأسرع:** فك `power_bi_dashboard.zip` في `C:\SalesIntelligence\` وافتح `Sales Dashboard.pbip` في Power BI Desktop، ثم Home ▸ Refresh (لو البيانات ما تحمّلتش: Transform data ▸ Edit parameters ▸ `DataFile`). **لو ظهر خطأ ابعتلي نصه ولقطة الشاشة.**
   **الطريقة اليدوية:** اتبع **`powerbi/STEP_BY_STEP.md`** كاملاً (موجود داخل الحزمة أيضاً).
3. **معيار النجاح** (English demo):

| الـ Measure | القيمة المتوقعة |
|---|---|
| `[Total Sales]` | **2,326,534** (= «Total sales after cleaning» في جدول Quality) |
| `[Total Profit]` | **292,297** |
| `[Profit Margin %]` | **12.56%** |
| `[Loss Rate %]` | **19.29%** (1,966 من 10,194) |
| `[Avg Discount]` | **15.54%** |
| `[Best Category]` / `[Worst Category]` | **Technology** / **Furniture** |
| `[Worst Region]` | **Central** |
| `[Best Product]` | Canon imageCLASS 2200 Advanced Copier |
| مبيعات 2024 و`[Sales LY]` لسنة 2025 | 472,993 (2024) ← تظهر كـ Sales LY داخل 2025 |
| `[Sales YoY %]` لسنة 2025 | (613,934 − 472,993) ÷ 472,993 ≈ **29.8%** |
| `[High Risk Orders]` | رقم > 0 (لو درّبت النموذج قبل التصدير) |

4. **لو أي رقم مختلف:** ابعتلي رسالة الخطأ أو لقطة الشاشة، ولاحظ أن الـ DAX لم يُجرَّب داخل Power BI قبل كده.

---

## المرحلة 5: التحديث التلقائي (10 دقائق)
```
python refresh_exports.py --input test_files/12_two_files_for_refresh --output out_test --combine
```
- المتوقع: `OK: done` و`Wrote 12 files`. في `out_test/` ملف `power_bi_data.xlsx` وباقي الملفات، و`refresh_status.csv` فيه `Status = OK` وصفوف **5,000**، **وما فيش ملفات `.tmp`**.
- **اختبار الفشل:** اكتب ملف بايظ: `echo a,b > test_files/12_two_files_for_refresh/zz_bad.csv` ثم شغّل نفس الأمر ← `FAILED`، وملفات `out_test` القديمة **سليمة** و`refresh_status.csv` فيه `FAILED` وسببه. (امسح `zz_bad.csv` بعدها.)
- **اختبار المراقبة:** `python refresh_exports.py --input inbox --output exports --watch 10` ثم انسخ ملف مبيعات إلى `inbox` ← بعد ثواني يظهر `OK`، ولو ما تغيّرش حاجة **ما يعيدش التشغيل**. اضغط Ctrl+C للإيقاف.

---

## المرحلة 6: الأمان (15 دقيقة)
| الاختبار | الخطوات | المتوقع |
|---|---|---|
| كلمة السر | `$env:APP_PASSWORD="abc123"` (PowerShell) أو `set APP_PASSWORD=abc123` (CMD) أو `export APP_PASSWORD=abc123` (Linux/Mac) ثم `streamlit run app.py` في نفس النافذة | شاشة دخول فقط. كلمة غلط ← «Wrong password». الصحيحة ← يفتح |
| نوع ملف ممنوع | حاول ترفع `.exe` أو `.pdf` | Streamlit نفسه بيرفض النوع |
| ملف أكبر من 50MB | `python -c "open('big.csv','w').write('a,b\n'+'1,2\n'*20000000)"` ثم ارفعه | Streamlit يرفضه (حد 50MB) |
| حقن معادلات | اعمل CSV فيه عمود Category قيمته `=HYPERLINK("http://x")`، ارفعه ونزّل «cleaned data» وافتحه في Excel | الخلية نص يبدأ بـ `'` ومفيش معادلة بتشتغل |
| ملف تالف | اعمل ملف `.xlsx` فاضي بالامتداد فقط (`echo x > bad.xlsx`) | رسالة خطأ واضحة، والتطبيق ما يقعش |

---

## المرحلة 7: الأداء (10 دقائق)
ولّد ملف 100 ألف صف:
```
python -c "import pandas as pd, numpy as np; d=pd.read_csv('data/sample_superstore.csv'); b=pd.concat([d]*10,ignore_index=True); b['Sales']*=np.random.uniform(.9,1.1,len(b)); b.to_csv('big_100k.csv',index=False)"
```
ارفعه وقِس: التحميل والتنظيف **أقل من 10 ثواني**، التدريب **10–20 ثانية**، فحص الموثوقية **أقل من دقيقة**، إعداد حزمة Power BI **حوالي 50 ثانية** (كتابة Excel بطيئة). فوق 100 ألف صف ما فيش ملف Excel واحد وتظهر رسالة بدلاً منه (الـ CSV موجودة).

---

## المرحلة 8: التشغيل والنشر
- **Windows:** في فولدر نضيف جديد، دوس مرتين على `run_windows.bat` ← يفتح التطبيق.
- **Docker:** `docker compose up --build` ثم افتح `http://localhost:8501`، وحط ملف في `inbox/` وانتظر 5 دقائق ← يظهر `power_bi_data.xlsx` في `exports/`. *(مجرّب جزئياً: ملفات Docker ما اتشغّلتش في بيئة البناء.)*
- **من جهاز تاني في الشبكة:** افتح `http://عنوان-الجهاز:8501`.
- جرّب Chrome وEdge، وشوف شكل الصفحة بالعربي (اتجاه اليمين لليسار).

---

## المرحلة 9: قائمة القبول قبل التسليم للشركة
- [ ] `pytest -q` كله passed
- [ ] ملفات الاختبار الـ 12 تعطي النتائج الجدولية أعلاه
- [ ] تقرير الجودة لملفهم الحقيقي: إجمالي المبيعات والربح **يطابق ملفهم الأصلي**
- [ ] جرّبت ملف حقيقي من الشركة نفسها، والنموذج مرّ على «فحص الموثوقية» (Strong أو Moderate)
- [ ] التوقع ظهر بحكم (Reliable/Moderate/Weak) وأبلغتهم بمعناه
- [ ] اتبعت `STEP_BY_STEP.md` ونجح اختبار الصحة في Power BI (Total Sales يطابق Quality)
- [ ] اختبرت التحديث التلقائي مرة (ملف جديد → Refresh)
- [ ] كلمة السر مفعّلة إذا يستخدمه أكثر من شخص
- [ ] اختبرت Docker أو `run_windows.bat` على جهاز الشركة

---

## لو ظهرت مشكلة، ابعتلي
1. الخطوة اللي كنت فيها، والنتيجة المتوقعة، والنتيجة الفعلية.
2. لقطة شاشة (أو نص الخطأ).
3. آخر 20 سطر من `logs/app.log`.
4. لو الملف مش حساس: الملف نفسه (أو أول 20 صف منه بعد إخفاء الأسماء).
