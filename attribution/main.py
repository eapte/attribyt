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
from attribution.markov import markov_attribution, calculate_last_click, calculate_linear, calculate_time_decay
from attribution.metrics import compute_metrics
import plotly.graph_objects as go
from collections import Counter
import polars as pl

app = typer.Typer()
console = Console()


def print_interpretation(results: dict, total_revenue: float):
    if not results:
        return
    
    sorted_channels = sorted(results.items(), key=lambda x: x[1], reverse=True)
    
    console.print("\n[bold cyan]Interpretation[/]")
    console.print("-" * 50)
    
    for i, (ch, value) in enumerate(sorted_channels):
        share = (value / total_revenue * 100) if total_revenue else 0
        if i == 0:
            console.print(f"[bold green]Top channel:[/] {ch} — {share:.1f}% of total value (${value:,.2f})")
        elif i == len(sorted_channels) - 1:
            console.print(f"[bold red]Lowest channel:[/] {ch} — {share:.1f}% of total value (${value:,.2f})")
        else:
            bar = "█" * int(share / 2)
            console.print(f"  {ch:15} {bar} {share:.1f}%  (${value:,.2f})")
    
    console.print("-" * 50)
    console.print("[italic]Channels at the top are critical for driving conversions. "
                  "Consider allocating more budget there.[/]\n")


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
    export = config.get("export")

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

    if df.is_empty():
        console.print("[red]Error: No data found[/]")
        return

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

    if df['revenue'].null_count() > 0:
        df = df.with_columns(df['revenue'].fill_null(0))

    journeys = build_journeys(df)
    
    if journeys.is_empty():
        console.print("[red]Error: No journeys found[/]")
        return

    total_revenue = journeys["total_revenue"].sum()

    metrics = compute_metrics(journeys)
    console.print(Panel.fit(
        f"[bold]Total users:[/] {metrics['total_users']} | "
        f"[bold]Total touches:[/] {metrics['total_touches']} | "
        f"[bold]Converted:[/] {metrics['conversion_users']} users ({metrics['conversion_rate']:.1f}%) | "
        f"[bold]Non-converted:[/] {metrics['non_conversion_users']} users | "
        f"[bold]Avg revenue/user:[/] ${metrics['avg_revenue_per_converting_user']:,.2f} | "
        f"[bold]Total revenue:[/] ${total_revenue:,.2f}",
        title="Summary"
    ))

    results = {}
    
    if model in ("last-click", "both"):
        results["last_click"] = calculate_last_click(journeys, total_revenue)
    
    if model in ("linear", "both"):
        results["linear"] = calculate_linear(journeys, total_revenue)
    
    if model in ("time-decay", "both"):
        results["time_decay"] = calculate_time_decay(journeys, total_revenue)
    
    if model in ("markov", "both"):
        results["markov"] = markov_attribution(journeys, total_revenue)
    
    for key in results:
        if results[key]:
            total = sum(results[key].values())
            if total > 0 and total != total_revenue:
                for ch in results[key]:
                    results[key][ch] = (results[key][ch] / total) * total_revenue

    table = Table(title="Attribution Comparison", show_header=True, header_style="bold magenta")
    table.add_column("Channel", style="cyan")
    
    model_order = []
    if "last_click" in results:
        table.add_column("Last-Click", style="green", justify="right")
        model_order.append("last_click")
    if "linear" in results:
        table.add_column("Linear", style="blue", justify="right")
        model_order.append("linear")
    if "time_decay" in results:
        table.add_column("Time Decay", style="cyan", justify="right")
        model_order.append("time_decay")
    if "markov" in results:
        table.add_column("Markov", style="yellow", justify="right")
        model_order.append("markov")
    
    if len(model_order) >= 2:
        table.add_column("Delta", style="red", justify="right")
    
    all_channels = set()
    for key in results:
        all_channels.update(results[key].keys())
    all_channels = sorted(all_channels)

    for ch in all_channels:
        row = [ch]
        values = []
        for key in model_order:
            val = results[key].get(ch, 0.0)
            row.append(f"{val:,.2f}")
            values.append(val)
        
        if len(values) >= 2:
            delta = values[-1] - values[0]
            row.append(f"{delta:+,.2f}")
        
        table.add_row(*row)

    console.print(table)

    if "markov" in results:
        print_interpretation(results["markov"], total_revenue)
    elif "last_click" in results:
        print_interpretation(results["last_click"], total_revenue)

    if export:
        export_df = pl.DataFrame({
            "channel": list(all_channels),
            **{key: [results[key].get(ch, 0.0) for ch in all_channels] for key in results}
        })
        export_df.write_csv(export)
        console.print(f"[bold green]Results exported to {export}[/]")

    if sankey:
        all_journeys = journeys["journey"].to_list()
        nodes = set()
        links = []
        for journey in all_journeys:
            chain = ["START"] + journey + ["CONVERSION"]
            for i in range(len(chain) - 1):
                src = chain[i]
                tgt = chain[i + 1]
                nodes.add(src)
                nodes.add(tgt)
                links.append((src, tgt))
        
        link_counter = Counter(links)
        node_list = list(nodes)
        node_indices = {node: idx for idx, node in enumerate(node_list)}
        
        sources = [node_indices[src] for src, _ in link_counter.keys()]
        targets = [node_indices[tgt] for _, tgt in link_counter.keys()]
        values = list(link_counter.values())
        
        fig = go.Figure(data=[go.Sankey(
            node=dict(label=node_list, pad=15, thickness=20),
            link=dict(source=sources, target=targets, value=values)
        )])
        fig.update_layout(title_text="User Journey Sankey Diagram", font_size=12)
        fig.write_html("sankey.html")
        console.print("[bold green]Sankey diagram saved to sankey.html[/]")

    if not sankey and not export:
        console.print("[italic]Tip: Use --sankey to generate a visual diagram, or --export results.csv[/]")


def interactive_mode():
    console.print(Panel.fit(
        "[bold cyan]Attribyt Interactive Setup[/]\n"
        "Answer a few questions, and we'll run the attribution analysis for you.",
        title="Hello"
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
    config["user_col"] = Prompt.ask("Column for user ID", default="user_id")
    config["timestamp_col"] = Prompt.ask("Column for timestamp", default="timestamp")
    config["channel_col"] = Prompt.ask("Column for channel", default="channel")
    config["event_col"] = Prompt.ask("Column for event type", default="event_type")
    config["revenue_col"] = Prompt.ask("Column for revenue", default="revenue")

    model = Prompt.ask(
        "Attribution model",
        choices=["markov", "last-click", "linear", "time-decay", "both"],
        default="both"
    )
    config["model"] = model

    config["sankey"] = Confirm.ask("Generate Sankey diagram?", default=True)
    export = Prompt.ask("Export results to CSV? (leave empty to skip)", default="")
    if export:
        config["export"] = export

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
    model: str = typer.Option("both", "--model", help="Model: markov, last-click, linear, time-decay, both"),
    user_col: str = typer.Option("user_id", "--user-col", help="Column name for user ID"),
    timestamp_col: str = typer.Option("timestamp", "--timestamp-col", help="Column name for timestamp"),
    channel_col: str = typer.Option("channel", "--channel-col", help="Column name for channel"),
    event_col: str = typer.Option("event_type", "--event-col", help="Column name for event type"),
    revenue_col: str = typer.Option("revenue", "--revenue-col", help="Column name for revenue"),
    start_date: str = typer.Option(None, "--start", help="Start date (YYYY-MM-DD)"),
    end_date: str = typer.Option(None, "--end", help="End date (YYYY-MM-DD)"),
    sankey: bool = typer.Option(False, "--sankey", help="Generate Sankey diagram (HTML)"),
    export: str = typer.Option(None, "--export", help="Export results to CSV file")
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
        "sankey": sankey,
        "export": export
    }
    try:
        execute_attribution(config)
    except Exception as e:
        console.print(f"[red]Error: {e}[/]")
        raise typer.Exit(code=1)


def cli():
    if len(sys.argv) == 1:
        interactive_mode()
    else:
        app()


if __name__ == "__main__":
    cli()