"""
grocery_pipeline.py

A daily Airflow pipeline that:
  1. Loads grocery_orders.csv from Cloud Storage into BigQuery (raw table).
  2. Rebuilds the dept_daily_sales analytics table (partitioned + clustered).
  3. Runs a data-quality check: fail the DAG if grocery_orders is empty.
"""

from datetime import datetime

from airflow import DAG
from airflow.providers.google.cloud.transfers.gcs_to_bigquery import (
    GCSToBigQueryOperator,
)
from airflow.providers.google.cloud.operators.bigquery import (
    BigQueryInsertJobOperator,
    BigQueryCheckOperator,
)

# --- Project settings ---
PROJECT_ID = "retail-pipeline-499301"
DATASET = "retail"
BUCKET = "reatil_pipeline_digvijay_2026"
CSV_OBJECT = "grocery_orders.csv"
RAW_TABLE = "grocery_orders"
ANALYTICS_TABLE = "dept_daily_sales"

# --- SQL: rebuild the partitioned + clustered analytics table ---
TRANSFORM_SQL = f"""
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET}.{ANALYTICS_TABLE}`
PARTITION BY order_date
CLUSTER BY department AS
SELECT
  order_date,
  department,
  SUM(quantity * unit_price) AS total_sales,
  SUM(quantity) AS total_units
FROM `{PROJECT_ID}.{DATASET}.{RAW_TABLE}`
GROUP BY order_date, department;
"""

# --- Quality check: fail if the raw table is empty ---
QUALITY_SQL = f"""
SELECT COUNT(*) FROM `{PROJECT_ID}.{DATASET}.{RAW_TABLE}`
"""

with DAG(
    dag_id="grocery_pipeline",
    description="Load CSV to BigQuery, rebuild analytics table, run quality check.",
    start_date=datetime(2026, 1, 1),
    schedule="@daily",
    catchup=False,
    tags=["grocery", "bigquery", "gcp"],
) as dag:

    # Step 1: load the CSV from Cloud Storage into BigQuery.
    load_data = GCSToBigQueryOperator(
        task_id="load_data",
        bucket=BUCKET,
        source_objects=[CSV_OBJECT],
        destination_project_dataset_table=f"{PROJECT_ID}.{DATASET}.{RAW_TABLE}",
        source_format="CSV",
        skip_leading_rows=1,
        write_disposition="WRITE_TRUNCATE",  # replace the table each run
        autodetect=True,                     # infer schema from the CSV header
        project_id=PROJECT_ID,
    )

    # Step 2: rebuild the partitioned + clustered analytics table.
    transform_data = BigQueryInsertJobOperator(
        task_id="transform_data",
        configuration={
            "query": {
                "query": TRANSFORM_SQL,
                "useLegacySql": False,
            }
        },
        project_id=PROJECT_ID,
    )

    # Step 3: data-quality check — fails the DAG if the raw table is empty.
    quality_check = BigQueryCheckOperator(
        task_id="quality_check",
        sql=QUALITY_SQL,
        use_legacy_sql=False,
    )

    load_data >> transform_data >> quality_check
