import os
import sys
import time
import duckdb
import requests
from dotenv import load_dotenv
import json

CONFIG_PATH = os.getenv("CONFIG_PATH", "config.json")

# Load environment variables from .env file (for local testing)
load_dotenv()

GITHUB_TOKEN = os.getenv("TOKEN")
DB_PATH = os.getenv("DUCKDB_PATH", "data/warehouse.duckdb")


def get_headers():
    """Build authorization headers for GitHub API."""
    headers = {"Accept": "application/vnd.github.v3+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    else:
        print("⚠️ Warning: GITHUB_TOKEN not found. Running unauthenticated (60 req/hr limit).")
    return headers


def fetch_pull_requests(owner: str, repo: str, max_pages: int = 3) -> list:
    """
    Fetch PRs from GitHub REST API with pagination.
    max_pages=3 fetches up to 300 recent PRs per repo (great for dev/testing).
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
    all_prs = []
    headers = get_headers()

    for page in range(1, max_pages + 1):
        params = {
            "state": "all",      # open, merged, and closed PRs
            "per_page": 100,     # Max allowed by GitHub API
            "page": page,
            "sort": "created",
            "direction": "desc"  # Fetch newest PRs first
        }

        print(f"  Fetching {owner}/{repo} - Page {page}...")
        response = requests.get(url, headers=headers, params=params)

        if response.status_code != 200:
            print(f"❌ Error fetching data ({response.status_code}): {response.text}")
            break

        data = response.json()
        if not data:
            break  # Stop if page is empty

        # Attach repo metadata to each record before storing
        for pr in data:
            pr["repo_owner"] = owner
            pr["repo_name"] = repo

        all_prs.extend(data)
        
        # Respect rate limits with a small delay
        time.sleep(0.5)

    print(f"✅ Fetched {len(all_prs)} total PRs for {owner}/{repo}.")
    return all_prs


def load_to_duckdb(all_prs: list):
    """Load the raw list of dictionaries directly into DuckDB as a staging table."""
    if not all_prs:
        print("No data to load.")
        return

    # Ensure output data folder exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    # Temporary raw JSON file path
    temp_json_path = "data/temp_prs.json"

    # Write Python list of dicts to a temporary JSON file
    with open(temp_json_path, "w", encoding="utf-8") as f:
        json.dump(all_prs, f)

    try:
        # Connect to DuckDB database file
        conn = duckdb.connect(DB_PATH)

        print(f"📦 Loading {len(all_prs)} records into DuckDB (`{DB_PATH}`)...")

        # DuckDB reads JSON directly from disk and infers the table schema automatically
        conn.execute(f"""
            CREATE OR REPLACE TABLE stg_raw_pull_requests AS 
            SELECT * FROM read_json_auto('{temp_json_path}');
        """)

        # Quick verification count
        count = conn.execute("SELECT COUNT(*) FROM stg_raw_pull_requests").fetchone()[0]
        print(f"🎉 Success! `stg_raw_pull_requests` table now contains {count} rows.")

        conn.close()

    finally:
        # Clean up temporary raw JSON file
        if os.path.exists(temp_json_path):
            os.remove(temp_json_path)

def main():
    print("🚀 Starting GitHub API Extraction...")
    aggregated_prs = []

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)

    max_pages = config.get("max_pages", 3)
    target_repos = config.get(
        "target_repos",
        [
            {"owner": "duckdb", "repo": "duckdb"},
            {"owner": "jenkinsci", "repo": "jenkins"},
        ],
    )

    for target in target_repos:
        prs = fetch_pull_requests(target["owner"], target["repo"], max_pages=max_pages)
        aggregated_prs.extend(prs)

    load_to_duckdb(aggregated_prs)


if __name__ == "__main__":
    main()
