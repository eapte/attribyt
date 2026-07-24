import typer
import sys
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm, IntPrompt
from attribution.connector_csv import CSVConnector
from attribution.connectors.postgres import PostgresConnector
from attribution.connectors.clickhouse import ClickHouseConnector
from attribution.journey import build_journeys
from attribution.markov import markov_attribution, calculate_last_click
from attribution.metrics import compute_metrics
import plotly.graph_objects as go
from collections import Counter

app = typer.Typer()
console = Console()

def execute_attribution(config: dict):
    source = config["source"]
    file = config.get("file")
    dsn = config.get("dsn")
    host = config.get("host")
    port = config.get("port", 8123)
    user = config.get("user", "default")
    password = config.get("password", "")
    query = config.get("query")
    table = config.get("table", "events")
    model = config.get("model", "both")
    user_col = config.get("user_col", "user_id")
    timestamp_col = config.get("timestamp_col", "timestamp")
    channel_col = config.get("channel_col", "channel")
    event_col = config.get("event_col", "event_type")
    revenue_col = config.get("revenue_col", "revenue")
    start_date = config.get("start_date")
    end_date = config.get("end_date")
    sankey = config.get("sankey", False)

    connector_config = {}
    if source == "csv":
        if not file:
            raise ValueError("--file is required for csv source")
        connector_config["file_path"] = file
    elif source == "postgres":
        if not dsn:
            raise ValueError("--dsn is required for postgres source")
        connector_config["dsn"] = dsn
        connector_config["query"] = query
        connector_config["table"] = table
    elif source == "clickhouse":
        connector_config["host"] = host
        connector_config["port"] = port
        connector_config["user"] = user
        connector_config["password"] = password
        connector_config["query"] = query
        connector_config["table"] = table
    else:
        raise ValueError("Unsupported source")

    if source == "csv":
        connector = CSVConnector(connector_config)
    elif source == "postgres":
        connector = PostgresConnector(connector_config)
    elif source == "clickhouse":
        connector = ClickHouseConnector(connector_config)
    else:
        raise ValueError("Unsupported source")

    df = connector.fetch(start_date, end_date)

    mapping = {
        user_col: "user_id",
        timestamp_col: "timestamp",
        channel_col: "channel",
        event_col: "event_type",
        revenue_col: "revenue"
    }
    for old_col in mapping.keys():
        if old_col not in df.columns:
            raise ValueError(f"Column '{old_col}' not found in data")
    df = df.rename(mapping)

    journeys = build_journeys(df)
    total_revenue = journeys["total_revenue"].sum()

    metrics = compute_metrics(journeys)
    console.print(Panel.fit(
        f"Total users: {metrics['total_users']} | Total touches: {metrics['total_touches']} | Avg revenue per user: {metrics['avg_revenue_per_user']:.2f}",
        title="Summary"
    ))

    result_lc = calculate_last_click(journeys, total_revenue) if model in ("last-click", "both") else None
    result_markov = markov_attribution(journeys, total_revenue) if model in ("markov", "both") else None

    table = Table(title="Attribution Comparison", show_header=True, header_style="bold magenta")
    table.add_column("Channel", style="cyan")
    if model in ("last-click", "both"):
        table.add_column("Last-Click", style="green", justify="right")
    if model in ("markov", "both"):
        table.add_column("Markov", style="yellow", justify="right")
    if model == "both":
        table.add_column("Delta (M - LC)", style="red", justify="right")
    table.add_column("Share (M)", style="blue", justify="right")

    channels = set()
    if result_markov:
        channels.update(result_markov.keys())
    if result_lc:
        channels.update(result_lc.keys())
    channels = sorted(channels)

    for ch in channels:
        row = [ch]
        if model in ("last-click", "both"):
            lc_val = result_lc.get(ch, 0.0) if result_lc else 0.0
            row.append(f"{lc_val:.2f}")
        if model in ("markov", "both"):
            markov_val = result_markov.get(ch, 0.0) if result_markov else 0.0
            row.append(f"{markov_val:.2f}")
        if model == "both" and result_lc and result_markov:
            delta = result_markov.get(ch, 0.0) - result_lc.get(ch, 0.0)
            row.append(f"{delta:+.2f}")
        share = (result_markov.get(ch, 0.0) / total_revenue * 100) if result_markov and total_revenue else 0.0
        row.append(f"{share:.1f}%")
        table.add_row(*row)

    console.print(table)

    if sankey:
        all_journeys = journeys["journey"].to_list()
        nodes = set()
        links = []
        for journey in all_journeys:
            chain = ["START"] + journey + ["CONVERSION"]
            for i in range(len(chain)-1):
                src = chain[i]
                tgt = chain[i+1]
                nodes.add(src)
                nodes.add(tgt)
                links.append((src, tgt))
        link_counter = Counter(links)
        node_list = list(nodes)
        node_indices = {node: idx for idx, node in enumerate(node_list)}
        sources = [node_indices[src] for src, tgt in link_counter.keys()]
        targets = [node_indices[tgt] for src, tgt in link_counter.keys()]
        values = list(link_counter.values())
        fig = go.Figure(data=[go.Sankey(
            node=dict(label=node_list, pad=15, thickness=20),
            link=dict(source=sources, target=targets, value=values)
        )])
        fig.update_layout(title_text="User Journey Sankey Diagram", font_size=12)
        fig.write_html("sankey.html")
        console.print("[bold green]Sankey diagram saved to sankey.html[/]")

def interactive_mode():
    console.print(Panel.fit(
        "[bold cyan]Attribyt Interactive Setup[/]\n"
        "Answer a few questions, and we'll run the attribution analysis for you.",
        title="🚀 Hello"
    ))

    source = Prompt.ask(
        "Choose data source",
        choices=["csv", "postgres", "clickhouse"],
        default="csv"
    )

    config = {"source": source}

    if source == "csv":
        file = Prompt.ask("Path to CSV file", default="test_data.csv")
        config["file"] = file
    elif source == "postgres":
        dsn = Prompt.ask("PostgreSQL DSN", default="postgresql://user:pass@localhost/db")
        config["dsn"] = dsn
        query = Prompt.ask("SQL query", default="SELECT * FROM events")
        config["query"] = query
    elif source == "clickhouse":
        host = Prompt.ask("ClickHouse host", default="localhost")
        port = IntPrompt.ask("ClickHouse port", default=8123)
        user = Prompt.ask("ClickHouse user", default="default")
        password = Prompt.ask("ClickHouse password", password=True)
        query = Prompt.ask("SQL query", default="SELECT * FROM events")
        config.update({"host": host, "port": port, "user": user, "password": password, "query": query})

    console.print("\n[bold]Column mapping[/] — tell us which columns contain the required data.")
    user_col = Prompt.ask("Column for user ID", default="user_id")
    timestamp_col = Prompt.ask("Column for timestamp", default="timestamp")
    channel_col = Prompt.ask("Column for channel", default="channel")
    event_col = Prompt.ask("Column for event type", default="event_type")
    revenue_col = Prompt.ask("Column for revenue", default="revenue")
    config.update({
        "user_col": user_col,
        "timestamp_col": timestamp_col,
        "channel_col": channel_col,
        "event_col": event_col,
        "revenue_col": revenue_col
    })

    model = Prompt.ask(
        "Attribution model",
        choices=["markov", "last-click", "both"],
        default="both"
    )
    config["model"] = model

    sankey = Confirm.ask("Generate Sankey diagram?", default=True)
    config["sankey"] = sankey

    start = Prompt.ask("Start date (YYYY-MM-DD, leave empty for all)", default="")
    end = Prompt.ask("End date (YYYY-MM-DD, leave empty for all)", default="")
    if start:
        config["start_date"] = start
    if end:
        config["end_date"] = end

    console.print("\n[bold green]Running attribution with your settings...[/]\n")
    try:
        execute_attribution(config)
    except Exception as e:
        console.print(f"[red]Error: {e}[/]")
        console.print("[yellow]Please check your input and try again.[/]")

@app.command()
def run(
    source: str = typer.Option("csv", "--from", help="Data source: csv, postgres, clickhouse"),
    file: str = typer.Option(None, "--file", help="Path to CSV file (for csv source)"),
    dsn: str = typer.Option(None, "--dsn", help="PostgreSQL DSN (for postgres source)"),
    host: str = typer.Option(None, "--host", help="ClickHouse host"),
    port: int = typer.Option(8123, "--port", help="ClickHouse port"),
    user: str = typer.Option("default", "--user", help="ClickHouse user"),
    password: str = typer.Option("", "--password", help="ClickHouse password"),
    query: str = typer.Option(None, "--query", help="SQL query to fetch data"),
    table: str = typer.Option("events", "--table", help="Table name (if no query)"),
    model: str = typer.Option("both", "--model", help="Model: markov, last-click, both"),
    user_col: str = typer.Option("user_id", "--user-col", help="Column name for user ID"),
    timestamp_col: str = typer.Option("timestamp", "--timestamp-col", help="Column name for timestamp"),
    channel_col: str = typer.Option("channel", "--channel-col", help="Column name for channel"),
    event_col: str = typer.Option("event_type", "--event-col", help="Column name for event type"),
    revenue_col: str = typer.Option("revenue", "--revenue-col", help="Column name for revenue"),
    start_date: str = typer.Option(None, "--start", help="Start date (YYYY-MM-DD)"),
    end_date: str = typer.Option(None, "--end", help="End date (YYYY-MM-DD)"),
    sankey: bool = typer.Option(False, "--sankey", help="Generate Sankey diagram (HTML)")
):
    config = {
        "source": source,
        "file": file,
        "dsn": dsn,
        "host": host,
        "port": port,
        "user": user,
        "password": password,
        "query": query,
        "table": table,
        "model": model,
        "user_col": user_col,
        "timestamp_col": timestamp_col,
        "channel_col": channel_col,
        "event_col": event_col,
        "revenue_col": revenue_col,
        "start_date": start_date,
        "end_date": end_date,
        "sankey": sankey
    }
    try:
        execute_attribution(config)
    except Exception as e:
        console.print(f"[red]Error: {e}[/]")
        raise typer.Exit(code=1)

def show_help():
    console.print(Panel.fit(
        "[bold cyan]Attribyt[/] — privacy-first attribution engine\n\n"
        "📊 [yellow]Run attribution analysis[/] on CSV, PostgreSQL or ClickHouse.\n\n"
        "[green]Quick start with interactive mode:[/]\n"
        "  python main.py\n\n"
        "[green]Command-line mode:[/]\n"
        "  python main.py --from csv --file test_data.csv --model both --sankey\n\n"
        "[green]Custom column mapping:[/]\n"
        "  python main.py --from csv --file my_data.csv \\\n"
        "    --user-col client_id --timestamp-col event_time \\\n"
        "    --channel-col traffic_source --event-col action \\\n"
        "    --revenue-col amount --model both --sankey\n\n"
        "[blue]See all options:[/] python main.py --help",
        title="🚀 Hello"
    ))

if __name__ == "__main__":
    if len(sys.argv) == 1:
        interactive_mode()
    else:
        app()