import subprocess
import sys
from unittest.mock import MagicMock

import pytest
import requests

from config.cities import CITIES
from config.config import ConfigurationError, DatabaseSettings, WeatherSettings
from ingestion.extract import fetch_city_weather, run_extraction_batch
from ingestion.load import load_extracted_records_to_bronze


def test_imports_work_outside_repo_without_settings_or_import_side_effects(tmp_path):
    # An invalid dotenv beside the caller must not affect imports.
    (tmp_path / ".env").write_text("DB_PORT=not-an-integer\n")
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import logging; import config.config; import config.cities; "
            "import ingestion.extract; import ingestion.load; "
            "assert not logging.getLogger().handlers",
        ],
        cwd=tmp_path,
        env={},
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == ""


def test_extractor_uses_configured_endpoint(monkeypatch):
    response = MagicMock()
    response.json.return_value = {"hourly": {}}
    get = MagicMock(return_value=response)
    monkeypatch.setattr("ingestion.extract.requests.get", get)
    settings = WeatherSettings.from_env(
        {"OPEN_METEO_BASE_URL": "https://example.com/weather"}
    )
    record = fetch_city_weather("manila", CITIES["manila"], settings=settings)
    assert get.call_args.args == (settings.base_url,)
    assert get.call_args.kwargs["params"]["timezone"] == "Asia/Manila"
    assert record["raw_payload"] == response.json.return_value


def test_bad_city_configuration_fails_before_http(monkeypatch):
    monkeypatch.setattr("ingestion.extract.CITIES", {"bad key": {}})
    with pytest.raises(ConfigurationError, match="City keys"):
        run_extraction_batch(settings=WeatherSettings.from_env({}))


def test_prototype_http_failure_propagates_original_error(monkeypatch):
    error = requests.HTTPError("source unavailable")
    response = MagicMock()
    response.raise_for_status.side_effect = error
    monkeypatch.setattr(
        "ingestion.extract.requests.get", MagicMock(return_value=response)
    )
    with pytest.raises(requests.HTTPError) as caught:
        fetch_city_weather(
            "manila", CITIES["manila"], settings=WeatherSettings.from_env({})
        )
    assert caught.value is error


def test_loader_uses_validated_application_credentials(monkeypatch, database_env):
    connect = MagicMock()
    monkeypatch.setattr("ingestion.load.psycopg2.connect", connect)
    settings = DatabaseSettings.from_env(database_env)
    record = {
        "city_key": "manila",
        "city_name": "Manila",
        "ingested_at": "2026-09-28T00:00:00+00:00",
        "raw_payload": {},
    }
    load_extracted_records_to_bronze([record], settings=settings)
    connect.assert_called_once_with(
        host="localhost",
        port=5432,
        dbname="silid",
        user="silid_app",
        password=database_env["DB_PASSWORD"],
    )
    cursor = connect.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value
    assert cursor.execute.call_count == 1
