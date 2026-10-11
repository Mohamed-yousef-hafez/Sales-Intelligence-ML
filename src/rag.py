import re

from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .analytics import group_table
from .i18n import DIMENSIONS, t
from .text_utils import normalize_text

ARABIC_STOP_WORDS = ["ما", "ماذا", "هي", "هو", "كم", "في", "من", "على", "عن", "الى", "إلى", "كيف", "هل", "هذا", "هذه", "ان", "أن"]
STOP_WORDS = set(ENGLISH_STOP_WORDS) | {normalize_text(word) for word in ARABIC_STOP_WORDS}

FACT_COLUMNS = ["Category", "Sub-Category", "Region", "Segment", "Ship Mode", "Product", "Customer"]
MAX_VALUES_PER_COLUMN = 200  # columns with more different values (many products) are answered by the agent directly


def analyze(text):
    """Split text into normalized words (Arabic or English) and remove stop words."""
    words = re.findall(r"\w\w+", normalize_text(text))
    return [word for word in words if word not in STOP_WORDS]


class SalesRAG:
    """Lightweight local RAG. It builds business facts from the uploaded data in Arabic AND English,
    finds the facts closest to the question (TF-IDF) and answers in the language of the question."""

    def __init__(self, df):
        self.df = df
        self.documents = self._build_documents()  # list of {"en": "...", "ar": "..."}
        texts = [doc["en"] + " " + doc["ar"] for doc in self.documents]
        self.vectorizer = TfidfVectorizer(analyzer=analyze)
        self.matrix = self.vectorizer.fit_transform(texts)

    def _both(self, key, **values):
        return {"en": t("en", key, **values), "ar": t("ar", key, **values)}

    def _build_documents(self):
        df = self.df
        docs = []

        total_sales = df["Sales"].sum()
        total_profit = df["Profit"].sum()
        margin = total_profit / total_sales * 100 if total_sales else 0
        docs.append(self._both("doc_overall", sales=f"{total_sales:,.2f}", profit=f"{total_profit:,.2f}", margin=f"{margin:.2f}"))

        for column in FACT_COLUMNS:
            if column not in df.columns or df[column].nunique() > MAX_VALUES_PER_COLUMN:
                continue
            for value, row in group_table(df, column).iterrows():
                docs.append({
                    lang: t(lang, "doc_entity", dim=DIMENSIONS[column][lang], name=value,
                            sales=f"{row['sales']:,.2f}", profit=f"{row['profit']:,.2f}",
                            margin=f"{row['margin']:.2f}", loss_rate=f"{row['loss_rate']:.2f}", orders=int(row["orders"]))
                    for lang in ("en", "ar")
                })

        if "Discount" in df.columns:
            discount_profit = df.groupby("Discount")["Profit"].mean()
            if len(discount_profit) <= 30:
                for discount, profit in discount_profit.items():
                    docs.append(self._both("doc_discount", discount=f"{discount:.0%}", value=f"{profit:,.2f}"))

        yearly = df.groupby("Order Year")[["Sales", "Profit"]].sum()
        for year, row in yearly.iterrows():
            docs.append(self._both("doc_year", year=int(year), sales=f"{row['Sales']:,.2f}", profit=f"{row['Profit']:,.2f}"))

        return docs

    def retrieve(self, question, k=3):
        query = self.vectorizer.transform([question])
        scores = cosine_similarity(query, self.matrix)[0]
        indexes = scores.argsort()[::-1][:k]
        return [(self.documents[i], float(scores[i])) for i in indexes]

    def answer(self, question, lang="en"):
        hits = self.retrieve(question)
        useful = [doc[lang] for doc, score in hits if score > 0]
        if not useful:
            return t(lang, "rag_none")
        return t(lang, "rag_header") + "\n- " + "\n- ".join(useful)
