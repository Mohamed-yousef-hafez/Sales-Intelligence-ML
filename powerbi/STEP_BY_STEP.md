# دليل خطوة بخطوة: من ملف المبيعات إلى داشبورد Power BI

> **صراحة:** الدليل مكتوب بدون تشغيل Power BI فعلياً. أسماء القوائم هنا بالإنجليزية كما تظهر في Power BI Desktop؛ قد تختلف قليلاً حسب الإصدار أو لغة البرنامج.
> **الوقت المتوقع:** 45 إلى 60 دقيقة أول مرة. بعدها كل تحديث يأخذ دقيقة.

## 0) ما تحتاجه
- **Power BI Desktop** (مجاني من Microsoft Store أو موقع Microsoft).
- الملف **`power_bi_data.xlsx`** (من تاب Power BI في التطبيق ثم «جهّز الحزمة»، أو من مجلد `exports` لو استخدمت `refresh_exports.py`).
- ملف **`measures.dax`** (داخل الحزمة) مفتوح في أي محرر نصوص للنسخ منه.
- لو الملف أكبر من 100,000 صف لن تجد `power_bi_data.xlsx`؛ استخدم ملفات الـ CSV بدلاً منه (`README_POWERBI.md`).

---

## 1) تحميل البيانات (5 دقائق)
1. افتح Power BI Desktop ← **Home ▸ Get data ▸ Excel workbook** ← اختر `power_bi_data.xlsx`.
2. في نافذة **Navigator** علّم الجداول: **Sales, Forecast, Monthly, Quality, ModelMetrics, Status** (لا تعلّم `README`). ثم اضغط **Transform Data**.
3. في Power Query تأكد من أنواع الأعمدة (الأيقونة بجانب اسم العمود):
   - `Sales[Order Date]` و `Sales[Ship Date]` ← **Date** (اضغط الأيقونة واختر Date إن كانت Date/Time).
   - `Sales[Sales]` و `Profit` و `Discount` و `Profit Probability` ← **Decimal number**.
   - `Forecast[Month]` و `Monthly[Month]` ← **Date**.
4. **Home ▸ Close & Apply**.

✅ **تأكد:** في قائمة Fields على اليمين تجد الجداول: Sales وForecast وMonthly وQuality وModelMetrics وStatus.

> بعض الأعمدة اختيارية (مثل Discount أو Product). إن لم يكن عمود موجوداً في ملفك فلن تجده، وستتجاهل المعادلات التي تعتمد عليه (انظر القسم 8).

---

## 2) جدول التواريخ (5 دقائق)
مطلوب لمقارنة العام الماضي (`Sales LY`) وللرسم الشهري.
1. **Modeling ▸ New table**.
2. افتح `measures.dax` وانسخ الكتلة الأولى (التي تبدأ بـ `Date =` وتنتهي قبل «CORE KPIs») والصقها، ثم Enter.
3. اختر الجدول **Date** ثم **Table tools ▸ Mark as date table** ← اختر العمود **Date**.
4. اضغط على أيقونة **Model view** (الأيقونة الثالثة على اليسار). اسحب **`Date[Date]`** وأفلته على **`Sales[Order Date]`**.
   - تأكد أن العلاقة: **Many to one**… أي من Sales (كثير) إلى Date (واحد)، واتجاه الفلترة **Single**.
5. ارجع إلى Data view، اختر العمود **Month Name** في جدول Date ثم **Column tools ▸ Sort by column ▸ Month Number**.

✅ **تأكد:** في Model view يظهر خط بين Date وSales.

---

## 3) المعادلات Measures (15 دقيقة)
لكل معادلة: **Modeling ▸ New measure** ← الصق المعادلة (واحدة فقط في كل مرة) ← Enter.
الأفضل أن تنشئها وأنت مختار جدول **Sales**.

ابدأ بهذا الترتيب (من `measures.dax`):
1. `Total Sales` · `Total Profit` · `Profit Margin %` · `Orders` · `Loss Orders` · `Loss Rate %` · `Avg Discount` · `Avg Profit per Order`
2. `Sales LY` · `Sales YoY %` · `Profit LY` · `Profit YoY %` · `Profit Prev Month` · `Profit MoM Change`
3. `Best Category` · `Worst Category` · `Best Product` · `Worst Product` · `Best Region` · `Worst Region`
4. `Forecast Sales` · `Forecast Sales Low` · `Forecast Sales High` · `Forecast Profit`
5. `High Risk Orders` · `High Risk Sales Amount` · `Predicted Loss Orders` · `Avg Profit Probability` · `Model Accuracy Unseen`

لتنسيق النسب: اختر المعادلة ثم **Measure tools ▸ Format ▸ Percentage** للمعادلات المنتهية بـ `%`.

**الأعمدة المحسوبة (Calculated columns)** لتجميع الخصم:
**Modeling ▸ New column** (والجدول Sales مختار) ← الصق `Discount Band` ثم أعد العملية مع `Discount Band Order`.
بعدها اختر `Discount Band` ← **Column tools ▸ Sort by column ▸ Discount Band Order**.

### ✅ اختبار الصحة (مهم جداً)
1. أضف **Card** (من Visualizations) وضع فيه `[Total Sales]`.
2. افتح جدول **Quality** وابحث عن الصف «Total sales after cleaning».
3. **الرقمان لازم يتطابقا.** لو لم يتطابقا فهناك فلتر أو علاقة خاطئة (انظر القسم 8).

---

## 4) بناء الصفحات (20 دقيقة)
من **Visualizations** اسحب الحقول إلى الأماكن المذكورة.

### الصفحة 1: نظرة عامة (Overview)
| العنصر | النوع | الحقول |
|---|---|---|
| إجمالي المبيعات | Card | `[Total Sales]` |
| إجمالي الربح | Card | `[Total Profit]` |
| هامش الربح | Card | `[Profit Margin %]` |
| نسبة الطلبات الخاسرة | Card | `[Loss Rate %]` |
| متوسط الخصم | Card | `[Avg Discount]` |
| النمو عن العام الماضي | Card | `[Sales YoY %]` |
| أفضل / أسوأ فئة | 2 Cards | `[Best Category]` و `[Worst Category]` |
| أفضل / أسوأ منتج | 2 Cards | `[Best Product]` و `[Worst Product]` |
| الربح حسب الفئة | Clustered column | Axis: `Sales[Category]` · Values: `[Total Profit]` |
| المبيعات والربح شهرياً | Line chart | Axis: `Date[Year-Month]` · Values: `[Total Sales]` و `[Total Profit]` |
| أعلى 10 منتجات ربحاً | Bar chart | Axis: `Sales[Product]` · Values: `[Total Profit]` · في **Filters** ضع Product ← **Top N = 10** حسب `[Total Profit]` |
| أسوأ 10 منتجات | Bar chart | نفس السابق مع **Bottom N = 10** |
| الربح عند كل مستوى خصم | Column chart | Axis: `Sales[Discount Band]` · Values: `[Avg Profit per Order]` |
| فلاتر | Slicer × 3 | `Date[Year]` و `Sales[Region]` و `Sales[Category]` |

### الصفحة 2: التوقعات (Forecast)
| العنصر | النوع | الحقول |
|---|---|---|
| توقع المبيعات | Line chart | Axis: `Forecast[Month]` · Values: `[Forecast Sales]` و `[Forecast Sales Low]` و `[Forecast Sales High]` |
| توقع الربح | Card أو Column | `[Forecast Profit]` |
| جدول التفاصيل | Table | `Forecast[Metric]` و `Month` و `Forecast` و `Lower` و `Upper` و `Method` و `Reliability` و `Backtest WAPE` |

> **قبل الاعتماد على التوقع** انظر `Reliability` (good / ok / weak) و`Backtest WAPE` (متوسط الخطأ على شهور ماضية). `weak` معناها: لا تعتمد عليه.

### الصفحة 3: مخاطر الخسارة (Risk)
| العنصر | النوع | الحقول |
|---|---|---|
| عمليات عالية المخاطرة | Card | `[High Risk Orders]` |
| مبيعاتها | Card | `[High Risk Sales Amount]` |
| دقة النموذج على بيانات لم يتعلمها | Card | `[Model Accuracy Unseen]` |
| المخاطرة حسب المنطقة | Matrix | Rows: `Sales[Region]` · Columns: `Sales[Risk Level]` · Values: `[Orders]` |
| أخطر العمليات | Table | `Sales[Order ID]` أو أي معرّف و`Product` و`Sales` و`Profit Probability` · في **Filters** ضع `Risk Level = High` |

> **ملاحظة:** هذه الصفحة تعمل فقط إذا كانت البيانات قد دُرّبت (جدول Sales فيه عمود `Risk Level`). الصفوف التي `In Training Set = 1` احتمالاتها متفائلة.

---

## 5) الحفظ والنشر
1. **File ▸ Save as** واحفظ باسم مثل `Sales Dashboard.pbix`.
2. للمشاركة مع آخرين: **Home ▸ Publish** (يحتاج حساب Power BI).

## 6) عندما يصلك ملف مبيعات جديد
**الطريقة اليدوية (بسيطة):**
1. من التطبيق: ارفع الملف ثم «جهّز الحزمة» وحمّل `power_bi_data.xlsx`.
2. **ضعه مكان الملف القديم بنفس الاسم والمسار** (استبدله).
3. في Power BI Desktop اضغط **Home ▸ Refresh**. الداشبورد كله يتحدّث ولا تحتاج تعيد بناء شيء.

**الطريقة شبه التلقائية:**
1. ضع الملف الجديد في مجلد `inbox`.
2. شغّل `python refresh_exports.py` (أو جدوله). يكتب `exports/power_bi_data.xlsx` بنفس المسار دائماً.
3. اجعل Power BI يقرأ هذا الملف من `exports`، ثم Refresh.

**التحديث بدون ضغط Refresh:** انشر الملف على Power BI Service واضبط **Scheduled refresh** (حسب Microsoft: حتى 8 مرات يومياً مع Pro، والملفات المحلية تحتاج On-premises data gateway). Desktop لا يحدّث نفسه.

> اغلق ملف Excel قبل Refresh، وإلا قد يفشل التحديث.

---

## 7) قائمة التأكد النهائية
- [ ] `Total Sales` يساوي «Total sales after cleaning» في جدول Quality.
- [ ] مجموع الربح يساوي «Total profit after cleaning».
- [ ] `Sales LY` يظهر أرقاماً (وليس فارغاً) لو عندك أكثر من سنة.
- [ ] صفحة التوقعات تعرض `Reliability` بجانب الأرقام.
- [ ] ملف `.pbix` محفوظ ومسار ملف البيانات ثابت.

---

## 8) حل المشاكل

| المشكلة | السبب المحتمل | الحل |
|---|---|---|
| معادلة تعطي خطأ «column cannot be found» | العمود اختياري وغير موجود في ملفك (مثل `Product` أو `Discount` أو `Risk Level`) | احذف المعادلة والرسم المرتبطين بالعمود |
| `Sales LY` فارغة | جدول التواريخ غير معلَّم، أو لا توجد علاقة، أو بياناتك سنة واحدة فقط | راجع القسم 2؛ تحتاج بيانات لعامين على الأقل |
| `Total Sales` لا يطابق تقرير الجودة | فلتر/Slicer مفعّل، أو علاقة معكوسة | امسح كل الفلاتر وتأكد أن الاتجاه Single من Date إلى Sales |
| `Order Date` يظهر Date/Time | نوع العمود لم يُضبط | Transform Data ← غيّر النوع إلى Date |
| صفحة المخاطر فارغة | لم يُدرّب النموذج قبل التصدير | دربه في تاب النموذج ثم أعد التصدير |
| جدول Forecast فارغ | أقل من 9 شهور كاملة من البيانات | أضف بيانات أكثر |
| فشل Refresh | الملف مفتوح، أو تغيّر مساره أو اسمه | أغلقه وأعد المسار والاسم كما كانا |
| فشل Scheduled refresh في Service | ملف محلي بدون Gateway | ثبّت On-premises data gateway أو ضع الملف على OneDrive/SharePoint |

---

## English summary
1. **Get data ▸ Excel workbook ▸ `power_bi_data.xlsx`** ▸ tick all tables (not README) ▸ set `Order Date` to *Date* ▸ Close & Apply.
2. **New table** ▸ paste the `Date =` block from `measures.dax` ▸ *Mark as date table* ▸ relate `Date[Date]` → `Sales[Order Date]`.
3. Create the measures from `measures.dax` one by one; check that `[Total Sales]` equals "Total sales after cleaning" in the Quality table.
4. Build the three pages (Overview, Forecast, Risk) as listed above.
5. For new data: replace the Excel file (same name and path) and click **Refresh**; for scheduled refresh publish to Power BI Service (gateway needed for local files; Pro = 8 refreshes per day).
