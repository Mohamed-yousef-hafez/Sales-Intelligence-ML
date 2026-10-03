import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class SalesRAG:
    """Lightweight local RAG: retrieves business facts generated from the uploaded data."""

    def __init__(self, df):
        self.df = df
        self.documents = self._build_documents()
        self.vectorizer = TfidfVectorizer(stop_words="english")
        self.matrix = self.vectorizer.fit_transform(self.documents)

    def _build_documents(self):
        df = self.df
        docs = []

        total_sales = df["Sales"].sum()
        total_profit = df["Profit"].sum()
        margin = total_profit / total_sales * 100 if total_sales else 0
        docs.append(
            f"Overall sales are {total_sales:.2f}. Overall profit is {total_profit:.2f}. "
            f"Profit margin is {margin:.2f} percent."
        )

        if "Category" in df:
            for k, v in df.groupby("Category")["Profit"].sum().items():
                docs.append(f"Category {k} generated total profit of {v:.2f}.")

        if "Region" in df:
            for k, v in df.groupby("Region")["Profit"].sum().items():
                docs.append(f"Region {k} generated total profit of {v:.2f}.")

        avg_discount_profit = df.groupby("Discount")["Profit"].mean()
        for discount, profit in avg_discount_profit.items():
            docs.append(
                f"Average profit for discount {discount:.2f} is {profit:.2f}."
            )

        return docs

    def retrieve(self, question, k=3):
        query = self.vectorizer.transform([question])
        scores = cosine_similarity(query, self.matrix)[0]
        indexes = scores.argsort()[::-1][:k]
        return [(self.documents[i], float(scores[i])) for i in indexes]

    def answer(self, question):
        hits = self.retrieve(question)
        useful = [doc for doc, score in hits if score > 0]
        if not useful:
            return "I could not retrieve a reliable business fact from the uploaded data."
        return "Based on the uploaded data:\n- " + "\n- ".join(useful)
