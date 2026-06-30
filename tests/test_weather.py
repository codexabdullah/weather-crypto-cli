"""
Live integration tests for WeatherAPI.

These tests make real HTTP calls to the Open-Meteo geocoding and forecast
APIs (no mocking, no API key). They require an active internet connection
and validate that the live response schema still matches what WeatherAPI
expects.
"""

import pytest

from dash_cli.weather import WeatherAPI, CityNotFoundError


def test_weather_live_success():
    """A well-known city should return a complete, correctly-typed weather payload."""
    api = WeatherAPI()
    data = api.get_weather("Lahore")

    assert isinstance(data, dict)

    expected_keys = {"temperature", "description", "humidity", "wind_speed"}
    assert expected_keys.issubset(data.keys())

    assert isinstance(data["temperature"], (int, float))
    assert isinstance(data["humidity"], (int, float))
    assert isinstance(data["wind_speed"], (int, float))


def test_weather_invalid_city():
    """A nonsense city name should fail geocoding and raise CityNotFoundError."""
    api = WeatherAPI()

    with pytest.raises(CityNotFoundError):
        api.get_weather("Nonexistentville12345xyz")
