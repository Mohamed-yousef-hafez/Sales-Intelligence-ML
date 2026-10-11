import hmac
import os
from pathlib import Path
import sys

import pandas as pd
import streamlit as st

sys.path.append(str(Path(__file__).parent))

from src.agent import SalesAgent
from src.analytics import business_summary, discount_profit, monthly_profit, profit_by
from src.data import clean_data
from src.export import clean_csv_bytes, report_csv_bytes, template_xlsx_bytes
from src.i18n import COLUMN_LABELS_AR, t
from src.model import feature_importance, predict_one, train_and_evaluate
from src.monitoring import Timer, log_event
from src.rag import SalesRAG
from src.security import load_uploaded_file, prepare_table

st.set_page_config(page_title="Sales Intelligence | ذكاء المبيعات", page_icon="📊", layout="wide")

# ---------------------------------------------------------------- language
choice = st.sidebar.radio("Language / اللغة", ["العربية", "English"], index=0, key="language")
lang = "ar" if choice == "العربية" else "en"


def T(key, **values):
    return t(lang, key, **values)


def label(column):
    """Column name in the language of the interface."""
    return COLUMN_LABELS_AR.get(column, column) if lang == "ar" else column


PLURALS = {
    "Product": {"en": "Products", "ar": "المنتجات"},
    "Customer": {"en": "Customers", "ar": "العملاء"},
}

if lang == "ar":  # right-to-left text for the Arabic interface
    st.markdown(
        """
        <style>
        h1, h2, h3, .stMarkdown, .stAlert, [data-testid="stMetric"],
        [data-testid="stCaptionContainer"], label { direction: rtl; text-align: right; }
        </style>
        """,
        unsafe_allow_html=True,
    )

st.title(T("app_title"))
st.caption(T("app_caption"))


# ---------------------------------------------------------------- optional password
def password_ok():
    """If the environment variable APP_PASSWORD is set, ask for it before showing any data."""
    expected = os.environ.get("APP_PASSWORD")
    if not expected or st.session_state.get("authenticated"):
        return True
    st.subheader(T("login_title"))
    typed = st.text_input(T("login_prompt"), type="password", key="login_password")
    if st.button(T("login_button")):
        if hmac.compare_digest(typed.encode("utf-8"), expected.encode("utf-8")):
            st.session_state["authenticated"] = True
            log_event("login", "success")
            st.rerun()
        log_event("login_failed", "wrong password")
        st.error(T("login_wrong"))
    return False


if not password_ok():
    st.stop()

demo_choice = st.sidebar.radio(
    T("demo_label"), ["en", "ar"], format_func=lambda key: T("demo_" + key), key="demo_choice"
)


# ---------------------------------------------------------------- helpers
@st.cache_data(show_spinner=False)
def load_demo_data(path):
    return prepare_table(pd.read_csv(path, encoding="utf-8-sig"))


@st.cache_data(show_spinner=False)
def process_data(raw):
    """Clean the data. Returns (cleaned_dataframe, quality_report)."""
    return clean_data(raw)


@st.cache_resource(show_spinner=False)
def build_assistant(dataframe):
    return SalesAgent(dataframe, SalesRAG(dataframe))


@st.cache_data(show_spinner=False)
def cleaned_csv(dataframe):
    return clean_csv_bytes(dataframe)


@st.cache_data(show_spinner=False)
def template_file(language):
    return template_xlsx_bytes(language)


def format_value(value):
    if isinstance(value, bool):
        return T("yes") if value else T("no")
    if isinstance(value, float):
        return f"{value:,.2f}"
    if isinstance(value, list):
        return ", ".join(label(item) for item in value) if value else "—"
    return str(value)


def report_table(report):
    details = [
        (T("dq_before"), report["rows_before"]),
        (T("dq_after"), report["rows_after_cleaning"]),
        (T("dq_removed"), report["rows_removed_total"]),
        (T("dq_columns"), report["columns_before"]),
        (T("dq_placeholders"), report["placeholders_converted"]),
        (T("dq_summary_rows"), report["summary_rows_removed"]),
        (T("dq_variants"), report["spelling_variants_unified"]),
        (T("dq_duplicates"), report["duplicate_rows_removed"]),
        (T("dq_invalid"), report["rows_missing_required_fields"]),
        (T("dq_impossible"), report["rows_impossible_values"]),
        (T("dq_filled"), report["categories_filled_unknown"]),
        (T("dq_extreme"), report["possible_extreme_values_kept"]),
        (T("dq_profit_from_cost"), report["profit_calculated_from_cost"]),
        (T("dq_missing_optional"), report["optional_columns_missing"]),
        (T("dq_missing_before"), report["missing_cells_before_cleaning"]),
        (T("dq_missing_after"), report["missing_cells_after_cleaning"]),
        (T("dq_sales"), report["sales_total"]),
        (T("dq_profit"), report["profit_total"]),
        (T("dq_discount"), report["discount_converted_from_percent"]),
        (T("dq_date_order"), T("date_order_" + report["date_order"])),
        (T("dq_date_min"), report["date_min"]),
        (T("dq_date_max"), report["date_max"]),
    ]
    return pd.DataFrame(
        [(name, format_value(value)) for name, value in details],
        columns=[T("dq_metric"), T("dq_value")],
    )


def show_quality_report(report):
    st.subheader(T("quality_title"))
    c1, c2, c3 = st.columns(3)
    c1.metric(T("dq_before"), f"{report['rows_before']:,}")
    c2.metric(T("dq_after"), f"{report['rows_after_cleaning']:,}")
    c3.metric(T("dq_removed"), f"{report['rows_removed_total']:,}")

    table = report_table(report)
    st.dataframe(table, width="stretch", hide_index=True)
    st.caption(T("dq_note"))

    d1, d2 = st.columns(2)
    d1.download_button(T("download_clean"), cleaned_csv(df), file_name="cleaned_sales.csv", mime="text/csv")
    d2.download_button(T("download_report"), report_csv_bytes(table), file_name="quality_report.csv", mime="text/csv")
    st.markdown(f"**{T('cleaning_steps_title')}**\n\n{T('cleaning_steps')}")


def default_for(feature):
    """Starting value of an input of the 'try a new transaction' form."""
    if feature in ("Sales", "Discount"):
        return float(df[feature].median())
    if feature == "Quantity":
        return int(df["Quantity"].median())
    if feature == "Ship Days":
        return int(df["Ship Days"].median()) if df["Ship Days"].notna().any() else 4
    if feature == "Order Month":
        return 6
    return int(df["Order Year"].max())  # Order Year


# ---------------------------------------------------------------- load data
st.sidebar.download_button(
    T("download_template"), template_file(lang), file_name=f"sales_template_{lang}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)

uploaded = st.file_uploader(
    T("uploader"), type=["xlsx", "xlsm", "xls", "csv", "tsv", "txt"], help=T("uploader_help")
)

if uploaded is None:
    demo_files = {"en": "sample_superstore.csv", "ar": "sample_arabic_sales.csv"}
    default_path = Path(__file__).parent / "data" / demo_files[demo_choice]
    if not default_path.exists():
        st.warning(T("uploader"))
        st.stop()
    raw = load_demo_data(str(default_path))
    source_name = f"{T('demo_name')} — {T('demo_' + demo_choice)}"
    source_id = f"demo-{demo_choice}"  # same in both interface languages
else:
    try:
        raw = load_uploaded_file(uploaded)
        source_name = uploaded.name
        source_id = uploaded.name
    except Exception as e:
        log_event("upload_error", str(e))
        st.error(T("upload_error", error=e))
        st.stop()

try:
    with Timer() as timer:
        df, quality_report = process_data(raw)
    log_event("data_processing_complete", f"source={source_name}, rows={len(df)}, seconds={timer.elapsed:.3f}")
except Exception as e:
    log_event("pipeline_error", str(e))
    st.error(T("process_error", error=e))
    st.stop()

if df.empty:
    st.error(T("no_rows"))
    st.stop()

st.success(T("loaded", rows=f"{len(df):,}", source=source_name, seconds=f"{timer.elapsed:.2f}"))

with st.expander(T("quality_title"), expanded=True):
    show_quality_report(quality_report)

# A model trained on one dataset must not be shown for another uploaded file.
data_key = f"{source_id}|{len(df)}|{df['Sales'].sum():.2f}|{df['Profit'].sum():.2f}"
if st.session_state.get("data_key") != data_key:
    st.session_state.pop("model_bundle", None)
    st.session_state["data_key"] = data_key


def apply_filters(frame):
    """Date range and Category/Region/Segment filters. They change the dashboard only."""
    view = frame
    with st.expander(T("filters")):
        low, high = frame["Order Date"].min().date(), frame["Order Date"].max().date()
        picked = st.date_input(T("filter_dates"), value=(low, high), min_value=low, max_value=high, key=f"dates_{data_key}")
        if isinstance(picked, tuple) and len(picked) == 2:
            dates = view["Order Date"].dt.date
            view = view[(dates >= picked[0]) & (dates <= picked[1])]
        for column in ["Category", "Region", "Segment"]:
            if column in frame.columns:
                options = sorted(frame[column].astype(str).unique())
                chosen = st.multiselect(label(column), options, key=f"filter_{column}_{data_key}")
                if chosen:
                    view = view[view[column].astype(str).isin(chosen)]
    return view


tabs = st.tabs([T("tab_dashboard"), T("tab_model"), T("tab_assistant"), T("tab_security")])

# ---------------------------------------------------------------- dashboard
with tabs[0]:
    view = apply_filters(df)
    if view.empty:
        st.warning(T("filter_empty"))
    else:
        summary = business_summary(view)
        st.subheader(T("overview"))
        c1, c2, c3, c4 = st.columns(4)
        c1.metric(T("m_sales"), f"{summary['sales']:,.0f}")
        c2.metric(T("m_profit"), f"{summary['profit']:,.0f}")
        c3.metric(T("m_margin"), f"{summary['margin']:.2f}%")
        c4.metric(T("m_loss"), f"{summary['loss_rate']:.2f}%")

        for column in ["Category", "Sub-Category", "Region", "Segment", "Ship Mode"]:
            if column in view.columns and view[column].nunique() > 1:
                st.subheader(T("chart_by", dim=label(column)))
                st.bar_chart(profit_by(view, column))

        for column in ["Product", "Customer"]:  # many values: show the best and the worst ten
            if column in view.columns and view[column].nunique() > 1:
                ranking = profit_by(view, column).rename(label("Profit"))
                name = PLURALS[column][lang]
                left, right = st.columns(2)
                left.subheader(T("top10", dim=name))
                left.dataframe(ranking.head(10), width="stretch")
                right.subheader(T("bottom10", dim=name))
                right.dataframe(ranking.tail(10)[::-1], width="stretch")

        if "Discount" in view.columns and view["Discount"].nunique() > 1:
            st.subheader(T("chart_discount"))
            st.line_chart(discount_profit(view).set_index("Discount")["Profit"])

        monthly = monthly_profit(view)
        if len(monthly):
            monthly = monthly.copy()
            monthly["Period"] = monthly["Order Year"].astype(str) + "-" + monthly["Order Month"].astype(str).str.zfill(2)
            st.subheader(T("chart_monthly"))
            st.line_chart(monthly.set_index("Period")[["Sales", "Profit"]])

        st.subheader(T("preview"))
        preview = view.head(20)
        if lang == "ar":
            preview = preview.rename(columns=COLUMN_LABELS_AR)
        st.dataframe(preview, width="stretch")

# ---------------------------------------------------------------- ML model
with tabs[1]:
    st.subheader(T("predict_title"))

    if "model_bundle" not in st.session_state:
        st.info(T("train_info"))
        if st.button(T("train_button"), type="primary"):
            try:
                with st.spinner(T("training")):
                    with Timer() as model_timer:
                        model_bundle = train_and_evaluate(df)
                st.session_state.model_bundle = model_bundle
                log_event("model_training_complete", f"rows={len(df)}, seconds={model_timer.elapsed:.3f}")
                st.rerun()
            except Exception as e:
                log_event("model_training_error", str(e))
                st.error(T("train_error", error=e))
    else:
        model, features, metrics = st.session_state.model_bundle
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric(T("accuracy"), f"{metrics['accuracy']:.2%}")
        m2.metric(T("precision"), f"{metrics['precision']:.2%}")
        m3.metric(T("recall"), f"{metrics['recall']:.2%}")
        m4.metric(T("f1"), f"{metrics['f1']:.2%}")
        m5.metric(T("roc_auc"), f"{metrics['roc_auc']:.2%}")

        st.caption(
            T(
                "baseline_note",
                baseline=f"{metrics['baseline_accuracy']:.1%}",
                test=f"{metrics['test_size']:,}",
                train=f"{metrics['train_size']:,}",
                split=T("split_" + metrics["split_strategy"]),
            )
        )
        st.write(T("target_note"))

        st.subheader(T("confusion"))
        st.dataframe(
            pd.DataFrame(
                metrics["confusion_matrix"],
                index=[T("actual_loss"), T("actual_profit")],
                columns=[T("pred_loss"), T("pred_profit")],
            ),
            width="content",
        )

        st.subheader(T("importance_title"))
        importance = feature_importance(model)
        importance.index = [label(column) for column in importance.index]
        st.bar_chart(importance)

        st.subheader(T("try_title"))
        cols = st.columns(3)
        row = {}
        for i, feature in enumerate(features):
            with cols[i % 3]:
                if feature in ["Sales", "Discount"]:
                    row[feature] = st.number_input(label(feature), value=default_for(feature), key=f"in_{feature}")
                elif feature in ["Quantity", "Ship Days", "Order Month", "Order Year"]:
                    row[feature] = st.number_input(label(feature), value=default_for(feature), step=1, key=f"in_{feature}")
                else:
                    options = sorted(df[feature].dropna().astype(str).unique().tolist())
                    most_common = str(df[feature].mode().iloc[0])
                    row[feature] = st.selectbox(
                        label(feature), options,
                        index=options.index(most_common) if most_common in options else 0,
                        key=f"in_{feature}",
                    )

        if st.button(T("predict_button"), type="primary"):
            try:
                pred, probability = predict_one(model, row)
                text = T("pred_result", label=T("pred_yes") if pred else T("pred_no"), probability=f"{probability:.2%}")
                st.success(text) if pred else st.warning(text)
                log_event("prediction", f"prediction={pred}, probability={probability:.4f}")
            except Exception as e:
                log_event("prediction_error", str(e))
                st.error(T("pred_failed", error=e))

# ---------------------------------------------------------------- assistant
with tabs[2]:
    st.subheader(T("assistant_title"))
    st.write(T("assistant_desc"))
    st.markdown(f"**{T('examples_title')}**\n\n{T('examples')}")

    try:
        agent = build_assistant(df)
        question = st.text_input(T("question_label"), placeholder=T("question_placeholder"))
        if st.button(T("ask_button")) and question.strip():
            try:
                with st.spinner(T("analyzing")):
                    result = agent.run(question)
                st.write(f"**{T('agent_tool')}:** `{T('tool_' + result['tool'])}`")
                st.write(result["answer"])
                log_event("assistant_question", f"tool={result['tool']}, language={result['lang']}")
            except Exception as e:
                log_event("assistant_error", str(e))
                st.error(T("assistant_failed", error=e))
    except Exception as e:
        log_event("assistant_initialization_error", str(e))
        st.error(T("assistant_init_failed", error=e))

# ---------------------------------------------------------------- security
with tabs[3]:
    st.subheader(T("security_title"))
    st.markdown(T("security_points"))
    st.subheader(T("monitoring_title"))
    st.markdown(T("monitoring_points"))

st.divider()
st.caption(T("deploy_note"))
