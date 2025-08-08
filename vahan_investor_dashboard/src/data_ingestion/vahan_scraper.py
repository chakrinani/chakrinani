"""
Experimental Vahan data collector.

The official dashboard is a JSF/PrimeFaces app that maintains server-side state via
javax.faces.ViewState. This makes plain HTTP scraping brittle. Recommended options:

1) Selenium (headless Chrome) to interact with filters and export tables.
2) requests_html (Pyppeteer) to render client-side and then parse DOM.
3) Manual export of relevant tables into data/raw/ then parse with BeautifulSoup.

This module provides a minimal interface and a fallback to sample data.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import List, Optional, Tuple

import pandas as pd

from src.utils.io import get_sample_dir


@dataclass
class VahanQuery:
    start_date: date
    end_date: date
    vehicle_categories: Optional[List[str]] = None  # e.g., ["2W", "3W", "4W"]


def load_sample_category_data() -> pd.DataFrame:
    sample_path = get_sample_dir() / "category_monthly.csv"
    return pd.read_csv(sample_path, parse_dates=["date"])  # columns: date, category, registrations


def load_sample_manufacturer_data() -> pd.DataFrame:
    sample_path = get_sample_dir() / "manufacturer_monthly.csv"
    return pd.read_csv(sample_path, parse_dates=["date"])  # columns: date, category, manufacturer, registrations


# Public interface

def fetch_category_registrations(query: VahanQuery) -> pd.DataFrame:
    """Fetch monthly category-wise registrations. Returns all sample data, optionally filtered by category."""
    df = load_sample_category_data()
    if query.vehicle_categories:
        df = df.loc[df["category"].isin(query.vehicle_categories)]
    return df.reset_index(drop=True)


def fetch_manufacturer_registrations(query: VahanQuery) -> pd.DataFrame:
    """Fetch monthly manufacturer-wise registrations. Returns all sample data, optionally filtered by category."""
    df = load_sample_manufacturer_data()
    if query.vehicle_categories:
        df = df.loc[df["category"].isin(query.vehicle_categories)]
    return df.reset_index(drop=True)


# Notes for future implementers:
# - Add a strategy class (e.g., SeleniumVahanCollector) with .collect(query) -> (category_df, manufacturer_df)
# - Persist raw snapshots with timestamps under data/raw/ to support reproducibility
# - Normalise schemas to match sample CSV columns for downstream compatibility