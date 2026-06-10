"""
Load Parquet data into Trino managed tables.

Creates schema and tables, then inserts data in batches
using the trino Python client. Tables are stored as Parquet
internally by Trino.

Usage:
    python3 scripts/load_data.py
"""
import os
import sys
import time
import trino
import pyarrow.parquet as pq
import pandas as pd

PARQUET_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'parquet')
BATCH_SIZE = 500


def get_connection():
    return trino.dbapi.connect(
        host='localhost', port=8080,
        user='trino', catalog='muwalah', schema='main'
    )


def wait_for_trino():
    print("Waiting for Trino to be ready...")
    for i in range(30):
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT 1")
            cur.fetchone()
            cur.close()
            conn.close()
            print("Trino is ready.")
            return
        except Exception:
            time.sleep(2)
    print("ERROR: Trino did not become ready in 60 seconds.")
    sys.exit(1)


def execute(cur, sql):
    cur.execute(sql)
    try:
        cur.fetchone()
    except trino.exceptions.TrinoUserError:
        pass


def insert_batch(cur, table, columns, rows):
    """Insert a batch of rows using VALUES syntax."""
    if not rows:
        return
    placeholders = ', '.join(['?'] * len(columns))
    sql = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"
    for row in rows:
        cur.execute(sql, row)
        cur.fetchone()


def insert_dataframe(cur, table, df, columns):
    """Insert a DataFrame into a Trino table in batches."""
    total = len(df)
    inserted = 0
    for start in range(0, total, BATCH_SIZE):
        batch = df.iloc[start:start + BATCH_SIZE]
        values_list = []
        for _, row in batch.iterrows():
            vals = []
            for col in columns:
                v = row[col]
                if pd.isna(v):
                    vals.append('NULL')
                elif isinstance(v, str):
                    vals.append("'" + v.replace("'", "''") + "'")
                elif isinstance(v, (pd.Timestamp,)):
                    vals.append(f"TIMESTAMP '{v}'")
                else:
                    vals.append(str(v))
            values_list.append('(' + ', '.join(vals) + ')')

        values_sql = ', '.join(values_list)
        sql = f"INSERT INTO {table} ({', '.join(columns)}) VALUES {values_sql}"
        cur.execute(sql)
        cur.fetchone()
        inserted += len(batch)
        pct = inserted * 100 // total
        print(f"  {inserted:,}/{total:,} rows ({pct}%)", end='\r')
    print()


def load_sellers(cur):
    print("Loading sellers...")
    execute(cur, "DROP TABLE IF EXISTS sellers")
    execute(cur, """
        CREATE TABLE sellers (
            seller_id VARCHAR,
            seller_zip_code_prefix VARCHAR,
            seller_city VARCHAR,
            seller_state VARCHAR,
            geolocation_lat DOUBLE,
            geolocation_lng DOUBLE
        ) WITH (format = 'PARQUET')
    """)
    df = pq.read_table(os.path.join(PARQUET_DIR, 'sellers')).to_pandas()
    cols = ['seller_id', 'seller_zip_code_prefix', 'seller_city',
            'seller_state', 'geolocation_lat', 'geolocation_lng']
    insert_dataframe(cur, 'sellers', df, cols)
    print(f"  sellers: {len(df):,} rows loaded")


def load_customers(cur):
    print("Loading customers...")
    execute(cur, "DROP TABLE IF EXISTS customers")
    execute(cur, """
        CREATE TABLE customers (
            customer_id VARCHAR,
            customer_unique_id VARCHAR,
            customer_zip_code_prefix VARCHAR,
            customer_city VARCHAR,
            customer_state VARCHAR,
            geolocation_lat DOUBLE,
            geolocation_lng DOUBLE
        ) WITH (format = 'PARQUET')
    """)
    df = pq.read_table(os.path.join(PARQUET_DIR, 'customers')).to_pandas()
    cols = ['customer_id', 'customer_unique_id', 'customer_zip_code_prefix',
            'customer_city', 'customer_state', 'geolocation_lat', 'geolocation_lng']
    insert_dataframe(cur, 'customers', df, cols)
    print(f"  customers: {len(df):,} rows loaded")


def load_products(cur):
    print("Loading products...")
    execute(cur, "DROP TABLE IF EXISTS products")
    execute(cur, """
        CREATE TABLE products (
            product_id VARCHAR,
            category_portuguese VARCHAR,
            category_english VARCHAR,
            weight_g DOUBLE,
            length_cm DOUBLE,
            height_cm DOUBLE,
            width_cm DOUBLE,
            product_name_length DOUBLE,
            product_description_length DOUBLE,
            product_photos_qty DOUBLE
        ) WITH (format = 'PARQUET')
    """)
    df = pq.read_table(os.path.join(PARQUET_DIR, 'products')).to_pandas()
    # Flatten nested structs
    df['category_portuguese'] = df['category'].apply(lambda x: x['portuguese'] if x else None)
    df['category_english'] = df['category'].apply(lambda x: x['english'] if x else None)
    df['weight_g'] = df['dimensions'].apply(lambda x: x['weight_g'] if x else None)
    df['length_cm'] = df['dimensions'].apply(lambda x: x['length_cm'] if x else None)
    df['height_cm'] = df['dimensions'].apply(lambda x: x['height_cm'] if x else None)
    df['width_cm'] = df['dimensions'].apply(lambda x: x['width_cm'] if x else None)
    cols = ['product_id', 'category_portuguese', 'category_english',
            'weight_g', 'length_cm', 'height_cm', 'width_cm',
            'product_name_length', 'product_description_length', 'product_photos_qty']
    insert_dataframe(cur, 'products', df, cols)
    print(f"  products: {len(df):,} rows loaded")


def load_reviews(cur):
    print("Loading reviews...")
    execute(cur, "DROP TABLE IF EXISTS reviews")
    execute(cur, """
        CREATE TABLE reviews (
            review_id VARCHAR,
            order_id VARCHAR,
            review_comment_title VARCHAR,
            review_comment_message VARCHAR,
            review_creation_date TIMESTAMP,
            review_answer_timestamp TIMESTAMP,
            review_score INTEGER
        ) WITH (
            format = 'PARQUET',
            partitioned_by = ARRAY['review_score']
        )
    """)
    df = pq.read_table(os.path.join(PARQUET_DIR, 'reviews')).to_pandas()
    df['review_creation_date'] = pd.to_datetime(df['review_creation_date'])
    df['review_answer_timestamp'] = pd.to_datetime(df['review_answer_timestamp'])
    cols = ['review_id', 'order_id', 'review_comment_title',
            'review_comment_message', 'review_creation_date',
            'review_answer_timestamp', 'review_score']
    insert_dataframe(cur, 'reviews', df, cols)
    print(f"  reviews: {len(df):,} rows loaded")


def load_orders(cur):
    print("Loading orders...")
    execute(cur, "DROP TABLE IF EXISTS orders")
    execute(cur, """
        CREATE TABLE orders (
            order_id VARCHAR,
            customer_id VARCHAR,
            order_status VARCHAR,
            order_purchase_timestamp TIMESTAMP,
            order_approved_at TIMESTAMP,
            order_delivered_carrier_date TIMESTAMP,
            order_delivered_customer_date TIMESTAMP,
            order_estimated_delivery_date TIMESTAMP,
            order_item_id DOUBLE,
            product_id VARCHAR,
            seller_id VARCHAR,
            shipping_limit_date TIMESTAMP,
            price DOUBLE,
            freight_value DOUBLE,
            payment_type VARCHAR,
            payment_installments DOUBLE,
            payment_value DOUBLE,
            year INTEGER,
            month INTEGER
        ) WITH (
            format = 'PARQUET',
            partitioned_by = ARRAY['year', 'month']
        )
    """)
    df = pq.read_table(os.path.join(PARQUET_DIR, 'orders')).to_pandas()
    for col in ['order_purchase_timestamp', 'order_approved_at',
                'order_delivered_carrier_date', 'order_delivered_customer_date',
                'order_estimated_delivery_date', 'shipping_limit_date']:
        df[col] = pd.to_datetime(df[col])
    df['year'] = df['year'].astype(int)
    df['month'] = df['month'].astype(int)
    cols = ['order_id', 'customer_id', 'order_status',
            'order_purchase_timestamp', 'order_approved_at',
            'order_delivered_carrier_date', 'order_delivered_customer_date',
            'order_estimated_delivery_date',
            'order_item_id', 'product_id', 'seller_id',
            'shipping_limit_date', 'price', 'freight_value',
            'payment_type', 'payment_installments', 'payment_value',
            'year', 'month']
    insert_dataframe(cur, 'orders', df, cols)
    print(f"  orders: {len(df):,} rows loaded")


def verify(cur):
    print("\nVerifying row counts...")
    for table in ['sellers', 'customers', 'products', 'reviews', 'orders']:
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        count = cur.fetchone()[0]
        print(f"  {table}: {count:,} rows")


def main():
    wait_for_trino()

    conn = get_connection()
    cur = conn.cursor()

    # Create schema
    print("Creating schema...")
    execute(cur, "CREATE SCHEMA IF NOT EXISTS muwalah.main")

    # Load tables (smallest first for fast feedback)
    load_sellers(cur)
    load_products(cur)
    load_customers(cur)
    load_reviews(cur)
    load_orders(cur)

    verify(cur)

    cur.close()
    conn.close()
    print("\nDone! All tables loaded into Trino.")


if __name__ == '__main__':
    main()
