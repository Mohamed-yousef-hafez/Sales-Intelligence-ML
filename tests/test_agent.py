import pandas as pd
from src.agent import SalesAgent
from src.data import clean_data
from src.rag import SalesRAG


def make_agent(arabic=False):
    names = {
        "Region": ["الغرب", "الشرق", "الجنوب", "الوسط"] if arabic else ["West", "East", "South", "Central"],
        "Category": ["تقنية", "تقنية", "أثاث", "أثاث"] if arabic else ["Tech", "Tech", "Furniture", "Furniture"],
    }
    df = pd.DataFrame({
        "Sales": [100, 100, 100, 100],
        "Profit": [50, 10, -20, -40],
        "Discount": [0.0, 0.1, 0.4, 0.5],
        "Quantity": [1, 1, 1, 1],
        "Order Date": ["2024-01-01"] * 4,
        "Region": names["Region"],
        "Category": names["Category"],
    })
    df, _ = clean_data(df)
    return SalesAgent(df, SalesRAG(df))


def test_highest_and_lowest_are_different():
    agent = make_agent()
    high = agent.run("Which region has the highest profit?")["answer"]
    low = agent.run("Which region has the lowest profit?")["answer"]
    assert "West" in high and "Central" not in high
    assert "Central" in low and "West" not in low


def test_arabic_question_gets_arabic_answer():
    agent = make_agent()
    result = agent.run("ما هي المنطقة الأعلى أرباحا؟")
    assert result["tool"] == "ranking" and result["lang"] == "ar"
    assert "West" in result["answer"] and "أعلى منطقة" in result["answer"]


def test_arabic_data_values_are_understood():
    agent = make_agent(arabic=True)
    result = agent.run("كم ربح الأثاث؟")  # "الأثاث" = ال + أثاث
    assert result["tool"] == "entity_summary"
    assert "أثاث" in result["answer"] and "-60.00" in result["answer"]
    assert "الوسط" in agent.run("ما هي أقل منطقة ربحا؟")["answer"]


def test_ranking_by_sales_when_asked_about_sales():
    answer = make_agent().run("Which category has the lowest sales?")["answer"]
    assert "Total sales" in answer


def test_discount_question_uses_discount_tool_in_both_languages():
    agent = make_agent()
    en = agent.run("How does discount affect profit?")
    ar = agent.run("كيف يؤثر الخصم على الربح؟")
    assert en["tool"] == ar["tool"] == "discount_profit"
    assert "40%" in en["answer"] and "40%" in ar["answer"]
    assert "negative" in en["answer"] and "سالباً" in ar["answer"]


def test_unknown_question_fallback_language():
    assert "matching fact" in make_agent().run("hello")["answer"]
    assert "لم أجد" in make_agent().run("مرحبا")["answer"]
