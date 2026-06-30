"""
Weather API wrapper module for dash-cli.
Uses WeatherAPI.com to fetch live stats and a 3-day forecast.
"""

import os
import requests


class WeatherAPIError(Exception):
    """Base exception for all WeatherAPI-related errors."""

    pass


class LocationNotFoundError(WeatherAPIError):
    """Raised when the given location/city is not found (HTTP 400 - Code 1006)."""

    pass


class InvalidAPIKeyError(WeatherAPIError):
    """Raised when the configured API key is invalid or expired (HTTP 401)."""

    pass


class WeatherNetworkError(WeatherAPIError):
    """Raised for network drops, DNS failures, or timeouts."""

    pass


class WeatherAPI:
    """Client for interacting with WeatherAPI.com endpoints."""

    BASE_URL = "http://api.weatherapi.com/v1"
    DEFAULT_TIMEOUT = 5

    def __init__(self):
        # Fallback to a placeholder string to avoid crashes during token validation
        self.api_key = os.getenv("WEATHER_API_KEY", "PLACEHOLDER_KEY")

    def get_weather(self, city: str) -> dict:
        """
        Fetch real-time weather and 3-day forecast for a city.

        Args:
            city: Name of the city (e.g., "Lahore", "London").

        Returns:
            A clean parsed dictionary with current stats and forecast days.
        """
        url = f"{self.BASE_URL}/forecast.json"
        params = {
            "key": self.api_key,
            "q": city,
            "days": 3,
            "aqi": "no",
            "alerts": "no",
        }

        try:
            response = requests.get(url, params=params, timeout=self.DEFAULT_TIMEOUT)
            response.raise_for_status()

        except requests.exceptions.Timeout as exc:
            raise WeatherNetworkError(
                f"Request timed out while fetching weather for '{city}'."
            ) from exc

        except requests.exceptions.HTTPError as exc:
            res = exc.response
            status_code = res.status_code if res is not None else None

            if status_code == 401:
                raise InvalidAPIKeyError(
                    "Invalid or expired WeatherAPI key. "
                    "Check your environment variables."
                ) from exc

            if status_code == 400:
                try:
                    err_data = res.json().get("error", {})
                    if err_data.get("code") == 1006:
                        raise LocationNotFoundError(
                            f"City '{city}' was not found. "
                            "Please check the spelling."
                        ) from exc
                except (ValueError, AttributeError):
                    pass

            raise WeatherAPIError(
                f"Weather API returned unexpected error (HTTP {status_code})."
            ) from exc

        except requests.exceptions.RequestException as exc:
            raise WeatherNetworkError(
                f"Failed to connect to Weather API for '{city}'. "
                "Check your connection."
            ) from exc

        data = response.json()
        current = data.get("current", {})
        location = data.get("location", {})

        forecast_list = []
        for day in data.get("forecast", {}).get("forecastday", []):
            day_data = day.get("day", {})
            forecast_list.append(
                {
                    "date": day.get("date"),
                    "condition": day_data.get("condition", {}).get("text"),
                    "max_temp_c": day_data.get("maxtemp_c"),
                    "min_temp_c": day_data.get("mintemp_c"),
                }
            )

        return {
            "city": location.get("name"),
            "country": location.get("country"),
            "current": {
                "temp_c": current.get("temp_c"),
                "condition": current.get("condition", {}).get("text"),
                "humidity": current.get("humidity"),
                "wind_kph": current.get("wind_kph"),
            },
            "forecast": forecast_list,
        }
