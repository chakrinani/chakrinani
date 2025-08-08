from __future__ import annotations

from typing import List, Literal, Optional

import numpy as np
import pandas as pd


Periodicity = Literal["monthly", "quarterly"]


def ensure_datetime_month(df: pd.DataFrame, date_col: str) -> pd.DataFrame:
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])
    # Normalize to first day of month for consistency
    df[date_col] = df[date_col].values.astype("datetime64[M]")
    return df


def add_quarter_columns(df: pd.DataFrame, date_col: str = "date") -> pd.DataFrame:
    df = df.copy()
    df["year"] = df[date_col].dt.year
    df["quarter"] = df[date_col].dt.quarter
    df["year_quarter"] = df["year"].astype(str) + "-Q" + df["quarter"].astype(str)
    return df


def aggregate_to_period(
    df: pd.DataFrame,
    value_col: str,
    group_cols: List[str],
    periodicity: Periodicity,
    date_col: str = "date",
) -> pd.DataFrame:
    df = ensure_datetime_month(df, date_col)
    if periodicity == "monthly":
        grouped = df.groupby(group_cols + [date_col], dropna=False, as_index=False)[value_col].sum()
        return grouped
    elif periodicity == "quarterly":
        df_q = add_quarter_columns(df, date_col)
        grouped = (
            df_q.groupby(group_cols + ["year", "quarter"], dropna=False, as_index=False)[value_col]
            .sum()
            .sort_values(["year", "quarter"]) 
        )
        grouped["year_quarter"] = grouped["year"].astype(str) + "-Q" + grouped["quarter"].astype(str)
        return grouped
    else:
        raise ValueError("periodicity must be 'monthly' or 'quarterly'")


def compute_growth(
    df: pd.DataFrame,
    value_col: str,
    group_cols: List[str],
    periodicity: Periodicity,
    date_col: str = "date",
) -> pd.DataFrame:
    """Compute YoY and QoQ growth for the given periodicity.

    Returns a DataFrame with the aggregated value and two additional columns:
    - yoy_pct
    - qoq_pct
    """
    agg = aggregate_to_period(df, value_col, group_cols, periodicity, date_col)

    if periodicity == "monthly":
        time_key = date_col
        agg = agg.sort_values(group_cols + [time_key])
        # YoY: shift by 12 months within each group
        if len(group_cols) > 0:
            yoy = agg.groupby(group_cols)[value_col].pct_change(periods=12)
            qoq = agg.groupby(group_cols)[value_col].pct_change(periods=3)
        else:
            yoy = agg[value_col].pct_change(periods=12)
            qoq = agg[value_col].pct_change(periods=3)
        agg["yoy_pct"] = yoy.replace([np.inf, -np.inf], np.nan)
        agg["qoq_pct"] = qoq.replace([np.inf, -np.inf], np.nan)
        return agg

    # Quarterly path
    time_key = "year_quarter"
    agg = agg.sort_values(group_cols + ["year", "quarter"])  # created in quarterly aggregation

    # YoY: compare to same quarter last year (4 quarters earlier)
    if len(group_cols) > 0:
        yoy = agg.groupby(group_cols)[value_col].pct_change(periods=4)
        qoq = agg.groupby(group_cols)[value_col].pct_change(periods=1)
    else:
        yoy = agg[value_col].pct_change(periods=4)
        qoq = agg[value_col].pct_change(periods=1)

    agg["yoy_pct"] = yoy.replace([np.inf, -np.inf], np.nan)
    agg["qoq_pct"] = qoq.replace([np.inf, -np.inf], np.nan)

    return agg


def latest_period_metrics(
    df: pd.DataFrame,
    value_col: str,
    group_cols: List[str],
    periodicity: Periodicity,
    date_col: str = "date",
) -> pd.DataFrame:
    """Return the most recent period value and growth for each group."""
    growth = compute_growth(df, value_col, group_cols, periodicity, date_col)

    if periodicity == "monthly":
        idx = growth.groupby(group_cols)[date_col].idxmax()
    else:
        idx = growth.groupby(group_cols)[["year", "quarter"]].apply(lambda x: x.assign(rank=x["year"] * 4 + x["quarter"]).idxmax()["rank"])  # type: ignore
    latest = growth.loc[idx]
    return latest.reset_index(drop=True)