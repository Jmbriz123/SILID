"""Load settings at an application boundary, never as an import side effect."""

import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit

from dotenv import dotenv_values
from sqlalchemy.engine import URL

PROJECT_TIMEZONE = "Asia/Manila"
DEFAULT_WEATHER_URL = "https://api.open-meteo.com/v1/forecast"


class ConfigurationError(ValueError):
    """Invalid settings; messages identify fields without exposing values."""


def load_environment(
    env_file: Path | None = None,
    *,
    environ: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Read an explicitly selected file, then overlay process environment values.

    No upward .env search, interpolation, or mutation of os.environ occurs.
    An empty environment value overrides a file value and fails required checks.
    """
    values: dict[str, str] = {}
    # create environment variables -> values mappings
    if env_file is not None:
        if not env_file.is_file():
            raise ConfigurationError("The selected environment file does not exist")
        values.update(
            (key, value)
            for key, value in dotenv_values(env_file, interpolate=False).items()
            if value is not None
        )
    #overlay the actual process environment
    values.update(os.environ if environ is None else environ)
    return values


def _required(values: Mapping[str, str], name: str) -> str:
    """Validation for required variables"""
    value = values.get(name)
    if value is None or not value.strip():
        raise ConfigurationError(f"{name} is required and must not be blank")
    return value


@dataclass(frozen=True)
class DatabaseSettings:
    host: str
    port: int
    name: str
    user: str
    password: str = field(repr=False)

    @classmethod
    def from_env(cls, values: Mapping[str, str] | None = None) -> "DatabaseSettings":
        values = os.environ if values is None else values
        if "DB_NAEME" in values:
            raise ConfigurationError("DB_NAEME is unsupported; rename it to DB_NAME")
        host = _required(values, "DB_HOST").strip()
        raw_port = _required(values, "DB_PORT").strip()
        if not raw_port.isascii() or not raw_port.isdecimal():
            raise ConfigurationError("DB_PORT must be an integer from 1 to 65535")
        try:
            port = int(raw_port)
        except ValueError:
            raise ConfigurationError(
                "DB_PORT must be an integer from 1 to 65535"
            ) from None
        if not 1 <= port <= 65535:
            raise ConfigurationError("DB_PORT must be an integer from 1 to 65535")
        if any(char.isspace() for char in host) or "://" in host or "@" in host:
            raise ConfigurationError("DB_HOST must be a hostname or IP address")
        return cls(
            host=host,
            port=port,
            name=_required(values, "DB_NAME").strip(),
            user=_required(values, "DB_USER").strip(),
            password=_required(values, "DB_PASSWORD"),
        )

    @property
    def url(self) -> URL:
        """Build structurally so special characters in credentials remain intact."""
        return URL.create(
            drivername="postgresql+psycopg2",
            username=self.user,
            password=self.password,
            host=self.host,
            port=self.port,
            database=self.name,
        )


@dataclass(frozen=True)
class WeatherSettings:
    base_url: str = DEFAULT_WEATHER_URL
    timezone: str = PROJECT_TIMEZONE

    @classmethod
    def from_env(cls, values: Mapping[str, str] | None = None) -> "WeatherSettings":
        values = os.environ if values is None else values
        base_url = values.get("OPEN_METEO_BASE_URL", DEFAULT_WEATHER_URL).strip()
        try:
            parsed = urlsplit(base_url)
            valid_url = (
                parsed.scheme == "https"
                and bool(parsed.hostname)
                and parsed.username is None
                and parsed.password is None
                and not parsed.query
                and not parsed.fragment
                and (parsed.port is None or 1 <= parsed.port <= 65535)
                and not any(char.isspace() for char in base_url)
            )
        except ValueError:
            valid_url = False
        if not valid_url:
            raise ConfigurationError(
                "OPEN_METEO_BASE_URL must be an HTTPS URL without credentials, query, or fragment"
            )
        timezone = values.get("TIMEZONE", PROJECT_TIMEZONE).strip()
        if timezone != PROJECT_TIMEZONE:
            raise ConfigurationError("TIMEZONE must be Asia/Manila for the MVP")
        return cls(base_url=base_url, timezone=timezone)
