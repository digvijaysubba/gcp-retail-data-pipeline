# RetailFlow — GCP Retail Data & AI Pipeline

An end-to-end data and AI pipeline built on Google Cloud Platform, modeled on a
grocery retail use case. Raw order data is ingested and transformed in BigQuery,
orchestrated with Apache Airflow, and (next phase) surfaced through a Vertex AI
retrieval-augmented generation (RAG) agent that answers plain-English questions
about the data.

## Architecture

```
Cloud Storage (raw CSV)
        |
        v
BigQuery (raw orders table)
        |
        v
BigQuery (partitioned + clustered analytics table: dept_daily_sales)
        |
        v
[in progress] Vertex AI RAG agent  ->  natural-language Q&A
```

Apache Airflow orchestrates the **load -> transform -> data-quality-check**
steps on a daily schedule. GitHub Actions (planned) provides CI/CD.

## What's implemented

- Ingestion of grocery order data from Cloud Storage into BigQuery.
- A partitioned (by date) and clustered (by department) analytics table,
  `dept_daily_sales`, summarizing daily sales per department.
- An Apache Airflow DAG (`dags/grocery_pipeline.py`) that orchestrates the
  load -> transform -> quality-check workflow on a daily schedule, running
  locally via Docker Compose.

## In progress / planned

- **Vertex AI RAG layer:** embeddings + Vector Search + Gemini for
  natural-language queries over the BigQuery data.
- **GitHub Actions CI/CD** to lint and validate the pipeline.

## Tech stack

Python, Google Cloud Platform (BigQuery, Cloud Storage, Vertex AI),
Apache Airflow, Docker, SQL, GitHub Actions.

## Repository layout

- `dags/grocery_pipeline.py` — the Airflow pipeline definition.
- `sql/transform.sql` — the BigQuery transform that builds `dept_daily_sales`.
- `docker-compose.yaml` — local Airflow environment (Docker Compose).

## Running locally

1. Start Airflow from this folder: `docker compose up -d`
2. Open the Airflow UI at http://localhost:8080
3. Enable and trigger the `grocery_pipeline` DAG.
