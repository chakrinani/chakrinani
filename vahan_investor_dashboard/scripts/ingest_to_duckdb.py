from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "processed" / "vahan.duckdb"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def main():
    con = duckdb.connect(DB_PATH.as_posix())

    category_csv = ROOT / "data" / "sample" / "category_monthly.csv"
    manufacturer_csv = ROOT / "data" / "sample" / "manufacturer_monthly.csv"

    con.execute("CREATE SCHEMA IF NOT EXISTS vahan;")

    con.execute(
        """
        CREATE OR REPLACE TABLE vahan.category_monthly AS
        SELECT * FROM read_csv_auto(?);
        """,
        [category_csv.as_posix()],
    )

    con.execute(
        """
        CREATE OR REPLACE TABLE vahan.manufacturer_monthly AS
        SELECT * FROM read_csv_auto(?);
        """,
        [manufacturer_csv.as_posix()],
    )

    print(f"DuckDB database initialized at {DB_PATH}")


if __name__ == "__main__":
    main()