from functions.holding_functions import HoldingsManager
from tools.generate_report import generate_portfolio_report as generate_pdf_report
import os
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.columns import Columns
from rich.prompt import Prompt
from mappings import currency_full_names

def generate_portfolio_report() -> str:
    """
    Generates a PDF report of user's portfolio.
    """
    console = Console()
    manager = HoldingsManager()

    console.print("Doing portfolio analysis...", style="dim italic")

    my_holdings = manager.list_holdings()

    if not my_holdings:
        console.print("[bold yellow]⚠️ Your portfolio is currently empty. Cannot generate a report.[/bold yellow]")
        return "Your portfolio is currently empty. Cannot generate a report."

    currency_list = currency_full_names

    currency_renderables = [f"[bold cyan]{code}[/bold cyan]: {name}" for code, name in currency_list.items()]
    
    console.print(
        Panel(
            Columns(currency_renderables, equal=True, expand=True),
            title="[bold]Select a Base Currency for the Report[/bold]",
            border_style="blue",
            padding=(1, 2)
        )
    )

    selected_currency = Prompt.ask(
        "Enter the 3-letter code for your desired currency",
        choices=list(currency_full_names.keys()),
        show_choices=False,
        show_default=False,
        default="USD"
    )

    console.print(f"\nGenerating report with base currency: [bold green]{selected_currency}[/bold green]...")

    folder = "reports"
    os.makedirs(folder, exist_ok=True)

    now = datetime.now()
    date_str = now.strftime("%d%m%Y")
    time_str = now.strftime("%H%M")

    filename = f"portfolio_report_{date_str}_{time_str}.pdf"
    output_pdf_path = os.path.join(folder, filename)

    generate_pdf_report(holdings=my_holdings, output_path=output_pdf_path, base_currency=selected_currency)

    success_message = f"✔ Report generated successfully!\n[dim]Saved to: {os.path.abspath(output_pdf_path)}[/dim]"
    console.print(Panel(success_message, style="green", title="[bold]Success[/bold]"))
    
    return "Report generated successfully!"


