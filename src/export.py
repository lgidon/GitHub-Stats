from pathlib import Path
import duckdb

# Define paths relative to project root
PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "data" / "warehouse.duckdb"
EXPORT_DIR = PROJECT_ROOT / "data" / "exports"


def export_marts():
    """Exports dbt mart models from DuckDB to compressed Parquet files."""
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Database not found at {DB_PATH}. Run dbt models first!"
        )

    # Ensure output directory exists
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    # Connect to DuckDB
    conn = duckdb.connect(str(DB_PATH))

    marts = ["fct_pull_requests", "dim_authors"]

    print("🚀 Starting Parquet exports...")

    for mart in marts:
        output_file = EXPORT_DIR / f"{mart}.parquet"

        # Export table directly to Parquet with Snappy compression
        query = f"""
            COPY {mart} TO '{output_file}' (FORMAT PARQUET, COMPRESSION 'SNAPPY');
        """
        conn.execute(query)

        # Get file size for verification
        file_size_kb = output_file.stat().st_size / 1024
        print(f"  ✓ Exported {mart} -> {output_file.name} ({file_size_kb:.2f} KB)")

    conn.close()
    print("✨ Parquet export complete!")


if __name__ == "__main__":
    export_marts()