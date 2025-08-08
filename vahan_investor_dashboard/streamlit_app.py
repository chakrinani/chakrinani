from __future__ import annotations

import os
from datetime import date
from typing import List, Optional

import altair as alt
import duckdb
import pandas as pd
import streamlit as st

from src.data_ingestion.vahan_scraper import VahanQuery, fetch_category_registrations, fetch_manufacturer_registrations
from src.data_processing.transformations import compute_growth, aggregate_to_period
from src.utils.io import get_processed_dir

st.set_page_config(page_title="Vahan Investor Dashboard", page_icon="🚘", layout="wide")


@st.cache_data(show_spinner=False)
def load_data(start_date: date, end_date: date, categories: Optional[List[str]]):
    query = VahanQuery(start_date=start_date, end_date=end_date, vehicle_categories=categories)
    cat_df = fetch_category_registrations(query)
    mfr_df = fetch_manufacturer_registrations(query)
    return cat_df, mfr_df


def render_header():
    st.title("Vahan Investor Dashboard")
    st.caption("YoY and QoQ growth across vehicle categories and manufacturers")


def render_sidebar(cat_df: pd.DataFrame, mfr_df: pd.DataFrame):
    min_date = min(cat_df["date"].min(), mfr_df["date"].min()).date()
    max_date = max(cat_df["date"].max(), mfr_df["date"].max()).date()

    with st.sidebar:
        st.subheader("Filters")
        date_range = st.date_input(
            "Date range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
        )

        categories = sorted(cat_df["category"].unique().tolist())
        selected_categories = st.multiselect("Vehicle categories", options=categories, default=categories)

        # Manufacturer selection depends on categories
        mfr_options = (
            mfr_df.loc[mfr_df["category"].isin(selected_categories), "manufacturer"].dropna().unique().tolist()
            if selected_categories
            else mfr_df["manufacturer"].dropna().unique().tolist()
        )
        selected_manufacturers = st.multiselect("Manufacturers", options=sorted(mfr_options), default=sorted(mfr_options))

        periodicity = st.radio("Periodicity", options=["monthly", "quarterly"], horizontal=True, index=0)

        use_sql = st.toggle("Use SQL Engine (DuckDB)", value=False, help="Compute aggregates using DuckDB instead of pandas")

    return date_range, selected_categories, selected_manufacturers, periodicity, use_sql


def filter_data(cat_df: pd.DataFrame, mfr_df: pd.DataFrame, date_range, categories, manufacturers):
    start_date, end_date = date_range
    mask_cat = (cat_df["date"].dt.date >= start_date) & (cat_df["date"].dt.date <= end_date)
    mask_mfr = (mfr_df["date"].dt.date >= start_date) & (mfr_df["date"].dt.date <= end_date)
    if categories:
        mask_cat &= cat_df["category"].isin(categories)
        mask_mfr &= mfr_df["category"].isin(categories)
    if manufacturers:
        mask_mfr &= mfr_df["manufacturer"].isin(manufacturers)

    return cat_df.loc[mask_cat].copy(), mfr_df.loc[mask_mfr].copy()


def kpi(value, label, delta):
    col = st.container()
    with col:
        st.metric(label=label, value=f"{value:,.0f}", delta=(f"{delta:+.1%}" if pd.notna(delta) else "N/A"))


def render_kpis(cat_df: pd.DataFrame, mfr_df: pd.DataFrame, periodicity: str, use_sql: bool):
    # Total across selected categories
    if use_sql:
        # Write to in-memory DuckDB from DataFrames
        con = duckdb.connect()
        con.register("cat", cat_df)
        con.register("mfr", mfr_df)
        if periodicity == "monthly":
            cat_agg = con.execute(
                """
                WITH mon AS (
                  SELECT date_trunc('month', date)::DATE AS date, SUM(registrations) AS registrations
                  FROM cat
                  GROUP BY 1
                ),
                mon_ord AS (
                  SELECT *, ROW_NUMBER() OVER (ORDER BY date) AS rn FROM mon
                )
                SELECT m.*,
                       (m.registrations / NULLIF(lag_y.registrations,0) - 1) AS qoq_pct,
                       (m.registrations / NULLIF(lag_y12.registrations,0) - 1) AS yoy_pct
                FROM mon_ord m
                LEFT JOIN mon_ord lag_y ON lag_y.rn = m.rn - 3
                LEFT JOIN mon_ord lag_y12 ON lag_y12.rn = m.rn - 12
                ORDER BY date
                """
            ).df()
        else:
            cat_agg = con.execute(
                """
                WITH q AS (
                  SELECT CAST(EXTRACT(year FROM date) AS INTEGER) AS year,
                         CAST(EXTRACT(quarter FROM date) AS INTEGER) AS quarter,
                         SUM(registrations) AS registrations
                  FROM cat
                  GROUP BY 1,2
                ),
                q_ord AS (
                  SELECT *, (year*4 + quarter) AS qn, ROW_NUMBER() OVER (ORDER BY year,quarter) AS rn FROM q
                )
                SELECT q.*,
                       (q.registrations / NULLIF(lag_q.registrations,0) - 1) AS qoq_pct,
                       (q.registrations / NULLIF(lag_y.registrations,0) - 1) AS yoy_pct
                FROM q_ord q
                LEFT JOIN q_ord lag_q ON lag_q.rn = q.rn - 1
                LEFT JOIN q_ord lag_y ON lag_y.rn = q.rn - 4
                ORDER BY year, quarter
                """
            ).df()
        latest = cat_agg.iloc[-1] if len(cat_agg) else None
        total_value = int(latest["registrations"]) if latest is not None else 0
        yoy = latest.get("yoy_pct", None) if latest is not None else None
        qoq = latest.get("qoq_pct", None) if latest is not None else None
    else:
        total_series = cat_df.groupby("date", as_index=False)["registrations"].sum()
        total_growth = compute_growth(total_series, value_col="registrations", group_cols=[], periodicity=periodicity)
        latest = total_growth.iloc[-1] if len(total_growth) else None
        total_value = int(latest["registrations"]) if latest is not None else 0
        yoy = latest.get("yoy_pct", None) if latest is not None else None
        qoq = latest.get("qoq_pct", None) if latest is not None else None

    c1, c2, c3 = st.columns(3)
    with c1:
        kpi(total_value, "Total registrations (latest period)", None)
    with c2:
        st.metric(label="YoY growth", value=(f"{yoy:.1%}" if pd.notna(yoy) else "N/A"))
    with c3:
        st.metric(label="QoQ growth", value=(f"{qoq:.1%}" if pd.notna(qoq) else "N/A"))


def render_trend_chart(df: pd.DataFrame, time_col: str, value_col: str, color_col: Optional[str], title: str):
    line = (
        alt.Chart(df)
        .mark_line(point=True)
        .encode(
            x=alt.X(time_col, title="Period"),
            y=alt.Y(value_col, title="Registrations"),
            color=alt.Color(color_col, title=color_col.capitalize() if color_col else None) if color_col else alt.value("#1f77b4"),
            tooltip=[time_col, value_col] + ([color_col] if color_col else []),
        )
        .properties(height=350, title=title)
    )
    st.altair_chart(line, use_container_width=True)


def main():
    render_header()

    # Default: load the full available range from sample/live
    # We first load broad range; sidebar will narrow
    full_start = (pd.Timestamp.today().normalize().replace(day=1) - pd.DateOffset(months=23)).date()
    full_end = pd.Timestamp.today().normalize().date()

    cat_df, mfr_df = load_data(full_start, full_end, categories=None)

    date_range, selected_categories, selected_manufacturers, periodicity, use_sql = render_sidebar(cat_df, mfr_df)

    # Filtered data
    cat_df_f, mfr_df_f = filter_data(cat_df, mfr_df, date_range, selected_categories, selected_manufacturers)

    # KPIs
    render_kpis(cat_df_f, mfr_df_f, periodicity=periodicity, use_sql=use_sql)

    # Trends by category
    if periodicity == "monthly":
        cat_growth = compute_growth(cat_df_f, value_col="registrations", group_cols=["category"], periodicity="monthly")
        time_col = "date"
    else:
        cat_growth = compute_growth(cat_df_f, value_col="registrations", group_cols=["category"], periodicity="quarterly")
        time_col = "year_quarter"

    render_trend_chart(
        df=cat_growth.rename(columns={"registrations": "Registrations"}),
        time_col=time_col,
        value_col="Registrations",
        color_col="category",
        title="Category registrations over time",
    )

    # Trends by manufacturer (within selected categories)
    if periodicity == "monthly":
        mfr_growth = compute_growth(mfr_df_f, value_col="registrations", group_cols=["manufacturer"], periodicity="monthly")
        time_col2 = "date"
    else:
        mfr_growth = compute_growth(mfr_df_f, value_col="registrations", group_cols=["manufacturer"], periodicity="quarterly")
        time_col2 = "year_quarter"

    render_trend_chart(
        df=mfr_growth.rename(columns={"registrations": "Registrations"}),
        time_col=time_col2,
        value_col="Registrations",
        color_col="manufacturer",
        title="Manufacturer registrations over time",
    )

    st.divider()

    # Show latest-period manufacturer leaderboard with growth
    if periodicity == "monthly":
        latest_idx = mfr_growth.groupby(["manufacturer"]) ["date"].idxmax()
    else:
        latest_idx = mfr_growth.groupby(["manufacturer"]) [["year", "quarter"]].apply(lambda x: x.assign(rank=x["year"] * 4 + x["quarter"]).idxmax()["rank"])  # type: ignore

    latest_mfr = mfr_growth.loc[latest_idx].sort_values("registrations", ascending=False)
    latest_mfr = latest_mfr[["manufacturer", "registrations", "yoy_pct", "qoq_pct"]].rename(columns={
        "registrations": "Registrations",
        "yoy_pct": "YoY",
        "qoq_pct": "QoQ",
    })

    st.subheader("Latest period: Manufacturer leaderboard")
    st.dataframe(
        latest_mfr,
        use_container_width=True,
        column_config={
            "Registrations": st.column_config.NumberColumn(format=",d"),
            "YoY": st.column_config.NumberColumn(format="%.1f%%"),
            "QoQ": st.column_config.NumberColumn(format="%.1f%%"),
        },
        hide_index=True,
    )


if __name__ == "__main__":
    main()