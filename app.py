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
from src.export import clean_csv_bytes, quality_report_frame, report_csv_bytes, template_xlsx_bytes
from src.forecast import forecast_monthly, normalize_metric
from src.i18n import COLUMN_LABELS_AR, t
from src.model_export import joblib_bytes, model_package_zip
from src.model import (
    cross_validate_time, feature_importance, predict_one, reliability_verdict, score_dataframe, train_and_evaluate,
)
from src.monitoring import Timer, log_event
from src.powerbi import DASHBOARD_ZIP, EXCEL_ROW_LIMIT, WORKBOOK_NAME, build_powerbi_files, zip_bytes
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


# ---------------------------------------------------------------- settings: environment variable or Streamlit Secrets
def setting(name):
    """A setting from an environment variable (own server, Docker) or from Streamlit Secrets (Streamlit Community Cloud)."""
    value = os.environ.get(name)
    if value:
        return value
    try:
        return st.secrets.get(name)
    except Exception:   # no secrets file: normal on a laptop
        return None


# ---------------------------------------------------------------- optional password
def password_ok():
    """If APP_PASSWORD is set, ask for it before showing any data."""
    expected = setting("APP_PASSWORD")
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
# Streamlit returns the option itself. If it ever returns the text shown on the screen, convert it back.
demo_choice = {t(l, "demo_" + k): k for l in ("en", "ar") for k in ("en", "ar")}.get(demo_choice, demo_choice)
if demo_choice not in ("en", "ar"):
    demo_choice = "en"


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


def show_quality_report(report):
    st.subheader(T("quality_title"))
    c1, c2, c3 = st.columns(3)
    c1.metric(T("dq_before"), f"{report['rows_before']:,}")
    c2.metric(T("dq_after"), f"{report['rows_after_cleaning']:,}")
    c3.metric(T("dq_removed"), f"{report['rows_removed_total']:,}")

    table = quality_report_frame(report, lang)
    st.dataframe(table, width="stretch", hide_index=True)
    st.caption(T("dq_note"))

    d1, d2 = st.columns(2)
    d1.download_button(T("download_clean"), cleaned_csv(df), file_name="cleaned_sales.csv", mime="text/csv")
    d2.download_button(T("download_report"), report_csv_bytes(table), file_name="quality_report.csv", mime="text/csv")
    st.markdown(f"**{T('cleaning_steps_title')}**\n\n{T('cleaning_steps')}")


def shorten(series, limit=38):
    """Show long names (products) shortened, so the value column is visible without scrolling."""
    series = series.copy()
    series.index = [name if len(str(name)) <= limit else str(name)[: limit - 1] + "…" for name in series.index]
    return series


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

DEMO_ONLY = str(setting("APP_DEMO_ONLY") or "").lower() in ("1", "true", "yes")   # public link: demo data only
if DEMO_ONLY:
    uploaded = None
    st.info(T("demo_only_note"))
else:
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

if quality_report["cleaning_needed"]:
    st.info(T("clean_fixed", n=f"{quality_report['cleaning_changes']:,}"))
else:
    st.success(T("clean_ok"))

with st.expander(T("quality_title"), expanded=True):
    show_quality_report(quality_report)

# A model trained on one dataset must not be shown for another uploaded file.
data_key = f"{source_id}|{len(df)}|{df['Sales'].sum():.2f}|{df['Profit'].sum():.2f}"
if st.session_state.get("data_key") != data_key:
    for old_key in ["model_bundle", "reliability", "scored_csv", "model_download", "pbi_pack", "pbi_pack_key"]:
        st.session_state.pop(old_key, None)
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


tabs = st.tabs([
    T("tab_dashboard"), T("tab_model"), T("tab_forecast"), T("tab_assistant"), T("tab_powerbi"), T("tab_security"),
])
tab_dashboard, tab_model, tab_forecast, tab_assistant, tab_powerbi, tab_security = tabs

# ---------------------------------------------------------------- dashboard
with tab_dashboard:
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
                left.dataframe(shorten(ranking.head(10)), width="stretch")
                right.subheader(T("bottom10", dim=name))
                right.dataframe(shorten(ranking.tail(10)[::-1]), width="stretch")

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
        preview = view.head(20).copy()
        for date_column in ["Order Date", "Ship Date"]:
            if date_column in preview.columns:
                preview[date_column] = preview[date_column].dt.strftime("%Y-%m-%d")
        if lang == "ar":
            preview = preview.rename(columns=COLUMN_LABELS_AR)
        st.dataframe(preview, width="stretch")

# ---------------------------------------------------------------- ML model
with tab_model:
    st.subheader(T("predict_title"))

    if "model_bundle" not in st.session_state:
        st.info(T("train_info"))
        if st.button(T("train_button"), type="primary"):
            try:
                with st.spinner(T("training")):
                    with Timer() as model_timer:
                        model_bundle = train_and_evaluate(df)
                st.session_state.model_bundle = model_bundle
                st.session_state["model_download"] = (joblib_bytes(model_bundle, df, source_name), model_package_zip(model_bundle, df, source_name))
                st.session_state["scored_csv"] = clean_csv_bytes(score_dataframe(df=df, model=model_bundle[0], train_index=model_bundle[2]["train_index"]))
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

        st.subheader(T("rel_title"))
        st.write(T("rel_desc"))
        if "reliability" not in st.session_state:
            if st.button(T("rel_button")):
                try:
                    with st.spinner(T("rel_running")):
                        folds = cross_validate_time(df)
                    st.session_state["reliability"] = (folds, reliability_verdict(folds))
                    log_event("reliability_check", f"periods={len(folds)}")
                    st.rerun()
                except Exception as e:
                    log_event("reliability_error", str(e))
                    st.error(T("train_error", error=e))
        else:
            folds, verdict = st.session_state["reliability"]
            if verdict["verdict"] == "not_enough":
                st.warning(T("rel_not_enough"))
            else:
                table = pd.DataFrame({
                    T("rel_period"): folds["start"].dt.strftime("%Y-%m-%d") + " → " + folds["end"].dt.strftime("%Y-%m-%d"),
                    T("rel_train"): folds["train_rows"],
                    T("rel_test"): folds["test_rows"],
                    T("accuracy"): (folds["accuracy"] * 100).round(1).astype(str) + "%",
                    T("rel_baseline"): (folds["baseline"] * 100).round(1).astype(str) + "%",
                    T("f1"): folds["f1"].round(3),
                    T("roc_auc"): folds["roc_auc"].round(3),
                })
                st.dataframe(table, hide_index=True, width="stretch")
                st.markdown(T("rel_summary", accuracy=f"{verdict['accuracy']:.1%}", baseline=f"{verdict['baseline']:.1%}",
                              gain=f"{verdict['gain'] * 100:.1f}", auc=f"{verdict['roc_auc']:.3f}", spread=f"{verdict['spread'] * 100:.1f}"))
                message = T("rel_verdict_" + verdict["verdict"])
                {"strong": st.success, "moderate": st.info, "weak": st.warning}[verdict["verdict"]](message)
            st.caption(T("rel_note"))

        if "scored_csv" in st.session_state:
            st.download_button(T("download_scored"), st.session_state["scored_csv"], file_name="sales_scored.csv", mime="text/csv")
            st.caption(T("scored_note"))
        if "model_download" in st.session_state:
            joblib_file, package_file = st.session_state["model_download"]
            m1, m2 = st.columns(2)
            m1.download_button(T("download_model"), joblib_file, file_name="profit_model.joblib", mime="application/octet-stream")
            m2.download_button(T("download_model_package"), package_file, file_name="profit_model_package.zip", mime="application/zip")
            st.caption(T("model_export_note"))

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
                if pred:
                    st.success(text)
                else:
                    st.warning(text)
                log_event("prediction", f"prediction={pred}, probability={probability:.4f}")
            except Exception as e:
                log_event("prediction_error", str(e))
                st.error(T("pred_failed", error=e))

# ---------------------------------------------------------------- forecast
with tab_forecast:
    st.subheader(T("fc_title"))
    st.write(T("fc_desc"))
    c1, c2 = st.columns(2)
    metric = normalize_metric(c1.radio(T("fc_what"), ["Sales", "Profit"], horizontal=True, key="fc_metric",
                                       format_func=lambda m: T("fc_sales") if m == "Sales" else T("fc_profit")))
    horizon = c2.slider(T("fc_horizon"), 1, 6, 3, key="fc_horizon")

    scope = df  # optional: forecast only one category or region
    scope_columns = [column for column in ["Category", "Region"] if column in df.columns]
    scope_boxes = st.columns(max(len(scope_columns), 1))
    for box, column in zip(scope_boxes, scope_columns):
        chosen = box.selectbox(label(column), [None] + sorted(df[column].astype(str).unique()), key=f"fc_{column}_{data_key}",
                               format_func=lambda v: T("all_values") if v is None else v)
        if chosen is not None and chosen not in (t("en", "all_values"), t("ar", "all_values")):
            scope = scope[scope[column].astype(str) == chosen]

    try:
        result = forecast_monthly(scope, metric, horizon)
    except Exception as e:   # an error here must not blank the whole page
        log_event("forecast_error", f"{type(e).__name__}: {e}")
        st.error(T("fc_failed", error=e))
        result = {"status": "failed", "notes": {"dropped_last": None, "dropped_first": None, "gap_months": 0}}
    notes = result["notes"]
    if notes["dropped_last"] is not None:
        st.info(T("fc_partial_last", month=str(notes["dropped_last"])))
    if notes["dropped_first"] is not None:
        st.info(T("fc_partial_first", month=str(notes["dropped_first"])))
    if notes["gap_months"]:
        st.info(T("fc_gap", n=notes["gap_months"]))

    if result["status"] == "failed":
        pass   # the error is already shown above
    elif result["status"] != "ok":
        st.warning(T("fc_not_enough", needed=result["needed"], found=result["n_months"]))
    else:
        forecast = result["forecast"]
        first = forecast.iloc[0]
        m1, m2 = st.columns(2)
        m1.metric(T("fc_next", month=str(forecast.index[0])), f"{first['forecast']:,.0f}")
        m2.metric(T("fc_range_label"), f"{first['lower']:,.0f} — {first['upper']:,.0f}")
        st.markdown(T("fc_method_line", method=T("fcm_" + result["method"])))
        st.markdown(T("fc_error_line", wape=f"{result['wape']:.1%}", base=f"{result['baseline_wape']:.1%}"))
        message = T("fc_verdict_" + result["verdict"], wape=f"{result['wape']:.0%}", gain=f"{result['gain'] * 100:.1f}")
        {"good": st.success, "ok": st.info, "weak": st.warning}[result["verdict"]](message)
        if result["method"] == "naive":
            st.caption(T("fc_naive_note"))

        history = result["history"].tail(36)
        chart = pd.DataFrame(index=[str(p) for p in list(history.index) + list(forecast.index)])
        chart[T("fc_history_label")] = list(history.values) + [None] * len(forecast)
        join_line = [None] * (len(history) - 1) + [history.iloc[-1]] + list(forecast["forecast"])   # starts at the last real month
        chart[T("fc_forecast_label")] = join_line
        chart[T("fc_col_low")] = [None] * len(history) + list(forecast["lower"])
        chart[T("fc_col_high")] = [None] * len(history) + list(forecast["upper"])
        st.subheader(T("fc_chart"))
        st.line_chart(chart)

        st.subheader(T("fc_table"))
        st.dataframe(pd.DataFrame({
            T("fc_col_month"): [str(p) for p in forecast.index],
            T("fc_col_forecast"): forecast["forecast"].round(0).astype(int).to_numpy(),
            T("fc_col_low"): forecast["lower"].round(0).astype(int).to_numpy(),
            T("fc_col_high"): forecast["upper"].round(0).astype(int).to_numpy(),
        }), hide_index=True, width="stretch")

        with st.expander(T("fc_backtest", n=result["backtest_months"])):
            scores = result["scores"].sort_values()
            st.dataframe(pd.DataFrame({
                T("fc_col_method"): [("✅ " if name == result["method"] else "") + T("fcm_" + name) for name in scores.index],
                T("fc_col_error"): [f"{value:.1%}" for value in scores.values],
            }), hide_index=True, width="stretch")
    st.caption(T("fc_disclaimer"))

# ---------------------------------------------------------------- power bi
with tab_powerbi:
    st.subheader(T("pbi_title"))
    st.write(T("pbi_desc"))
    st.markdown(T("pbi_files"))
    if "model_bundle" not in st.session_state:
        st.info(T("pbi_model_missing"))

    pack_key = (data_key, "model_bundle" in st.session_state, "reliability" in st.session_state)
    if st.button(T("pbi_prepare"), type="primary"):
        try:
            with st.spinner(T("pbi_preparing")):
                reliability_summary = st.session_state["reliability"][1] if "reliability" in st.session_state else None
                files = build_powerbi_files(df, quality_report, st.session_state.get("model_bundle"),
                                            reliability_summary, horizon=3, source=source_name, lang=lang)
            st.session_state["pbi_pack"] = (zip_bytes(files), len(files), files.get(WORKBOOK_NAME), files.get(DASHBOARD_ZIP))
            st.session_state["pbi_pack_key"] = pack_key
            log_event("powerbi_pack", f"files={len(files)}")
        except Exception as e:
            log_event("powerbi_pack_error", str(e))
            st.error(T("process_error", error=e))
    if st.session_state.get("pbi_pack_key") == pack_key and "pbi_pack" in st.session_state:
        pack, count, workbook, dashboard = st.session_state["pbi_pack"]
        st.success(T("pbi_ready", files=count))
        if dashboard is not None:   # the ready dashboard, a Power BI project
            st.download_button(T("pbi_download_dashboard"), dashboard, file_name=DASHBOARD_ZIP, type="primary", mime="application/zip")
            st.caption(T("pbi_dashboard_note"))
        if workbook is not None:   # the main file: everything in ONE Excel workbook
            st.download_button(T("pbi_download_xlsx"), workbook, file_name=WORKBOOK_NAME, type="primary",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        else:
            st.info(T("pbi_too_big", limit=f"{EXCEL_ROW_LIMIT:,}"))
        st.download_button(T("pbi_download"), pack, file_name="power_bi_pack.zip", mime="application/zip")
        st.markdown(T("pbi_steps"))

    st.subheader(T("pbi_refresh_title"))
    st.markdown(T("pbi_refresh_text"))
    dax_file = Path(__file__).parent / "powerbi" / "measures.dax"
    if dax_file.exists():
        with st.expander(T("pbi_dax_title")):
            st.code(dax_file.read_text(encoding="utf-8"), language="sql")

# ---------------------------------------------------------------- assistant
with tab_assistant:
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
with tab_security:
    st.subheader(T("security_title"))
    st.markdown(T("security_points"))
    st.subheader(T("monitoring_title"))
    st.markdown(T("monitoring_points"))

st.divider()
st.caption(T("deploy_note"))
