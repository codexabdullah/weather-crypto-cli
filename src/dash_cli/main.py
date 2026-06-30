"""
Main entry point for dash-cli.

Defines the top-level Click group and all sub-commands, wiring together
the WeatherAPI and CryptoAPI modules with Rich-styled terminal output.

Data sources (both fully free, no authentication required):
  - Weather: Open-Meteo (geocoding + forecast)
  - Crypto:  Coinbase public spot-price API
"""

import sys

import click
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from dash_cli.weather import WeatherAPI, WeatherAPIError
from dash_cli.crypto import CryptoAPI, CryptoAPIError

console = Console()


@click.group()
def main():
    """dash-cli: Real-time weather and crypto data in your terminal."""
    pass


# ---------------------------------------------------------------------------
# weather sub-command
# ---------------------------------------------------------------------------


@main.command()
@click.option(
    "--city",
    required=True,
    type=str,
    help="City name to fetch live weather data for (e.g. 'Lahore', 'London').",
)
def weather(city: str):
    """Fetch real-time weather for a specified city via Open-Meteo."""
    console.print(
        f"\n[bold cyan]⛅  Fetching live weather for[/bold cyan] "
        f"[bold white]{city}[/bold white]...\n"
    )

    api = WeatherAPI()

    try:
        data = api.get_weather(city)
    except WeatherAPIError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)

    temp = data.get("temperature")
    humidity = data.get("humidity")
    wind_speed = data.get("wind_speed")
    description = (data.get("description") or "N/A").capitalize()
    lat = data.get("latitude")
    lon = data.get("longitude")

    table = Table(box=box.SIMPLE_HEAVY, show_header=False, pad_edge=False, expand=False)
    table.add_column("Field", style="bold dim", min_width=20)
    table.add_column("Value", style="bold white", min_width=24)

    table.add_row("🌡  Temperature", f"{temp} °C" if temp is not None else "N/A")
    table.add_row("🌤  Condition", description)
    table.add_row("💧  Humidity", f"{humidity}%" if humidity is not None else "N/A")
    table.add_row(
        "💨  Wind Speed", f"{wind_speed} km/h" if wind_speed is not None else "N/A"
    )
    table.add_row("🌐  Coordinates", f"{lat}°N, {lon}°E" if lat and lon else "N/A")

    source_note = Text(
        "Source: Open-Meteo · open-meteo.com · No API key required", style="dim"
    )

    console.print(
        Panel(
            table,
            title=f"[bold cyan]  Weather — {data.get('city', city)}[/bold cyan]",
            subtitle=source_note,
            border_style="cyan",
            padding=(1, 2),
        )
    )
    console.print()


# ---------------------------------------------------------------------------
# crypto sub-command
# ---------------------------------------------------------------------------


@main.command()
@click.option(
    "--symbol",
    required=True,
    type=str,
    help="Cryptocurrency ticker symbol to fetch live price for (e.g. 'BTC', 'ETH', 'SOL').",
)
def crypto(symbol: str):
    """Fetch real-time USD spot price for a cryptocurrency via Coinbase."""
    symbol = symbol.upper()
    console.print(
        f"\n[bold green]🪙  Fetching live price for[/bold green] "
        f"[bold white]{symbol}[/bold white]...\n"
    )

    api = CryptoAPI()

    try:
        data = api.get_price(symbol)
    except CryptoAPIError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)

    price = data.get("price_usd")
    price_str = f"${price:,.2f}" if price is not None else "N/A"

    table = Table(box=box.SIMPLE_HEAVY, show_header=False, pad_edge=False, expand=False)
    table.add_column("Field", style="bold dim", min_width=20)
    table.add_column("Value", style="bold white", min_width=24)

    table.add_row("🪙  Symbol", data.get("symbol", symbol))
    table.add_row("💵  Spot Price (USD)", price_str)

    source_note = Text(
        "Source: Coinbase Public API · api.coinbase.com · No API key required",
        style="dim",
    )

    console.print(
        Panel(
            table,
            title=f"[bold green]  Crypto — {data.get('symbol', symbol)} / USD[/bold green]",
            subtitle=source_note,
            border_style="green",
            padding=(1, 2),
        )
    )
    console.print()


if __name__ == "__main__":
    main()
