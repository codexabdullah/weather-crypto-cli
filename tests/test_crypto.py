"""
Live integration tests for CryptoAPI.

These tests make real HTTP calls to the Coinbase public spot-price API
(no mocking, no API key). They require an active internet connection and
validate that the live response schema still matches what CryptoAPI expects.
"""

import pytest

from dash_cli.crypto import CryptoAPI, SymbolNotFoundError


def test_crypto_live_success():
    """Fetching BTC should return a correctly-typed dict with a positive USD price."""
    api = CryptoAPI()
    data = api.get_price("BTC")

    assert isinstance(data, dict)
    assert "symbol" in data
    assert "price_usd" in data

    assert data["symbol"] == "BTC"
    assert isinstance(data["price_usd"], float)
    assert data["price_usd"] > 0


def test_crypto_invalid_symbol():
    """An unrecognised ticker should raise SymbolNotFoundError."""
    api = CryptoAPI()

    with pytest.raises(SymbolNotFoundError):
        api.get_price("XYZINVALID")
