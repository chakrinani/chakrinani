import os
from pathlib import Path
from typing import Optional

import pandas as pd


def get_project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def get_data_dir() -> Path:
    return get_project_root() / "data"


def get_sample_dir() -> Path:
    return get_data_dir() / "sample"


def get_processed_dir() -> Path:
    path = get_data_dir() / "processed"
    path.mkdir(parents=True, exist_ok=True)
    return path


def load_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)


def save_parquet(df: pd.DataFrame, filename: str) -> Path:
    path = get_processed_dir() / filename
    df.to_parquet(path, index=False)
    return path


def load_parquet(filename: str) -> Optional[pd.DataFrame]:
    path = get_processed_dir() / filename
    if path.exists():
        return pd.read_parquet(path)
    return None