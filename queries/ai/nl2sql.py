"""
Natural Language → Presto SQL via local LLM (Ollama).

Sends table schema metadata to a local model with the user's question.
The model returns valid Presto SQL. The script runs the SQL against
Trino and displays results.

PM angle (ADR-004): Schema-rich formats like Parquet give LLMs
enough context to generate accurate SQL. CSV headers can't do this.

Uses IBM Granite 4.0 via Ollama — fully local, no API keys needed.
"""
import json
import subprocess
import sys
import urllib.request


OLLAMA_MODEL = "sam860/granite-4.0:7b"

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


def generate_sql(question: str) -> str:
    """Send question + schema to local Ollama model, get back Presto SQL."""
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
        "http://localhost:11434/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        result = json.loads(resp.read())

    sql = result["response"].strip()
    # Remove markdown code fences if present
    if sql.startswith('```'):
        sql = '\n'.join(sql.split('\n')[1:])
    if sql.endswith('```'):
        sql = '\n'.join(sql.split('\n')[:-1])
    return sql.strip()


def run_query(sql: str) -> str:
    """Execute SQL against Trino via docker exec."""
    result = subprocess.run(
        ['docker', 'exec', 'muwalah-trino', 'trino', '--execute', sql],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode != 0:
        return f"ERROR: {result.stderr}"
    return result.stdout


def main():
    if len(sys.argv) > 1:
        question = ' '.join(sys.argv[1:])
    else:
        question = input("Ask a question about the data: ")

    print(f"\nQuestion: {question}")
    print(f"Model: {OLLAMA_MODEL}")
    print("\nGenerating SQL...")
    sql = generate_sql(question)
    print(f"\nGenerated SQL:\n{sql}")

    print("\nRunning query...")
    results = run_query(sql)
    print(f"\nResults:\n{results}")


if __name__ == '__main__':
    main()
