# دليل الاستخدام السريع | Quick user guide

## بالعربية

### 1) تجهيز الملف
- ارفع ملف **Excel** (‏`.xlsx` أو `.xls`) أو **CSV**. يمكن أن تكون الأعمدة والقيم بالعربية أو الإنجليزية.
- لو لا تعرف الشكل المطلوب، اضغط **«حمّل قالب Excel»** من القائمة الجانبية، واملأه ببياناتك.
- **الأعمدة المطلوبة فقط:** تاريخ الطلب، المبيعات، والربح (أو التكلفة بدلاً من الربح).
- **أعمدة اختيارية** تضيف تحليلاً أكثر: الخصم، الكمية، الفئة، الفئة الفرعية، المنتج، العميل، المنطقة، الشريحة، طريقة الشحن، تاريخ الشحن.
- لا تقلق من الأخطاء الشائعة؛ البرنامج ينظّفها (راجع القسم التالي).

### 2) ماذا ينظّف البرنامج تلقائياً؟
عناوين التقرير فوق الجدول، صفوف الإجمالي، القيم المكررة، `N/A` و`-` و`غير متوفر`، اختلاف كتابة الأسماء (`furniture` / `Furniture`)،
الأرقام العربية، رموز العملة و`%`، الفاصلة العشرية، تواريخ بالعربية أو أرقام Excel، وقيم مستحيلة (مبيعات أو كمية ≤ 0، خصم فوق 100%).

### 3) قراءة النتائج
- **تقرير جودة البيانات:** يوضح كل ما تم تنظيفه. **قارن إجمالي المبيعات والربح بملفك الأصلي** قبل الاعتماد على النتائج.
- **لوحة الأعمال:** مؤشرات ورسوم، مع فلاتر للتاريخ والفئة والمنطقة.
- **النموذج:** اضغط «درّب النموذج» (يحتاج 30 صفاً على الأقل، منها 5 رابحة و5 خاسرة على الأقل). قارن دقته بـ«خط الأساس».
- **المساعد:** اسأل بالعربية أو الإنجليزية، مثل «ما هي أقل منطقة ربحاً؟» أو «كم ربح فئة الأثاث؟».
- يمكنك تحميل **البيانات بعد التنظيف** و**تقرير الجودة** كملفات CSV.

### 4) التوقعات وPower BI
- تاب **التوقعات:** يتوقع مبيعات أو ربح الشهور القادمة (1 إلى 6)، ويقول بصراحة هل التوقع **موثوق أو متوسط أو ضعيف** حسب أخطائه على الشهور الماضية في بياناتك. يحتاج 9 شهور كاملة على الأقل.
- في تاب **النموذج** اضغط «افحص موثوقية النموذج على بياناتي» قبل الاعتماد على توقعاته: دقة النموذج في بيانات شركة لا تضمن دقته في شركة أخرى.
- تاب **Power BI:** اضغط «جهّز الحزمة» ثم حمّل **ملف Excel واحد** (`power_bi_data.xlsx`) فيه كل الجداول، وافتحه من Power BI بـ Get data ▸ Excel workbook. الحزمة (ZIP) فيها أيضاً معادلات DAX و**`STEP_BY_STEP.md`**: دليل إعداد خطوة بخطوة (نحو ساعة أول مرة، ثم دقيقة لكل تحديث). للتحديث التلقائي ضع ملف المبيعات الجديد في `inbox` وشغّل `refresh_exports.py` (أو جدوله) وستجد النتائج في `exports`.

### 5) ملاحظات مهمة
- **المرتجعات** (مبيعات أو كمية سالبة) تُحذف، ويظهر عددها في التقرير.
- القيم المتطرفة **تبقى** وتُذكر في التقرير فقط للمراجعة.
- الحد الأقصى للملف 50 ميجابايت ومليون صف. في ملفات Excel متعددة الأوراق يختار البرنامج الورقة الأقرب لبيانات المبيعات.

## English

1. **Prepare the file:** upload Excel (`.xlsx`, `.xls`) or CSV, Arabic or English. Use **Download the Excel template** in the sidebar if unsure.
   Required: order date, sales, and profit (or cost). Optional: discount, quantity, category, sub-category, product, customer, region, segment, ship mode, ship date.
2. **Automatic cleaning:** report titles above the table, total rows, duplicates, `N/A`/`-` placeholders, spelling variants, Arabic digits,
   currency and `%`, decimal commas, Arabic month names and Excel date numbers, impossible values.
3. **Read the results:** compare the totals in the *Data Quality Report* with your original file first; then use the dashboard (with filters),
   train the model (needs 30+ rows with at least 5 profitable and 5 loss-making), and ask the assistant in Arabic or English.
   Download the cleaned data and the report as CSV.
4. **Notes:** returns (negative sales/quantity) are removed and counted in the report; extreme values are kept and only reported.
   Maximum file size: 50 MB / 1,000,000 rows.

## للمسؤول التقني | For IT
- تشغيل سريع: `run_windows.bat` أو `./run_linux_mac.sh`، أو `docker compose up --build`.
- كلمة مرور اختيارية: متغير البيئة `APP_PASSWORD`. السجلات في `logs/app.log`.
- للبيانات الحقيقية شغّل التطبيق داخل شبكة الشركة الخاصة، وضع أمامه HTTPS (reverse proxy) إذا فُتح خارج الشبكة.
