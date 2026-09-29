"""The single city catalog; validate it before making source requests."""

import math
import re
from collections.abc import Mapping
from typing import TypedDict

from config.config import PROJECT_TIMEZONE, ConfigurationError


class CityConfig(TypedDict):
    name: str
    latitude: float
    longitude: float
    timezone: str


CITIES: dict[str, CityConfig] = {
    "manila": {
        "name": "Manila",
        "latitude": 14.5995,
        "longitude": 120.9842,
        "timezone": PROJECT_TIMEZONE,
    },
    "iloilo": {
        "name": "Iloilo City",
        "latitude": 10.7202,
        "longitude": 122.5621,
        "timezone": PROJECT_TIMEZONE,
    },
    "cebu": {
        "name": "Cebu City",
        "latitude": 10.3157,
        "longitude": 123.8854,
        "timezone": PROJECT_TIMEZONE,
    },
    "baguio": {
        "name": "Baguio",
        "latitude": 16.4023,
        "longitude": 120.5960,
        "timezone": PROJECT_TIMEZONE,
    },
    "davao": {
        "name": "Davao City",
        "latitude": 7.1907,
        "longitude": 125.4553,
        "timezone": PROJECT_TIMEZONE,
    },
}


def validate_cities(cities: Mapping[str, CityConfig]) -> dict[str, CityConfig]:
    """Return a validated copy, without changing the caller's catalog."""
    if not cities:
        raise ConfigurationError("At least one city must be configured")
    result: dict[str, CityConfig] = {}
    for key, city in cities.items():
        if not isinstance(key, str) or re.fullmatch(r"[a-z][a-z0-9_]*", key) is None:
            raise ConfigurationError("City keys must be lowercase identifiers")
        if not isinstance(city, Mapping):
            raise ConfigurationError("Each city must contain a configuration mapping")
        name = city.get("name")
        if not isinstance(name, str) or not name.strip():
            raise ConfigurationError("City name must not be blank")
        coordinates = {}
        for field_name, limit in (("latitude", 90), ("longitude", 180)):
            value = city.get(field_name)
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not -limit <= value <= limit
                or not math.isfinite(value)
            ):
                raise ConfigurationError(
                    f"City {field_name} must be a finite valid coordinate"
                )
            coordinates[field_name] = float(value)
        if city.get("timezone") != PROJECT_TIMEZONE:
            raise ConfigurationError("City timezone must be Asia/Manila for the MVP")
        result[key] = CityConfig(
            name=name.strip(),
            latitude=coordinates["latitude"],
            longitude=coordinates["longitude"],
            timezone=PROJECT_TIMEZONE,
        )
    return result
