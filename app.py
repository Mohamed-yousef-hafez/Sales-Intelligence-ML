import os
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

sys.path.append(str(Path(__file__).parent))

from src.security import load_uploaded_file
from src.data import clean_data
from src.model import train_and_evaluate, predict_one
from src.analytics import business_summary, category_profit, region_profit, monthly_profit
from src.rag import SalesRAG
from src.agent import SalesAgent
from src.monitoring import log_event, Timer

st.set_page_config(page_title="Sales Intelligence ML", page_icon="📊", layout="wide")

st.title("📊 Sales Intelligence — End-to-End ML")
st.caption("Sales analytics + profitability prediction + lightweight RAG + agent routing + monitoring")

uploaded = st.file_uploader(
    "Upload your sales data (CSV or XLSX)",
    type=["csv", "xlsx"],
    help="For the included demo, use data/sample_superstore.csv"
)

if uploaded is None:
    default_path = Path("data/sample_superstore.csv")
    if not default_path.exists():
        st.warning("Upload a CSV/XLSX file to start.")
        st.stop()
    raw = pd.read_csv(default_path)
    source_name = "Built-in demo dataset"
else:
    try:
        raw = load_uploaded_file(uploaded)
        source_name = uploaded.name
    except Exception as e:
        st.error(str(e))
        st.stop()

try:
    with Timer() as timer:
        df = clean_data(raw)
        model, features, metrics = train_and_evaluate(df)
    log_event("pipeline_complete", f"source={source_name}, rows={len(df)}, seconds={timer.elapsed:.3f}")
except Exception as e:
    log_event("pipeline_error", str(e))
    st.error(f"Could not process this dataset: {e}")
    st.stop()

summary = business_summary(df)
rag = SalesRAG(df)
agent = SalesAgent(df, rag)

st.success(f"Loaded {len(df):,} rows from {source_name}. Processing time: {timer.elapsed:.2f}s")

tabs = st.tabs(["📈 Business Dashboard", "🤖 ML Model", "🧠 AI Assistant", "🔐 Security & Monitoring"])

with tabs[0]:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Sales", f"{summary['sales']:,.0f}")
    c2.metric("Total Profit", f"{summary['profit']:,.0f}")
    c3.metric("Profit Margin", f"{summary['margin']:.2f}%")
    c4.metric("Loss Rate", f"{summary['loss_rate']:.2f}%")

    st.subheader("Profit by Category")
    st.bar_chart(category_profit(df))

    st.subheader("Profit by Region")
    st.bar_chart(region_profit(df))

    monthly = monthly_profit(df)
    if len(monthly):
        monthly["Period"] = monthly["Order Year"].astype(str) + "-" + monthly["Order Month"].astype(str).str.zfill(2)
        st.subheader("Monthly Sales and Profit")
        st.line_chart(monthly.set_index("Period")[["Sales", "Profit"]])

    st.subheader("Preview")
    st.dataframe(df.head(20), use_container_width=True)

with tabs[1]:
    st.subheader("Profitability Prediction")
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Accuracy", f"{metrics['accuracy']:.2%}")
    m2.metric("Precision", f"{metrics['precision']:.2%}")
    m3.metric("Recall", f"{metrics['recall']:.2%}")
    m4.metric("F1", f"{metrics['f1']:.2%}")
    m5.metric("ROC-AUC", f"{metrics['roc_auc']:.2%}")

    st.write("Target: Profitable = 1 when Profit > 0, otherwise 0.")
    st.write("Confusion Matrix:", metrics["confusion_matrix"])

    st.subheader("Try a new transaction")
    defaults = {
        "Sales": float(df["Sales"].median()),
        "Quantity": int(df["Quantity"].median()),
        "Discount": float(df["Discount"].median()),
        "Ship Days": int(df["Ship Days"].median()) if "Ship Days" in df else 4,
        "Order Month": 6,
        "Order Year": int(df["Order Year"].max()),
        "Ship Mode": df["Ship Mode"].mode().iloc[0] if "Ship Mode" in df else "Standard Class",
        "Segment": df["Segment"].mode().iloc[0] if "Segment" in df else "Consumer",
        "Region": df["Region"].mode().iloc[0] if "Region" in df else "West",
        "Category": df["Category"].mode().iloc[0],
        "Sub-Category": df["Sub-Category"].mode().iloc[0],
    }

    cols = st.columns(3)
    row = {}
    for i, feature in enumerate(features):
        with cols[i % 3]:
            if feature in ["Sales", "Discount"]:
                row[feature] = st.number_input(feature, value=float(defaults[feature]))
            elif feature == "Quantity" or feature in ["Ship Days", "Order Month", "Order Year"]:
                row[feature] = st.number_input(feature, value=int(defaults[feature]), step=1)
            else:
                options = sorted(df[feature].dropna().astype(str).unique().tolist())
                row[feature] = st.selectbox(feature, options, index=options.index(str(defaults[feature])) if str(defaults[feature]) in options else 0)

    if st.button("Predict Profitability"):
        pred, probability = predict_one(model, row)
        label = "PROFITABLE" if pred else "LOSS / NOT PROFITABLE"
        st.info(f"Prediction: **{label}** — probability of profitability: **{probability:.2%}**")
        log_event("prediction", f"prediction={pred}, probability={probability:.4f}")

with tabs[2]:
    st.subheader("Sales AI Assistant")
    st.write("This is a lightweight local RAG + agent layer. It does not send company data to an external LLM.")
    question = st.text_input(
        "Ask a sales question",
        placeholder="Example: Which region has the lowest profit?"
    )
    if st.button("Ask Assistant") and question.strip():
        result = agent.run(question)
        st.write(f"**Agent tool:** `{result['tool']}`")
        st.write(result["answer"])
        log_event("assistant_question", f"tool={result['tool']}")

with tabs[3]:
    st.subheader("Security")
    st.markdown("""
- Accepts only CSV/XLSX uploads.
- Upload size is limited to 10 MB.
- Required business columns are validated.
- No uploaded file is executed as code.
- No external LLM is required.
- Uploaded company data stays inside the running application process.
""")
    st.subheader("Monitoring")
    st.markdown("""
- Pipeline execution time is logged.
- Upload/pipeline errors are logged.
- Prediction events are logged.
- Assistant questions and selected tools are logged.
- Logs are stored in `logs/app.log`.
""")

st.divider()
st.caption("Demo note: for real company data, deploy this application inside the company's private infrastructure/VPC rather than using a public demo server.")
