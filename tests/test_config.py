import os
import subprocess
import sys
from pathlib import Path

import pytest
from sqlalchemy.engine import make_url

from config.config import (
    ConfigurationError,
    DatabaseSettings,
    WeatherSettings,
    load_environment,
)


@pytest.mark.parametrize(
    "field", ["DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"]
)
@pytest.mark.parametrize("value", [None, "", "   "])
def test_database_requires_explicit_values(database_env, field, value):
    if value is None:
        database_env.pop(field)
    else:
        database_env[field] = value
    with pytest.raises(ConfigurationError, match=field):
        DatabaseSettings.from_env(database_env)


@pytest.mark.parametrize("port", ["abc", "0", "65536", "-1", "3.5", "５４３２"])
def test_invalid_port_is_rejected_without_echoing_value(database_env, port):
    database_env["DB_PORT"] = port
    with pytest.raises(ConfigurationError, match="DB_PORT") as error:
        DatabaseSettings.from_env(database_env)
    assert database_env["DB_PASSWORD"] not in str(error.value)


@pytest.mark.parametrize("host,port", [("localhost", "15432"), ("postgres", "5432")])
def test_host_and_container_settings_are_explicit(database_env, host, port):
    database_env.update(DB_HOST=host, DB_PORT=port, POSTGRES_PORT="9999")
    settings = DatabaseSettings.from_env(database_env)
    assert settings.host == host
    assert settings.port == int(port)


def test_airflow_and_bootstrap_settings_do_not_supply_application_credentials():
    with pytest.raises(ConfigurationError, match="DB_HOST"):
        DatabaseSettings.from_env(
            {
                "POSTGRES_USER": "metadata",
                "POSTGRES_PASSWORD": "bootstrap-only",
                "POSTGRES_DB": "airflow",
                "AIRFLOW__DATABASE__SQL_ALCHEMY_CONN": "postgresql://metadata",
            }
        )


def test_old_typo_has_actionable_error(database_env):
    database_env["DB_NAEME"] = "silid"
    with pytest.raises(ConfigurationError, match="rename it to DB_NAME"):
        DatabaseSettings.from_env(database_env)


def test_password_is_preserved_and_hidden_in_settings_repr(database_env):
    database_env["DB_PASSWORD"] = "  special:p@ss/$word  "
    settings = DatabaseSettings.from_env(database_env)
    assert settings.password == database_env["DB_PASSWORD"]
    assert settings.password not in repr(settings)
    assert settings.password not in repr(settings.url)
    encoded = settings.url.render_as_string(hide_password=False)
    assert make_url(encoded).password == settings.password


@pytest.mark.parametrize(
    "host", ["postgresql://localhost", "bad host", "user@localhost"]
)
def test_database_host_is_not_a_connection_string(database_env, host):
    database_env["DB_HOST"] = host
    with pytest.raises(ConfigurationError, match="DB_HOST"):
        DatabaseSettings.from_env(database_env)


def test_file_is_explicit_environment_wins_and_no_global_mutation(
    tmp_path, monkeypatch
):
    file = tmp_path / ".env"
    file.write_text("DB_HOST=file-host\nDB_PASSWORD='literal-${HOME}'\n")
    monkeypatch.setenv("DB_HOST", "process-host")
    monkeypatch.delenv("DB_PASSWORD", raising=False)
    before = dict(os.environ)
    values = load_environment(file)
    assert values["DB_HOST"] == "process-host"
    assert values["DB_PASSWORD"] == "literal-${HOME}"
    assert dict(os.environ) == before


def test_no_implicit_dotenv_search(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text("DB_HOST=hidden-host\n")
    monkeypatch.chdir(tmp_path)
    assert load_environment(environ={}) == {}


def test_blank_environment_does_not_fall_back_to_file(tmp_path, database_env):
    file = tmp_path / ".env"
    file.write_text("DB_PASSWORD=file-password\n")
    database_env["DB_PASSWORD"] = ""
    values = load_environment(file, environ=database_env)
    with pytest.raises(ConfigurationError, match="DB_PASSWORD"):
        DatabaseSettings.from_env(values)


def test_missing_explicit_file_is_an_error(tmp_path):
    with pytest.raises(ConfigurationError, match="does not exist"):
        load_environment(tmp_path / "missing.env", environ={})


def test_public_weather_defaults_require_no_database():
    settings = WeatherSettings.from_env({})
    assert settings.base_url == "https://api.open-meteo.com/v1/forecast"
    assert settings.timezone == "Asia/Manila"


@pytest.mark.parametrize(
    "url",
    [
        "",
        "http://example.com",
        "https://user:secret@example.com",
        "https://",
        "https://example.com?token=secret",
        "https://example.com#fragment",
        "https://example.com:99999",
        "https://bad host",
        "https://[bad",
    ],
)
def test_weather_url_validation_does_not_expose_values(url):
    with pytest.raises(ConfigurationError, match="OPEN_METEO_BASE_URL") as error:
        WeatherSettings.from_env({"OPEN_METEO_BASE_URL": url})
    assert "secret" not in str(error.value)


@pytest.mark.parametrize("timezone", ["UTC", "", "Asia/Manilla"])
def test_mvp_timezone_is_explicit(timezone):
    with pytest.raises(ConfigurationError, match="TIMEZONE"):
        WeatherSettings.from_env({"TIMEZONE": timezone})


def test_checked_in_example_is_valid():
    example = Path(__file__).resolve().parents[1] / ".env.example"
    values = load_environment(example, environ={})
    assert DatabaseSettings.from_env(values).host == "localhost"
    assert WeatherSettings.from_env(values).timezone == "Asia/Manila"


def test_config_cli_has_safe_output_and_nonzero_failure(tmp_path, database_env):
    valid = subprocess.run(
        [sys.executable, "-m", "config.check"],
        cwd=tmp_path,
        env=database_env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert valid.returncode == 0, valid.stderr
    assert "5 cities" in valid.stdout
    assert database_env["DB_PASSWORD"] not in valid.stdout + valid.stderr
    database_env["DB_PORT"] = "credential-like-invalid-value"
    invalid = subprocess.run(
        [sys.executable, "-m", "config.check"],
        cwd=tmp_path,
        env=database_env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert invalid.returncode == 1
    assert "DB_PORT" in invalid.stdout
    assert database_env["DB_PORT"] not in invalid.stdout + invalid.stderr
