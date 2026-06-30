"""
Weather API wrapper module for dash-cli.

Uses the fully free, zero-authentication Open-Meteo API ecosystem:
  - Geocoding:  https://geocoding-api.open-meteo.com/v1/search
  - Forecast:   https://api.open-meteo.com/v1/forecast

No API key required.
"""

import requests


# ---------------------------------------------------------------------------
# WMO Weather Interpretation Code → Human-readable description
# Reference: https://open-meteo.com/en/docs#weathervariables
# ---------------------------------------------------------------------------

WMO_CODE_MAP: dict[int, str] = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Foggy",
    48: "Rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Slight snowfall",
    73: "Moderate snowfall",
    75: "Heavy snowfall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


# ---------------------------------------------------------------------------
# Custom exception hierarchy
# ---------------------------------------------------------------------------


class WeatherAPIError(Exception):
    """Base exception for all WeatherAPI-related errors."""

    pass


class CityNotFoundError(WeatherAPIError):
    """Raised when geocoding returns no results for the given city."""

    pass


class WeatherServiceTimeoutError(WeatherAPIError):
    """Raised when any HTTP request to the weather stack times out."""

    pass


class WeatherServiceConnectionError(WeatherAPIError):
    """Raised for connection drops, DNS failures, or other network issues."""

    pass


# ---------------------------------------------------------------------------
# API client
# ---------------------------------------------------------------------------


class WeatherAPI:
    """
    A lightweight client for fetching real-time weather data.

    Strategy:
      1. Resolve the city name to coordinates via Open-Meteo's free geocoding API.
      2. Fetch live weather from the Open-Meteo forecast API using those coordinates.

    No API key required. Both endpoints are fully public.
    """

    GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
    FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
    DEFAULT_TIMEOUT = 10  # seconds

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _geocode(self, city: str) -> tuple[float, float, str]:
        """
        Resolve a city name to (latitude, longitude, resolved_display_name).

        Args:
            city: Free-text city name supplied by the user.

        Returns:
            Tuple of (latitude, longitude, resolved_name).

        Raises:
            CityNotFoundError:             No geocoding results returned.
            WeatherServiceTimeoutError:    Request timed out.
            WeatherServiceConnectionError: Network-level failure.
        """
        try:
            response = requests.get(
                self.GEOCODING_URL,
                params={"name": city, "count": 1, "language": "en", "format": "json"},
                timeout=self.DEFAULT_TIMEOUT,
            )
            response.raise_for_status()

        except requests.exceptions.Timeout as exc:
            raise WeatherServiceTimeoutError(
                f"Geocoding request timed out while resolving '{city}'."
            ) from exc

        except requests.exceptions.RequestException as exc:
            raise WeatherServiceConnectionError(
                f"Failed to reach the geocoding service for '{city}'. "
                "Check your internet connection and try again."
            ) from exc

        results = response.json().get("results", [])
        if not results:
            raise CityNotFoundError(
                f"City '{city}' could not be found. Check the spelling and try again."
            )

        top = results[0]
        parts = [top.get("name", city)]
        if top.get("admin1"):
            parts.append(top["admin1"])
        if top.get("country_code"):
            parts.append(top["country_code"])
        resolved_name = ", ".join(parts)

        return top["latitude"], top["longitude"], resolved_name

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def get_weather(self, city: str) -> dict:
        """
        Fetch real-time weather data for the given city.

        Args:
            city: The name of the city to fetch weather data for.

        Returns:
            A dictionary with keys:
                city        (str)          – resolved city name with region/country
                latitude    (float)        – resolved latitude
                longitude   (float)        – resolved longitude
                temperature (float | None) – current temperature in °C
                humidity    (int | None)   – relative humidity in %
                wind_speed  (float | None) – wind speed in km/h
                description (str)          – human-readable WMO weather condition

        Raises:
            CityNotFoundError:             City cannot be geocoded.
            WeatherServiceTimeoutError:    Request timed out.
            WeatherServiceConnectionError: Network-level failure.
            WeatherAPIError:               Unexpected HTTP error from forecast API.
        """
        latitude, longitude, resolved_name = self._geocode(city)

        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m",
            "wind_speed_unit": "kmh",
            "timezone": "auto",
        }

        try:
            response = requests.get(
                self.FORECAST_URL,
                params=params,
                timeout=self.DEFAULT_TIMEOUT,
            )
            response.raise_for_status()

        except requests.exceptions.Timeout as exc:
            raise WeatherServiceTimeoutError(
                f"Forecast request timed out while fetching data for '{city}'."
            ) from exc

        except requests.exceptions.HTTPError as exc:
            status_code = exc.response.status_code if exc.response is not None else None
            raise WeatherAPIError(
                f"Weather forecast service returned an unexpected error (HTTP {status_code})."
            ) from exc

        except requests.exceptions.RequestException as exc:
            raise WeatherServiceConnectionError(
                f"Failed to reach the weather forecast service for '{city}'. "
                "Check your internet connection and try again."
            ) from exc

        current = response.json().get("current", {})
        weather_code = current.get("weather_code")
        description = WMO_CODE_MAP.get(weather_code, f"Unknown (code {weather_code})")

        return {
            "city": resolved_name,
            "latitude": latitude,
            "longitude": longitude,
            "temperature": current.get("temperature_2m"),
            "humidity": current.get("relative_humidity_2m"),
            "wind_speed": current.get("wind_speed_10m"),
            "description": description,
        }
