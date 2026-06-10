#!/bin/bash
# Initialize Trino tables from Parquet data.
# Run after docker compose up.

set -e

echo "Loading data into Trino..."
python3 scripts/load_data.py

echo ""
echo "Testing a sample query..."
docker exec muwalah-trino trino --execute "
    SELECT customer_state, COUNT(*) as order_count
    FROM muwalah.main.orders o
    JOIN muwalah.main.customers c ON o.customer_id = c.customer_id
    GROUP BY customer_state
    ORDER BY order_count DESC
    LIMIT 5
"

echo ""
echo "Setup complete! Trino is ready for queries."
