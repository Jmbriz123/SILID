"""Validate settings without contacting the API or database."""

import argparse
from pathlib import Path

from config.cities import CITIES, validate_cities
from config.config import (
    ConfigurationError,
    DatabaseSettings,
    WeatherSettings,
    load_environment,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path, help="Explicit optional dotenv file")
    args = parser.parse_args()
    try:
        values = load_environment(args.env_file)
        DatabaseSettings.from_env(values)
        WeatherSettings.from_env(values)
        cities = validate_cities(CITIES)
    except ConfigurationError as exc:
        print(f"Configuration invalid: {exc}")
        return 1
    print(
        f"Configuration valid: database settings, weather settings, {len(cities)} cities"
    )
    print("No connections were attempted; credentials were not displayed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
