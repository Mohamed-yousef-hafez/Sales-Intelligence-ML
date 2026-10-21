from .analytics import business_summary, discount_profit, group_summary, profit_by
from .forecast import forecast_monthly
from .i18n import DIMENSIONS, METRICS, t
from .text_utils import PREFIXES, has_arabic, normalize_text, words_of


def W(*words):
    """Normalize keywords. A word ending with * matches any word that starts with it."""
    return [normalize_text(word) for word in words]


# Keywords in English and Arabic.
DISCOUNT_WORDS = W("discount*", "خصم*", "خصوم*", "تخفيض*")
PROFIT_WORDS = W("profit*", "loss", "losses", "lose*", "ربح*", "ارباح*", "خسار*", "خسائر*")
SALES_WORDS = W("sales", "revenue*", "margin*", "مبيع*", "ايراد*", "هامش*")
SALES_ONLY_WORDS = W("sales", "revenue*", "مبيع*", "ايراد*")
FORECAST_WORDS = W("forecast*", "next month", "next months", "توقع*", "تنبؤ*", "الشهر القادم", "الشهر الجاي", "الشهر المقبل", "الشهور القادمة")
HIGHEST_WORDS = W("highest", "most", "best", "top", "max", "maximum", "اعلي*", "اكثر*", "افضل*", "اكبر*", "اعظم*")
LOWEST_WORDS = W("lowest", "least", "worst", "min", "minimum", "اقل", "اسوا", "ادني", "اصغر", "اضعف")

# (column, words that mean this column). Sub-Category must come before Category.
DIMENSION_WORDS = [
    ("Sub-Category", W("sub-category", "sub-categories", "subcategory", "subcategories", "sub category", "فرعي*")),
    ("Product", W("product*", "item*", "منتج*", "صنف*", "اصناف")),
    ("Category", W("category", "categories", "product*", "فئ*", "منتج*", "تصنيف*")),
    ("Region", W("region*", "area*", "منطق*", "مناطق*", "اقليم*", "محافظ*")),
    ("Customer", W("customer*", "client*", "عميل*", "عملاء", "زبون*", "زبائن")),
    ("Segment", W("segment*", "customer*", "شريح*", "شرائح*", "قطاع*", "عملاء")),
]

# Columns whose values (for example "Furniture" or "أثاث") can be recognised inside a question.
ENTITY_COLUMNS = ["Category", "Sub-Category", "Region", "Segment", "Ship Mode", "Product", "Customer"]


def has_any(question, keywords):
    """True if one keyword appears as a whole word in the question (Arabic prefixes like ال are allowed)."""
    words = words_of(question)
    for keyword in keywords:
        if " " in keyword:
            if keyword in normalize_text(question):
                return True
            continue
        stem = keyword.rstrip("*")
        starts_with = keyword.endswith("*")
        for word in words:
            candidates = [word] + [word[len(p):] for p in PREFIXES if word.startswith(p)]
            if any(c == stem or (starts_with and c.startswith(stem)) for c in candidates):
                return True
    return False


class SalesAgent:
    """Rule-based agent for Arabic and English questions. It picks the right analysis and
    answers in the language of the question."""

    def __init__(self, df, rag):
        self.df = df
        self.rag = rag
        self.entities = self._collect_entities()

    def _collect_entities(self):
        entities = []
        for column in ENTITY_COLUMNS:
            if column in self.df.columns:
                for value in self.df[column].dropna().astype(str).unique():
                    entities.append((" ".join(words_of(value)), column, value))
        return sorted(entities, key=lambda item: len(item[0]), reverse=True)  # longest names first

    def run(self, question):
        lang = "ar" if has_arabic(question) else "en"

        if has_any(question, DISCOUNT_WORDS):
            answer = self._discount_answer(lang) if "Discount" in self.df.columns else t(lang, "ans_no_discount")
            return {"tool": "discount_profit", "lang": lang, "answer": answer}

        if has_any(question, FORECAST_WORDS):
            return {"tool": "forecast", "lang": lang, "answer": self._forecast_answer(question, lang)}

        found = self._find_entities(question)
        if found:
            return {"tool": "entity_summary", "lang": lang, "answer": self._entity_answer(found, lang)}

        column = self._find_dimension(question)
        if column:
            return {"tool": "ranking", "lang": lang, "answer": self._ranking_answer(question, column, lang)}

        if has_any(question, PROFIT_WORDS + SALES_WORDS):
            return {"tool": "business_summary", "lang": lang, "answer": self._summary_answer(lang)}

        return {"tool": "rag_retrieval", "lang": lang, "answer": self.rag.answer(question, lang)}

    # ---------- finding what the question is about ----------
    def _find_entities(self, question):
        """Return [(column, value)] for names from the data that appear in the question."""
        padded = " " + " ".join(words_of(question)) + " "
        found = []
        for name, column, value in self.entities:
            singular = name[:-1] if name.endswith("s") and len(name) > 3 else name  # chairs -> chair
            for candidate in {name, singular}:
                if any(f" {prefix}{candidate} " in padded for prefix in [""] + PREFIXES):
                    found.append((column, value))
                    break
        return found[:3]

    def _find_dimension(self, question):
        for column, words in DIMENSION_WORDS:
            if column in self.df.columns and has_any(question, words):
                return column
        return None

    # ---------- answers ----------
    def _forecast_answer(self, question, lang):
        asks_profit = has_any(question, PROFIT_WORDS) and not has_any(question, SALES_ONLY_WORDS)
        metric = "Profit" if asks_profit else "Sales"
        result = forecast_monthly(self.df, metric, 1)
        if result["status"] != "ok":
            return t(lang, "fc_not_enough", needed=result["needed"], found=result["n_months"])
        month, row = result["forecast"].index[0], result["forecast"].iloc[0]
        verdict = t(lang, "fc_verdict_" + result["verdict"], wape=f"{result['wape']:.0%}", gain=f"{result['gain'] * 100:.1f}")
        answer = t(lang, "ans_forecast", month=str(month), metric=METRICS[metric][lang], value=f"{row['forecast']:,.0f}",
                   low=f"{row['lower']:,.0f}", high=f"{row['upper']:,.0f}", verdict=verdict)
        if result["method"] == "naive":
            answer += " " + t(lang, "fc_naive_note")
        return answer

    def _summary_answer(self, lang):
        s = business_summary(self.df)
        return t(lang, "ans_summary", sales=f"{s['sales']:,.2f}", profit=f"{s['profit']:,.2f}",
                 margin=f"{s['margin']:.2f}", loss_rate=f"{s['loss_rate']:.2f}")

    def _entity_answer(self, found, lang):
        lines = []
        for column, value in found:
            s = group_summary(self.df, column, value)
            lines.append(t(lang, "ans_entity", name=value, dim=DIMENSIONS[column][lang],
                           sales=f"{s['sales']:,.2f}", profit=f"{s['profit']:,.2f}",
                           margin=f"{s['margin']:.2f}", loss_rate=f"{s['loss_rate']:.2f}", orders=s["orders"]))
        return "\n\n".join(lines)

    def _ranking_answer(self, question, column, lang):
        # Rank by sales only when the question asks about sales and not about profit.
        asks_sales = has_any(question, SALES_ONLY_WORDS) and not has_any(question, PROFIT_WORDS)
        metric_key = "Sales" if asks_sales else "Profit"
        table = profit_by(self.df, column, metric_key)  # sorted from highest to lowest

        names = METRICS[metric_key]
        metric_in_sentence = names["ar_adv"] if lang == "ar" else names["en"]
        dim = DIMENSIONS[column][lang]
        total = t(lang, "ans_total", metric=names[lang], total=f"{table.sum():,.2f}")
        show = 1 if len(table) <= 6 else 3  # many items (products, customers): show the top/bottom three
        top_items = ", ".join(f"{name} ({value:,.2f})" for name, value in table.head(show).items())
        bottom_items = ", ".join(f"{name} ({value:,.2f})" for name, value in table.tail(show)[::-1].items())
        best = t(lang, "ans_best", metric=metric_in_sentence, dim=dim, items=top_items)
        worst = t(lang, "ans_worst", metric=metric_in_sentence, dim=dim, items=bottom_items)

        wants_best = has_any(question, HIGHEST_WORDS)
        wants_worst = has_any(question, LOWEST_WORDS)
        if wants_best and not wants_worst:
            details = best
        elif wants_worst and not wants_best:
            details = worst
        else:
            details = best + " " + worst
        return f"{total} {details}"

    def _discount_answer(self, lang):
        table = discount_profit(self.df).sort_values("Discount")
        no_discount = table[table["Discount"] == 0]
        losing = table[table["Profit"] < 0]

        parts = []
        if not no_discount.empty:
            parts.append(t(lang, "ans_discount_none", value=f"{no_discount['Profit'].iloc[0]:,.2f}"))
        if losing.empty:
            parts.append(t(lang, "ans_discount_positive"))
        else:
            first = losing.iloc[0]
            parts.append(t(lang, "ans_discount_negative", discount=f"{first['Discount']:.0%}", value=f"{first['Profit']:,.2f}"))
        return " ".join(parts)
