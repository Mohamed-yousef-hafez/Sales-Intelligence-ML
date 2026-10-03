from .analytics import business_summary, category_profit, region_profit

class SalesAgent:
    """Simple rule-based agent that routes a question to the right analysis."""

    def __init__(self, df, rag):
        self.df = df
        self.rag = rag

    def run(self, question):
        q = question.lower().strip()

        if any(w in q for w in ["profit", "ربح", "خسارة", "loss"]):
            summary = business_summary(self.df)
            if any(w in q for w in ["category", "product", "فئة", "منتج"]):
                table = category_profit(self.df)
                return {
                    "tool": "category_profit",
                    "answer": f"Total profit: {summary['profit']:.2f}. "
                              f"Lowest-profit category: {table.index[-1]} ({table.iloc[-1]:.2f})."
                }
            if any(w in q for w in ["region", "منطقة"]):
                table = region_profit(self.df)
                return {
                    "tool": "region_profit",
                    "answer": f"Total profit: {summary['profit']:.2f}. "
                              f"Lowest-profit region: {table.index[-1]} ({table.iloc[-1]:.2f})."
                }
            return {
                "tool": "business_summary",
                "answer": f"Sales: {summary['sales']:.2f} | Profit: {summary['profit']:.2f} | "
                          f"Margin: {summary['margin']:.2f}% | Loss rate: {summary['loss_rate']:.2f}%."
            }

        return {
            "tool": "rag_retrieval",
            "answer": self.rag.answer(question)
        }
