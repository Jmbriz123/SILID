from copy import deepcopy

import pytest

from config.cities import CITIES, validate_cities
from config.config import ConfigurationError


def test_existing_city_catalog_is_preserved_and_copied():
    result = validate_cities(CITIES)
    assert set(result) == {"manila", "iloilo", "cebu", "baguio", "davao"}
    assert result == CITIES
    assert result is not CITIES
    assert result["manila"] is not CITIES["manila"]


@pytest.mark.parametrize(
    "field,value",
    [
        ("latitude", 91),
        ("longitude", -181),
        ("latitude", float("nan")),
        ("longitude", float("inf")),
        ("latitude", True),
        ("latitude", "14.5"),
        ("name", " "),
        ("timezone", "UTC"),
    ],
)
def test_invalid_city_fields_fail(field, value):
    cities = deepcopy(CITIES)
    cities["manila"][field] = value
    with pytest.raises(ConfigurationError):
        validate_cities(cities)


def test_missing_city_field_is_actionable():
    city = dict(CITIES["manila"])
    city.pop("latitude")
    with pytest.raises(ConfigurationError, match="latitude"):
        validate_cities({"manila": city})


@pytest.mark.parametrize("catalog", [{}, {"Bad Key": {}}, {"manila": None}])
def test_invalid_catalog_fails(catalog):
    with pytest.raises(ConfigurationError):
        validate_cities(catalog)
