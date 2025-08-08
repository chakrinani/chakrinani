# Vahan Investor Dashboard

A Streamlit dashboard focused on vehicle registration data with an investor lens. It computes Year-over-Year (YoY) and Quarter-over-Quarter (QoQ) growth for vehicle categories and manufacturers.

This project is designed to work out-of-the-box using included sample data and optionally with live data (experimental) sourced from the Vahan Dashboard.


## Features
- Interactive Streamlit UI
- Filters: date range, vehicle category, manufacturer
- Metrics: YoY and QoQ growth
- Charts: trend lines with % change annotations
- Optional SQL path using DuckDB for aggregation
- Modular Python codebase with clear separation of concerns


## Project Structure
```
vahan_investor_dashboard/
├─ streamlit_app.py
├─ requirements.txt
├─ README.md
├─ .gitignore
├─ data/
│  ├─ sample/
│  │  ├─ category_monthly.csv
│  │  └─ manufacturer_monthly.csv
│  └─ processed/  (created at runtime)
├─ scripts/
│  ├─ generate_sample_data.py
│  └─ ingest_to_duckdb.py
└─ src/
   ├─ data_ingestion/
   │  └─ vahan_scraper.py  (experimental)
   ├─ data_processing/
   │  └─ transformations.py
   └─ utils/
      └─ io.py
```


## Setup
1. Create and activate a virtual environment (recommended):
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. (Optional) Generate fresh sample data:
   ```bash
   python scripts/generate_sample_data.py
   ```


## Run the Dashboard
```bash
streamlit run streamlit_app.py
```

The app will launch in your browser. Use the sidebar filters to explore trends and growth metrics.


## Data Sources and Assumptions
- Primary source intended: Vahan Dashboard (`https://vahan.parivahan.gov.in/vahan4dashboard/vahan/view/reportview.xhtml`).
- Due to the dynamic nature of the portal (JSF/PrimeFaces + stateful requests), fully automated scraping is non-trivial and may require a headless browser. An experimental module is provided in `src/data_ingestion/vahan_scraper.py` describing approaches and providing a stub.
- To ensure this assignment runs end-to-end without external dependencies, curated sample CSVs are included under `data/sample/`. These mimic plausible patterns for:
  - Vehicle categories: 2W, 3W, 4W
  - Manufacturers per category
  - Monthly data for the last 24 months

If you want to attempt live collection, see the "Live Data (Experimental)" section below.


## How Growth Is Calculated
- YoY: percent change relative to the same period one year earlier.
- QoQ: percent change relative to the immediately preceding quarter.
- Periodicity: Monthly or Quarterly (selectable). For quarterly, we internally aggregate months into fiscal quarters (calendar quarters) and compute growth.

Implemented in `src/data_processing/transformations.py`.


## Optional SQL Path (DuckDB)
The app can compute aggregates either with pandas or SQL via DuckDB. Toggle the "Use SQL Engine (DuckDB)" switch in the app to compute summary metrics with SQL.

DuckDB is embedded and requires no server setup.


## Live Data (Experimental)
The `src/data_ingestion/vahan_scraper.py` module provides guidance and a stub for live data collection. Options:
- Use `selenium` (headless Chrome) to render and interact with the JSF page, then parse tables.
- Use `requests_html` (Pyppeteer) to render JavaScript.
- Manual export: Download relevant reports periodically and place under `data/raw/`, then parse.

For reliability and to avoid brittle automation against a stateful JSF app, this demo defaults to included sample data.


## Recording the Walkthrough
Record a short screen capture (≤ 5 minutes) showing:
- How to run the app
- Navigating filters, interpreting YoY/QoQ
- A couple of investor-relevant insights observed

Upload as unlisted YouTube or Google Drive and include the link in your submission.


## Valuable Insight (Example)
- Hypothetical example (from included sample data): 2W manufacturers show consistent QoQ acceleration for 3 consecutive quarters while 4W shows deceleration YoY, potentially indicating consumer down-trading or 2W financing tailwinds.

Replace with real observations if you collect live data.


## Roadmap
- Automate robust Vahan data extraction with Selenium and stable selectors
- Persist historical snapshots for reproducibility
- Add additional dimensions: fuel type, state-level drilldowns
- Add cohort decomposition and seasonal adjustment


## License
MIT