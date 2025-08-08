from __future__ import annotations

from datetime import date
from pathlib import Path
import random

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SAMPLE_DIR = ROOT / "data" / "sample"
SAMPLE_DIR.mkdir(parents=True, exist_ok=True)


random.seed(42)
np.random.seed(42)


def month_range(end_months_back: int = 0, periods: int = 24):
    today = pd.Timestamp.today().normalize()  # midnight
    last_month = (today.replace(day=1) - pd.offsets.MonthBegin(1)) - pd.DateOffset(months=end_months_back)
    start_month = last_month - pd.DateOffset(months=periods - 1)
    months = pd.period_range(start=start_month, end=last_month, freq="M").to_timestamp()
    return list(months)


def generate_category_series(months, base: int, drift: float, noise_scale: float = 0.03):
    values = []
    level = base
    for i, m in enumerate(months):
        # compound drift with small noise
        growth = 1.0 + drift + np.random.normal(0, noise_scale)
        level = max(0, level * growth)
        values.append(int(round(level)))
    return values


def main():
    months = month_range(periods=24)

    categories = {
        "2W": {"base": 800000, "drift": 0.01},
        "3W": {"base": 70000, "drift": 0.008},
        "4W": {"base": 320000, "drift": 0.005},
    }

    # Category-level
    cat_rows = []
    for cat, conf in categories.items():
        values = generate_category_series(months, conf["base"], conf["drift"], noise_scale=0.05)
        for m, v in zip(months, values):
            cat_rows.append({"date": m, "category": cat, "registrations": v})
    cat_df = pd.DataFrame(cat_rows)

    # Manufacturer splits (category-specific shares that drift slowly)
    manufacturers = {
        "2W": ["Bajaj", "Hero", "Honda", "TVS", "Yamaha"],
        "3W": ["Bajaj", "Piaggio", "Mahindra"],
        "4W": ["Maruti", "Hyundai", "Tata", "Mahindra", "Kia", "Toyota"],
    }

    mfr_rows = []
    rng = np.random.default_rng(123)

    for cat in categories.keys():
        mfrs = manufacturers[cat]
        # Initial random shares that sum to 1
        shares = rng.dirichlet(np.ones(len(mfrs)))
        for m in months:
            # small random walk on shares each month
            shares = shares + rng.normal(0, 0.01, size=len(shares))
            shares = np.clip(shares, 0.01, None)
            shares = shares / shares.sum()

            total_cat = int(cat_df.loc[(cat_df["category"] == cat) & (cat_df["date"] == m), "registrations"].values[0])
            for mf, sh in zip(mfrs, shares):
                mfr_rows.append({
                    "date": m,
                    "category": cat,
                    "manufacturer": mf,
                    "registrations": int(round(total_cat * float(sh)))
                })

    mfr_df = pd.DataFrame(mfr_rows)

    # Save
    cat_df.to_csv(SAMPLE_DIR / "category_monthly.csv", index=False)
    mfr_df.to_csv(SAMPLE_DIR / "manufacturer_monthly.csv", index=False)

    print(f"Wrote {SAMPLE_DIR / 'category_monthly.csv'} and {SAMPLE_DIR / 'manufacturer_monthly.csv'}")


if __name__ == "__main__":
    main()