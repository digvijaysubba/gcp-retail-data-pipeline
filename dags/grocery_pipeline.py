# grocery_pipeline.py
# A simple Airflow pipeline (DAG) with three steps that run in order:
#   load  ->  transform  ->  quality_check
# For now each step just prints a message. Later we'll make them
# actually run the BigQuery load + transform.

from airflow.sdk import DAG
from airflow.providers.standard.operators.python import PythonOperator
import pendulum


# --- The three jobs the robot will do ---

def load_data():
    print("Step 1: Loading grocery orders from Cloud Storage into BigQuery...")


def transform_data():
    print("Step 2: Building the dept_daily_sales summary table...")


def quality_check():
    print("Step 3: Checking the data (no missing departments, rows > 0)...")
    print("Quality check passed!")


# --- The pipeline definition ---

with DAG(
    dag_id="grocery_pipeline",                       # the name shown in Airflow
    schedule="@daily",                               # run once a day
    start_date=pendulum.datetime(2026, 6, 1, tz="UTC"),  # when it's allowed to start
    catchup=False,                                   # don't run for past dates
    tags=["retail"],                                 # a label to find it easily
) as dag:

    load = PythonOperator(
        task_id="load_data",
        python_callable=load_data,
    )

    transform = PythonOperator(
        task_id="transform_data",
        python_callable=transform_data,
    )

    check = PythonOperator(
        task_id="quality_check",
        python_callable=quality_check,
    )

    # This line sets the ORDER: load first, then transform, then check.
    load >> transform >> check
