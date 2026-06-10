"""
Muwalah Commerce — Interactive NL-to-SQL Terminal.

Single command to bootstrap the full analytics stack and drop into
an English-language query prompt powered by IBM Granite via Ollama.

Usage:
    python3 muwalah.py
"""
import csv
import io
import json
import subprocess
import sys
import time
import urllib.request
import urllib.error

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

console = Console()

OLLAMA_MODEL = "sam860/granite-4.0:7b"
OLLAMA_URL = "http://localhost:11434"

SCHEMA_CONTEXT = """
Trino SQL database 'muwalah.main' with these tables:

Table: muwalah.main.orders (partitioned by year, month)
  order_id VARCHAR, customer_id VARCHAR, order_status VARCHAR,
  order_purchase_timestamp TIMESTAMP, order_approved_at TIMESTAMP,
  order_delivered_carrier_date TIMESTAMP, order_delivered_customer_date TIMESTAMP,
  order_estimated_delivery_date TIMESTAMP, order_item_id DOUBLE,
  product_id VARCHAR, seller_id VARCHAR, shipping_limit_date TIMESTAMP,
  price DOUBLE, freight_value DOUBLE, payment_type VARCHAR,
  payment_installments DOUBLE, payment_value DOUBLE,
  year INTEGER, month INTEGER

Table: muwalah.main.products
  product_id VARCHAR, category_portuguese VARCHAR, category_english VARCHAR,
  weight_g DOUBLE, length_cm DOUBLE, height_cm DOUBLE, width_cm DOUBLE,
  product_name_length DOUBLE, product_description_length DOUBLE, product_photos_qty DOUBLE

Table: muwalah.main.customers
  customer_id VARCHAR, customer_unique_id VARCHAR, customer_zip_code_prefix VARCHAR,
  customer_city VARCHAR, customer_state VARCHAR, geolocation_lat DOUBLE, geolocation_lng DOUBLE

Table: muwalah.main.reviews (partitioned by review_score)
  review_id VARCHAR, order_id VARCHAR, review_comment_title VARCHAR,
  review_comment_message VARCHAR, review_creation_date TIMESTAMP,
  review_answer_timestamp TIMESTAMP, review_score INTEGER

Table: muwalah.main.sellers
  seller_id VARCHAR, seller_zip_code_prefix VARCHAR, seller_city VARCHAR,
  seller_state VARCHAR, geolocation_lat DOUBLE, geolocation_lng DOUBLE

Notes:
- Data is Brazilian e-commerce from 2016-2018
- Use Trino SQL syntax (DATE_DIFF, DATE_TRUNC, etc.)
- Use fully qualified table names (muwalah.main.tablename)
- orders.year and orders.month are partition columns (INTEGER)
- reviews.review_score is a partition column (INTEGER, 1-5)
"""


# --- Startup checks ---

def check_docker() -> bool:
    try:
        subprocess.run(
            ["docker", "info"],
            capture_output=True, timeout=10
        )
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def check_ollama() -> bool:
    try:
        req = urllib.request.Request(f"{OLLAMA_URL}/api/tags")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
        models = [m.get("name", "") for m in data.get("models", [])]
        return any(OLLAMA_MODEL in m for m in models)
    except Exception:
        return False


def ollama_running() -> bool:
    try:
        urllib.request.urlopen(f"{OLLAMA_URL}/api/tags", timeout=3)
        return True
    except Exception:
        return False


def start_trino() -> bool:
    subprocess.run(
        ["docker", "compose", "up", "-d"],
        capture_output=True, timeout=30
    )
    for _ in range(60):
        try:
            result = subprocess.run(
                ["docker", "exec", "muwalah-trino", "trino", "--execute", "SELECT 1"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                return True
        except subprocess.SubprocessError:
            pass
        time.sleep(2)
    return False


def check_tables() -> int:
    result = subprocess.run(
        ["docker", "exec", "muwalah-trino", "trino", "--execute",
         "SHOW TABLES FROM muwalah.main"],
        capture_output=True, text=True, timeout=15
    )
    if result.returncode != 0:
        return 0
    tables = [line.strip().strip('"') for line in result.stdout.strip().split("\n") if line.strip()]
    return len(tables)


def load_data():
    """Load data into Trino using the existing load_data.py script."""
    sys.path.insert(0, "scripts")
    import load_data
    load_data.main()
    sys.path.pop(0)


# --- NL-to-SQL ---

def generate_sql(question: str) -> str:
    prompt = f"""Given this database schema:

{SCHEMA_CONTEXT}

Write a Presto SQL query to answer this question:
"{question}"

Return ONLY the SQL query, no explanation. Use fully qualified table names (muwalah.main.tablename)."""

    payload = json.dumps({
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0}
    }).encode()

    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        result = json.loads(resp.read())

    sql = result["response"].strip()
    if sql.startswith("```"):
        sql = "\n".join(sql.split("\n")[1:])
    if sql.endswith("```"):
        sql = "\n".join(sql.split("\n")[:-1])
    return sql.strip()


def run_query(sql: str) -> str:
    result = subprocess.run(
        ["docker", "exec", "muwalah-trino", "trino", "--execute", sql],
        capture_output=True, text=True, timeout=60
    )
    if result.returncode != 0:
        return f"ERROR: {result.stderr.strip()}"
    return result.stdout.strip()


def display_results(raw: str):
    if not raw or raw.startswith("ERROR:"):
        console.print(f"  [red]{raw}[/red]")
        return

    lines = [line for line in raw.split("\n") if line.strip()]
    if not lines:
        console.print("  [dim]No results[/dim]")
        return

    # Trino --execute outputs CSV: "val1","val2"
    reader = csv.reader(io.StringIO(raw))
    rows = [row for row in reader if row]
    if not rows:
        console.print("  [dim]No results[/dim]")
        return

    num_cols = len(rows[0])
    table = Table(show_header=False, box=None, padding=(0, 2))
    for _ in range(num_cols):
        table.add_column()
    for row in rows:
        table.add_row(*row)

    console.print()
    console.print(table)


# --- Main ---

def startup() -> bool:
    console.print()
    console.print(Panel(
        "[bold]Muwalah Commerce[/bold]\nAnalytics Modernization -- NL-to-SQL with Granite",
        expand=False
    ))
    console.print()

    # Docker
    with console.status("[bold]Checking Docker..."):
        docker_ok = check_docker()
    if not docker_ok:
        console.print("[red]x[/red] Docker Desktop is not running. Start it and try again.")
        return False
    console.print("[green]ok[/green] Docker is running")

    # Ollama
    with console.status("[bold]Checking Ollama..."):
        oll_running = ollama_running()
        model_ok = check_ollama() if oll_running else False
    if not oll_running:
        console.print("[red]x[/red] Ollama is not running. Install: https://ollama.com")
        return False
    if not model_ok:
        console.print(f"[red]x[/red] Granite model not found. Run: [bold]ollama pull {OLLAMA_MODEL}[/bold]")
        return False
    console.print(f"[green]ok[/green] Ollama is running ({OLLAMA_MODEL})")

    # Trino
    with console.status("[bold]Starting Trino..."):
        trino_ok = start_trino()
    if not trino_ok:
        console.print("[red]x[/red] Trino failed to start within 60 seconds.")
        return False
    console.print("[green]ok[/green] Trino is ready")

    # Tables
    with console.status("[bold]Checking tables..."):
        table_count = check_tables()
    if table_count < 5:
        console.print(f"[yellow]...[/yellow] Found {table_count} tables, loading data...")
        with console.status("[bold]Loading data into Trino (this takes a few minutes)..."):
            try:
                load_data()
            except Exception as e:
                console.print(f"[red]x[/red] Data load failed: {e}")
                return False
        console.print("[green]ok[/green] Tables loaded")
    else:
        console.print(f"[green]ok[/green] Tables loaded ({table_count} tables)")

    return True


def repl():
    console.print()
    console.print("[dim]Ask anything about the data. Type 'exit' to quit.[/dim]")
    console.print()

    while True:
        try:
            question = console.input("[bold cyan]muwalah ->[/bold cyan] ")
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]Goodbye.[/dim]")
            break

        question = question.strip()
        if not question:
            continue
        if question.lower() in ("exit", "quit"):
            console.print("[dim]Goodbye.[/dim]")
            break

        # Generate SQL
        with console.status("[bold]Generating SQL..."):
            try:
                sql = generate_sql(question)
            except Exception as e:
                console.print(f"  [red]Error generating SQL: {e}[/red]")
                console.print()
                continue

        console.print()
        console.print(Syntax(sql, "sql", theme="monokai", padding=1))

        # Run query
        with console.status("[bold]Running query..."):
            try:
                raw = run_query(sql)
            except subprocess.TimeoutExpired:
                console.print("  [red]Query timed out.[/red]")
                console.print()
                continue
            except Exception as e:
                console.print(f"  [red]Query error: {e}[/red]")
                console.print()
                continue

        display_results(raw)
        console.print()


def main():
    try:
        if startup():
            repl()
    except KeyboardInterrupt:
        console.print("\n[dim]Goodbye.[/dim]")


if __name__ == "__main__":
    main()
