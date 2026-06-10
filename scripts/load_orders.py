"""Load just the orders table into Trino with larger batches."""
import os
import sys
import trino
import pyarrow.parquet as pq
import pandas as pd

PARQUET_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'parquet')
BATCH_SIZE = 200  # smaller batches to avoid overwhelming Trino


def get_connection():
    return trino.dbapi.connect(
        host='localhost', port=8080,
        user='trino', catalog='muwalah', schema='main'
    )


def insert_dataframe(cur, table, df, columns):
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
                elif isinstance(v, pd.Timestamp):
                    vals.append(f"TIMESTAMP '{v}'")
                else:
                    vals.append(str(v))
            values_list.append('(' + ', '.join(vals) + ')')

        values_sql = ', '.join(values_list)
        sql = f"INSERT INTO {table} ({', '.join(columns)}) VALUES {values_sql}"
        try:
            cur.execute(sql)
            cur.fetchone()
        except Exception as e:
            print(f"\n  Error at row {inserted}: {e}")
            print(f"  Retrying with fresh connection...")
            cur.close()
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(sql)
            cur.fetchone()

        inserted += len(batch)
        pct = inserted * 100 // total
        print(f"  {inserted:,}/{total:,} rows ({pct}%)", end='\r')
    print()
    return cur


def main():
    conn = get_connection()
    cur = conn.cursor()

    print("Creating orders table...")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
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
    cur.fetchone()

    print("Loading orders...")
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

    cur = insert_dataframe(cur, 'orders', df, cols)

    print("Verifying...")
    cur.execute("SELECT COUNT(*) FROM orders")
    count = cur.fetchone()[0]
    print(f"  orders: {count:,} rows loaded")

    cur.close()
    conn.close()
    print("Done!")


if __name__ == '__main__':
    main()
