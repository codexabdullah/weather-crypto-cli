"""
Crypto API wrapper module for dash-cli.

Uses the official Coinbase public spot-price API (no authentication required):
  https://api.coinbase.com/v2/prices/{SYMBOL}-USD/spot

Returns live USD spot prices for any token supported by Coinbase.
"""

import requests


# ---------------------------------------------------------------------------
# Custom exception hierarchy
# ---------------------------------------------------------------------------


class CryptoAPIError(Exception):
    """Base exception for all CryptoAPI-related errors."""

    pass


class SymbolNotFoundError(CryptoAPIError):
    """Raised when the given symbol is not recognised by Coinbase (404)."""

    pass


class RateLimitError(CryptoAPIError):
    """Raised when the Coinbase API rate limit has been exceeded (429)."""

    pass


class CryptoNetworkError(CryptoAPIError):
    """Raised for connection drops, DNS failures, or request timeouts."""

    pass


# ---------------------------------------------------------------------------
# API client
# ---------------------------------------------------------------------------


class CryptoAPI:
    """
    A lightweight client for fetching real-time cryptocurrency spot prices
    from the Coinbase public API. No API key required.
    """

    BASE_URL = "https://api.coinbase.com/v2/prices"
    DEFAULT_TIMEOUT = 5  # seconds

    def get_price(self, symbol: str) -> dict:
        """
        Fetch the current USD spot price for a cryptocurrency symbol.

        Args:
            symbol: Ticker symbol to look up (e.g. "BTC", "ETH", "SOL").
                    Case-insensitive — normalised to uppercase internally.

        Returns:
            A dictionary with keys:
                symbol    (str)          – canonical uppercase ticker symbol
                price_usd (float | None) – current USD spot price, rounded to 2 dp

        Raises:
            SymbolNotFoundError:  Symbol not recognised by Coinbase (404).
            RateLimitError:       Coinbase rate limit exceeded (429).
            CryptoNetworkError:   Request timeout or network-level failure.
            CryptoAPIError:       Any other unexpected HTTP error.
        """
        symbol = symbol.upper()
        url = f"{self.BASE_URL}/{symbol}-USD/spot"

        try:
            response = requests.get(url, timeout=self.DEFAULT_TIMEOUT)
            response.raise_for_status()

        except requests.exceptions.Timeout as exc:
            raise CryptoNetworkError(
                f"Request timed out while fetching the spot price for '{symbol}'."
            ) from exc

        except requests.exceptions.HTTPError as exc:
            status_code = exc.response.status_code if exc.response is not None else None

            if status_code == 404:
                raise SymbolNotFoundError(
                    f"'{symbol}' is not a recognised symbol on Coinbase. "
                    "Verify the ticker and try again."
                ) from exc
            elif status_code == 429:
                raise RateLimitError(
                    "Coinbase rate limit exceeded. Please wait a moment before retrying."
                ) from exc
            else:
                raise CryptoAPIError(
                    f"Coinbase API returned an unexpected error (HTTP {status_code})."
                ) from exc

        except requests.exceptions.RequestException as exc:
            raise CryptoNetworkError(
                f"Failed to connect to Coinbase while fetching the price for '{symbol}'. "
                "Check your internet connection and try again."
            ) from exc

        data = response.json().get("data", {})
        raw_price = data.get("amount")
        price_usd = round(float(raw_price), 2) if raw_price is not None else None

        return {
            "symbol": data.get("base", symbol),
            "price_usd": price_usd,
        }
