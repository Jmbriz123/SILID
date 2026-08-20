# SILID: Philippine Weather & Productivity Data Platform

> **Work in Progress** — A containerized data engineering platform that ingests hourly Philippine weather data, validates and transforms it through Bronze/Silver/Gold layers using dbt and Apache Airflow, and serves weather-derived productivity insights through Streamlit.

---

## 🏗 Architecture

```mermaid
graph TD
    A[Open-Meteo API] -->|Hourly Extraction| B[Apache Airflow]
    B --> C[(Bronze Layer<br/>Raw API JSON / Auditable)]
    C --> D[(Silver Layer<br/>Cleaned / Typed / UTC+8)]
    D -->|dbt Transformations| E[(Gold Layer<br/>Productivity Metrics & Analytics)]
    E --> F[Streamlit Dashboard]
    E --> G[Monitoring & Alerts]