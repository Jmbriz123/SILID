"""Legacy PostgreSQL JSONB loader; authoritative MinIO Bronze is Step 3."""

import argparse
import logging
from pathlib import Path
from typing import Any

import psycopg2
from psycopg2.extras import Json

from config.config import DatabaseSettings, WeatherSettings, load_environment
from ingestion.extract import run_extraction_batch

logger = logging.getLogger(__name__)


def load_extracted_records_to_bronze(
    records: list[dict[str, Any]], *, settings: DatabaseSettings | None = None
) -> None:
    """Insert parsed responses using validated application database settings."""
    settings = settings if settings is not None else DatabaseSettings.from_env()
    insert_query = """
        INSERT INTO bronze.weather_raw (city_key, city_name, ingested_at, raw_payload)
        VALUES (%s, %s, %s, %s)
    """
    try:
        with psycopg2.connect(
            host=settings.host,
            port=settings.port,
            dbname=settings.name,
            user=settings.user,
            password=settings.password,
        ) as connection:
            with connection.cursor() as cursor:
                for record in records:
                    cursor.execute(
                        insert_query,
                        (
                            record["city_key"],
                            record["city_name"],
                            record["ingested_at"],
                            Json(record["raw_payload"]),
                        ),
                    )
            # The connection context commits on success and rolls back on failure.
        logger.info("Loaded %d records into legacy Bronze", len(records))
    except psycopg2.Error:
        logger.error("Failed loading records into legacy Bronze")
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    values = load_environment(args.env_file)
    database = DatabaseSettings.from_env(values)
    weather = WeatherSettings.from_env(values)
    # Validate database settings before making any HTTP requests.
    data = run_extraction_batch(settings=weather)
    load_extracted_records_to_bronze(data, settings=database)
