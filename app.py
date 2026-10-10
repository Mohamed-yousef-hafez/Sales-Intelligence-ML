from pathlib import Path
import sys

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

st.title("📊 Sales Intelligence — ML")
st.caption(
    "Sales analytics + profitability prediction + lightweight RAG + agent routing + monitoring"
)


@st.cache_data(show_spinner=False)
def load_demo_data(path):
    return pd.read_csv(path)


@st.cache_data(show_spinner=False)
def process_data(raw):
    """Support both clean_data versions: dataframe-only or (dataframe, report)."""
    result = clean_data(raw)
    if isinstance(result, tuple) and len(result) == 2:
        return result[0], result[1]
    report = getattr(result, "attrs", {}).get("quality_report")
    return result, report


def make_fallback_quality_report(raw, cleaned):
    """Basic report for compatibility if clean_data does not return a report."""
    return {
        "rows_before": len(raw),
        "columns_before": len(raw.columns),
        "duplicate_rows_removed": int(raw.duplicated().sum()),
        "rows_after_duplicates": len(raw.drop_duplicates()),
        "rows_missing_required_fields": None,
        "rows_after_cleaning": len(cleaned),
        "rows_removed_total": max(0, len(raw) - len(cleaned)),
        "missing_cells_before_cleaning": int(raw.isna().sum().sum()),
        "missing_cells_after_cleaning": int(cleaned.isna().sum().sum()),
        "sales_total": float(cleaned["Sales"].sum()) if "Sales" in cleaned else None,
        "profit_total": float(cleaned["Profit"].sum()) if "Profit" in cleaned else None,
        "date_min": cleaned["Order Date"].min() if "Order Date" in cleaned else None,
        "date_max": cleaned["Order Date"].max() if "Order Date" in cleaned else None,
    }


def show_quality_report(report):
    st.subheader("🔎 Data Quality Report")
    c1, c2, c3 = st.columns(3)
    c1.metric("Rows before cleaning", f"{report['rows_before']:,}")
    c2.metric("Rows after cleaning", f"{report['rows_after_cleaning']:,}")
    c3.metric("Rows removed", f"{report['rows_removed_total']:,}")

    details = [
        ("Columns in source file", report.get("columns_before")),
        ("Duplicate rows removed", report.get("duplicate_rows_removed")),
        ("Rows with invalid/missing required fields", report.get("rows_missing_required_fields")),
        ("Missing cells before cleaning", report.get("missing_cells_before_cleaning")),
        ("Missing cells after cleaning", report.get("missing_cells_after_cleaning")),
        ("Total sales after cleaning", report.get("sales_total")),
        ("Total profit after cleaning", report.get("profit_total")),
        ("Earliest order date", report.get("date_min")),
        ("Latest order date", report.get("date_max")),
    ]
    report_df = pd.DataFrame(details, columns=["Metric", "Value"])
    report_df["Value"] = report_df["Value"].map(
        lambda value: f"{value:,.2f}" if isinstance(value, float) else str(value)
    )
    st.dataframe(report_df, use_container_width=True, hide_index=True)
    st.caption(
        "A successful upload confirms that the file was read and processed. "
        "It does not by itself prove that the source values are business-correct. "
        "Compare totals with the original file."
    )


uploaded = st.file_uploader(
    "Upload your sales data (CSV or XLSX)",
    type=["csv", "xlsx"],
    help="The included demo dataset is data/sample_superstore.csv.",
)

if uploaded is None:
    default_path = Path(__file__).parent / "data" / "sample_superstore.csv"
    if not default_path.exists():
        st.warning("Upload a CSV/XLSX file to start.")
        st.stop()
    raw = load_demo_data(str(default_path))
    source_name = "Built-in demo dataset"
else:
    try:
        raw = load_uploaded_file(uploaded)
        source_name = uploaded.name
    except Exception as e:
        log_event("upload_error", str(e))
        st.error(f"Could not read the uploaded file: {e}")
        st.stop()

try:
    with Timer() as timer:
        df, quality_report = process_data(raw)
    if quality_report is None:
        quality_report = make_fallback_quality_report(raw, df)
    log_event(
        "data_processing_complete",
        f"source={source_name}, rows={len(df)}, seconds={timer.elapsed:.3f}",
    )
except Exception as e:
    log_event("pipeline_error", str(e))
    st.error(f"Could not process this dataset: {e}")
    st.stop()

if df.empty:
    st.error("No valid rows remain after cleaning. Check the uploaded file and its columns.")
    st.stop()

try:
    summary = business_summary(df)
except Exception as e:
    log_event("summary_error", str(e))
    st.error(f"Could not calculate business metrics: {e}")
    st.stop()

st.success(
    f"Loaded {len(df):,} rows from {source_name}. Processing time: {timer.elapsed:.2f}s"
)

with st.expander("🔎 Data Quality Report", expanded=False):
    show_quality_report(quality_report)

tabs = st.tabs(
    [
        "📈 Business Dashboard",
        "🤖 ML Model",
        "🧠 AI Assistant",
        "🔐 Security & Monitoring",
    ]
)

with tabs[0]:
    st.subheader("Business Overview")
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
        monthly = monthly.copy()
        monthly["Period"] = (
            monthly["Order Year"].astype(str)
            + "-"
            + monthly["Order Month"].astype(str).str.zfill(2)
        )
        st.subheader("Monthly Sales and Profit")
        st.line_chart(monthly.set_index("Period")[["Sales", "Profit"]])

    st.subheader("Data Preview")
    st.dataframe(df.head(20), use_container_width=True)

with tabs[1]:
    st.subheader("Profitability Prediction")

    if "model_bundle" not in st.session_state:
        st.info(
            "The ML model is trained only when you click the button. "
            "This keeps the dashboard fast."
        )
        if st.button("🚀 Train ML Model", type="primary"):
            try:
                with st.spinner("Training profitability model..."):
                    with Timer() as model_timer:
                        model_bundle = train_and_evaluate(df)
                st.session_state.model_bundle = model_bundle
                log_event(
                    "model_training_complete",
                    f"rows={len(df)}, seconds={model_timer.elapsed:.3f}",
                )
                st.rerun()
            except Exception as e:
                log_event("model_training_error", str(e))
                st.error(f"Could not train the model: {e}")
    else:
        model, features, metrics = st.session_state.model_bundle
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Accuracy", f"{metrics['accuracy']:.2%}")
        m2.metric("Precision", f"{metrics['precision']:.2%}")
        m3.metric("Recall", f"{metrics['recall']:.2%}")
        m4.metric("F1", f"{metrics['f1']:.2%}")
        m5.metric("ROC-AUC", f"{metrics['roc_auc']:.2%}")

        st.write("Target: `Profitable = 1` when Profit > 0, otherwise `0`.")
        cm = metrics["confusion_matrix"]
        st.subheader("Confusion Matrix")
        st.dataframe(
            pd.DataFrame(
                cm,
                index=["Actual Loss", "Actual Profit"],
                columns=["Predicted Loss", "Predicted Profit"],
            ),
            use_container_width=False,
        )

        st.subheader("Try a New Transaction")
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
                    row[feature] = st.number_input(
                        feature, value=float(defaults.get(feature, 0.0))
                    )
                elif feature in ["Quantity", "Ship Days", "Order Month", "Order Year"]:
                    row[feature] = st.number_input(
                        feature, value=int(defaults.get(feature, 0)), step=1
                    )
                else:
                    if feature not in df.columns:
                        st.error(f"Feature '{feature}' is missing from the cleaned data.")
                        st.stop()
                    options = sorted(df[feature].dropna().astype(str).unique().tolist())
                    if not options:
                        st.error(f"No available values for feature '{feature}'.")
                        st.stop()
                    default_value = str(defaults.get(feature, options[0]))
                    row[feature] = st.selectbox(
                        feature,
                        options,
                        index=options.index(default_value)
                        if default_value in options
                        else 0,
                    )

        if st.button("Predict Profitability", type="primary"):
            try:
                pred, probability = predict_one(model, row)
                label = "PROFITABLE" if pred else "LOSS / NOT PROFITABLE"
                if pred:
                    st.success(
                        f"Prediction: **{label}** — probability of profitability: **{probability:.2%}**"
                    )
                else:
                    st.warning(
                        f"Prediction: **{label}** — probability of profitability: **{probability:.2%}**"
                    )
                log_event(
                    "prediction", f"prediction={pred}, probability={probability:.4f}"
                )
            except Exception as e:
                log_event("prediction_error", str(e))
                st.error(f"Prediction failed: {e}")

with tabs[2]:
    st.subheader("Sales AI Assistant")
    st.write(
        "Lightweight local RAG + agent routing. No external LLM is required "
        "and company data stays inside the application."
    )

    @st.cache_resource(show_spinner=False)
    def build_assistant(dataframe):
        local_rag = SalesRAG(dataframe)
        return SalesAgent(dataframe, local_rag)

    try:
        agent = build_assistant(df)
        question = st.text_input(
            "Ask a sales question",
            placeholder="Example: Which region has the lowest profit?",
        )
        if st.button("Ask Assistant") and question.strip():
            try:
                with st.spinner("Analyzing..."):
                    result = agent.run(question)
                st.write(f"**Agent tool:** `{result['tool']}`")
                st.write(result["answer"])
                log_event("assistant_question", f"tool={result['tool']}")
            except Exception as e:
                log_event("assistant_error", str(e))
                st.error(f"Assistant failed: {e}")
    except Exception as e:
        log_event("assistant_initialization_error", str(e))
        st.error(f"Could not initialize the assistant: {e}")

with tabs[3]:
    st.subheader("Security")
    st.markdown(
        """
- Accepts only CSV/XLSX uploads.
- Upload size is limited to 10 MB when enforced by `src/security.py`.
- Required business columns are validated by the upload loader.
- No uploaded file is executed as code.
- No external LLM is required.
- Uploaded company data stays inside the running application process.
"""
    )
    st.subheader("Monitoring")
    st.markdown(
        """
- Data processing time is logged.
- Upload/pipeline errors are logged.
- Model training errors are logged.
- Prediction events are logged.
- Assistant questions and selected tools are logged.
- Logs are stored in `logs/app.log` when configured in `src/monitoring.py`.
"""
    )

st.divider()
st.caption(
    "Demo note: for real company data, deploy this application inside the company's "
    "private infrastructure/VPC rather than using a public demo server."
)
