# 📊 GitHub Engineering Metrics & DORA Analytics Pipeline

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://dora-metrics.streamlit.app)
[![Pipeline Status](https://github.com/lgidon/GitHub-Stats/actions/workflows/pipeline.yml/badge.svg)](https://github.com/lgidon/GitHub-Stats/actions)


An end-to-end, production-grade Data Engineering pipeline and interactive dashboard that ingests GitHub REST API metrics, transforms data into analytical star schemas using **dbt** and **DuckDB**, and publishes live DORA metrics via a **Streamlit** web application.

---

## 🌟 Architecture Overview

```text
┌────────────────┐     ┌────────────────┐     ┌─────────────────┐     ┌────────────────┐
│  GitHub API    │ ──► │ Python Extract │ ──► │  dbt + DuckDB   │ ──► │ Parquet Marts  │
│ (Raw Metrics)  │     │  (Ingestion)   │     │(Transformations)│     │ (data/exports) │
└────────────────┘     └────────────────┘     └─────────────────┘     └───────┬────────┘
                                                                              │
                                                                              ▼
┌────────────────┐                   ┌─────────────────┐              ┌────────────────┐
│ Live Dashboard │ ◄──────────────── │ Streamlit Cloud │ ◄─────────── │  Git Auto-Push │
│  (Streamlit)   │                   │  (Presentation) │              │(GitHub Actions)│
└────────────────┘                   └─────────────────┘              └────────────────┘
```

The pipeline operates on an automated daily batch schedule using GitHub Actions, capturing metrics across multiple public and private repositories:

1. Extraction: Python queries the GitHub REST API for pull requests, reviews, commits, and author metadata.

2. Transformation: dbt-duckdb transforms raw JSON/relational payloads into a structured analytical star schema (fact tables and dimensions) with automated quality tests.

3. Export: Processed data marts are exported as compressed columnar Parquet files (fct_pull_requests.parquet, dim_authors.parquet).

4. Publishing: A multi-job GitHub Actions workflow commits analytical Parquet files back to main, triggering seamless data reloads on Streamlit Community Cloud.

## 🛠️ Tech Stack
* Orchestration & CI/CD: GitHub Actions (Multi-job workflow DAG)

* Data Ingestion: Python 3.11, requests

* Data Warehousing & Query Engine: DuckDB

* Data Transformation & Modeling: dbt (dbt-duckdb)

* Storage Format: Apache Parquet

* Visualization & Analytics: Streamlit, Plotly, Pandas

## 📈 Key Dashboard Metrics (DORA & Engineering Velocity)
* Deployment & Pull Request Volume: Total PRs created, merged, and closed across tracked repositories.

* Lead Time to Merge: Average and median time (in hours) from PR creation to merge event.

* Merge Rate Efficiency: Percentage of total pull requests successfully merged into main branches.

* Repository Comparison: Dynamic multi-repository filtering and cross-repo performance benchmarking.

## 🚀 Getting Started Locally
Prerequisites
* Python 3.11+

* A GitHub Personal Access Token (PAT) with repo scope

* Git
  
1. Clone the Repository & Setup Environment:
```Bash
git clone [https://github.com/lgidon/GitHub-Stats.git](https://github.com/lgidon/GitHub-Stats.git)
cd GitHub-Stats

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

# Install dependencies
pip install -r requirements-elt.txt
pip install -r requirements.txt
```

2. Configure Environment Variables
Create a .env file in the root directory:
```
GH_TOKEN=your_github_personal_access_token_here
```

3. Run the Data Pipeline
```Bash
# Step 1: Extract raw data from GitHub API
python src/extract.py

# Step 2: Run dbt models and data quality tests
cd transform
dbt run --profiles-dir ./.dbt
dbt test --profiles-dir ./.dbt
cd ..

# Step 3: Export transformed marts to Parquet
python src/export.py
```

4. Launch the Streamlit Dashboard

```Bash
streamlit run app.py
```

## 🔄 CI/CD Pipeline Architecture
The GitHub Actions workflow (.github/workflows/pipeline.yml) is split into two isolated, dependent jobs for maximum reliability and visibility:

* build-elt: Handles Python environment setup, API extraction, dbt transformations, data quality testing, Parquet generation, and artifact archiving.

* publish-marts: Runs strictly after build-elt succeeds. Downloads exported Parquet artifacts and pushes updated analytical files back to the main branch to refresh the live dashboard.

## 🛡️ Data Quality & Testing
Data integrity is maintained using dbt tests defined in schema configuration files:

* Unique & Non-Null Constraints: Applied to primary keys (pull_request_id, author_id).

* Accepted Values: Validating PR state values (open, closed, merged).

* Relationship Integrity: Foreign key checks linking fact tables to dimension models.

## 🔗 Live Demo & Deployment

The production dashboard is hosted on **Streamlit Community Cloud** and automatically refreshes daily whenever fresh analytical Parquet exports are pushed by GitHub Actions.

👉 **Explore the Live App Here:** [https://github-stats.streamlit.app](https://dora-metrics.streamlit.app)

---

## 🔬 Ad-Hoc Exploratory Analysis

In addition to the interactive dashboard, the exported Parquet files allow for rapid ad-hoc SQL querying and exploratory analysis without spinning up a database server.

Check out [`notebooks/ad_hoc_dora_analysis.ipynb`](notebooks/ad_hoc_dora_analysis.ipynb) to see how to query the Parquet data marts directly using DuckDB and Plotly in Python:

```python
import duckdb

# Query local Parquet marts using standard SQL via DuckDB
df = duckdb.query("""
    SELECT repo_name, COUNT(*) as total_prs, AVG(total_open_hours) as avg_open_time
    FROM '../data/exports/fct_pull_requests.parquet'
    GROUP BY repo_name
    """).df()

df
```
---