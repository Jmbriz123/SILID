"""Prototype hourly extraction; raw-response preservation is roadmap Step 3."""

import argparse
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

from config.cities import CITIES, CityConfig, validate_cities
from config.config import WeatherSettings, load_environment

logger = logging.getLogger(__name__)


def fetch_city_weather(
    city_key: str,
    city_meta: CityConfig,
    *,
    settings: WeatherSettings | None = None,
) -> dict[str, Any]:
    """Fetch the prototype's hourly payload using explicit weather settings."""
    settings = settings if settings is not None else WeatherSettings.from_env()
    api_parameters = {
        "latitude": city_meta["latitude"],
        "longitude": city_meta["longitude"],
        "hourly": [
            "temperature_2m",
            "relative_humidity_2m",
            "apparent_temperature",
            "precipitation_probability",
            "precipitation",
            "rain",
            "wind_speed_10m",
        ],
        "timezone": settings.timezone,
    }
    try:
        response = requests.get(settings.base_url, params=api_parameters, timeout=10)
        response.raise_for_status()
        return {
            "city_key": city_key,
            "city_name": city_meta["name"],
            "ingested_at": datetime.now(timezone.utc).isoformat(),
            "raw_payload": response.json(),
        }
    except requests.RequestException:
        # Do not swallow failure or log a potentially sensitive response/URL.
        logger.error("API extraction failed for city %s", city_key)
        raise


def run_extraction_batch(
    *, settings: WeatherSettings | None = None
) -> list[dict[str, Any]]:
    """Validate the complete catalog before making any source requests."""
    settings = settings if settings is not None else WeatherSettings.from_env()
    cities = validate_cities(CITIES)
    records = []
    for city_key, city_meta in cities.items():
        logger.info("Extracting weather for city %s", city_key)
        records.append(fetch_city_weather(city_key, city_meta, settings=settings))
    return records


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    weather = WeatherSettings.from_env(load_environment(args.env_file))
    data = run_extraction_batch(settings=weather)
    logger.info("Extracted %d city payloads", len(data))
