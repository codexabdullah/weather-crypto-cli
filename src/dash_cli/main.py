"""
Main CLI entry point for dash-cli.
Defines the click commands for interacting with weather and crypto APIs.
"""

import click
from rich.console import Console
from rich.table import Table

from dash_cli.crypto import CryptoAPI, CryptoAPIError
from dash_cli.weather import WeatherAPI, WeatherAPIError

console = Console()


@click.group()
def main():
    """A minimal, high-authority CLI tool for weather and crypto prices."""
    pass


@main.command()
@click.argument("city")
def weather(city: str):
    """Fetch current weather and 3-day forecast for a given CITY."""
    client = WeatherAPI()
    try:
        with console.status(f"[bold green]Fetching weather for {city}...[/bold green]"):
            data = client.get_weather(city)

        # Current Weather Card
        city_name = data["city"]
        country_name = data["country"]
        msg = (
            f"\n[bold cyan]Current Weather in "
            f"{city_name}, {country_name}[/bold cyan]"
        )
        console.print(msg)
        console.print(f"Condition: {data['current']['condition']}")
        temp_str = (
            f"Temperature: [bold yellow]" f"{data['current']['temp_c']}°C[/bold yellow]"
        )
        console.print(temp_str)
        console.print(f"Humidity: {data['current']['humidity']}%")
        console.print(f"Wind Speed: {data['current']['wind_kph']} kph")

        # Forecast Table
        table = Table(title="\n3-Day Weather Forecast", title_style="bold magenta")
        table.add_column("Date", style="cyan")
        table.add_column("Condition", style="green")
        table.add_column("Max Temp", style="red", justify="right")
        table.add_column("Min Temp", style="blue", justify="right")

        for day in data["forecast"]:
            table.add_row(
                day["date"],
                day["condition"],
                f"{day['max_temp_c']}°C",
                f"{day['min_temp_c']}°C",
            )

        console.print(table)

    except WeatherAPIError as err:
        console.print(f"[bold red]Error:[/bold red] {err}")
    except Exception:
        console.print("[bold red]Fatal Error:[/bold red] An unexpected error occurred.")


@main.command()
@click.argument("symbol")
def crypto(symbol: str):
    """Fetch the real-time USD spot price for a CRYPTO token."""
    client = CryptoAPI()
    try:
        with console.status(
            f"[bold green]Fetching spot price for {symbol.upper()}...[/bold green]"
        ):
            data = client.get_price(symbol)

        symbol_name = data["symbol"]
        price = data["price_usd"]

        console.print("\n[bold magenta]Coinbase Live Spot Price[/bold magenta]")
        if price is not None:
            console.print(
                f"Asset: [bold cyan]{symbol_name}[/bold cyan] -> "
                f"Price: [bold green]${price:,.2f} USD[/bold green]"
            )
        else:
            console.print(
                f"Asset: [bold cyan]{symbol_name}[/bold cyan] -> "
                "[bold yellow]Price Unavailable[/bold yellow]"
            )

    except CryptoAPIError as err:
        console.print(f"[bold red]Error:[/bold red] {err}")
    except Exception:
        console.print("[bold red]Fatal Error:[/bold red] An unexpected error occurred.")


if __name__ == "__main__":
    main()
