"""
CSV → Parquet conversion pipeline for Olist e-commerce dataset.

Reads raw CSVs, joins related tables, applies schema decisions
(nested structs, partitioning, compression), and writes Parquet.

Partition strategy:
  - orders: year/month (date-range queries)
  - reviews: review_score (rating-tier queries)
  - products, customers, sellers: unpartitioned (small tables)

Compression:
  - Snappy: orders, reviews (fast decompression, frequent reads)
  - Zstd: customers (better ratio, less frequent reads)
  - Snappy: products, sellers (default, small tables)
"""
import os
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

RAW_DIR = os.path.join(os.path.dirname(__file__), 'raw')
PARQUET_DIR = os.path.join(os.path.dirname(__file__), 'parquet')


def read_csv(name: str) -> pd.DataFrame:
    return pd.read_csv(os.path.join(RAW_DIR, name))


def convert_orders():
    """Denormalize orders + items + payments → partitioned Parquet."""
    print("Converting orders...")
    orders = read_csv('olist_orders_dataset.csv')
    items = read_csv('olist_order_items_dataset.csv')
    payments = read_csv('olist_order_payments_dataset.csv')

    pay_agg = payments.groupby('order_id').agg(
        payment_type=('payment_type', 'first'),
        payment_installments=('payment_installments', 'max'),
        payment_value=('payment_value', 'sum')
    ).reset_index()

    df = orders.merge(items, on='order_id', how='left')
    df = df.merge(pay_agg, on='order_id', how='left')

    df['order_purchase_timestamp'] = pd.to_datetime(df['order_purchase_timestamp'])
    df['order_approved_at'] = pd.to_datetime(df['order_approved_at'])
    df['order_delivered_carrier_date'] = pd.to_datetime(df['order_delivered_carrier_date'])
    df['order_delivered_customer_date'] = pd.to_datetime(df['order_delivered_customer_date'])
    df['order_estimated_delivery_date'] = pd.to_datetime(df['order_estimated_delivery_date'])
    df['shipping_limit_date'] = pd.to_datetime(df['shipping_limit_date'])
    df['year'] = df['order_purchase_timestamp'].dt.year
    df['month'] = df['order_purchase_timestamp'].dt.month

    cols = [
        'order_id', 'customer_id', 'order_status',
        'order_purchase_timestamp', 'order_approved_at',
        'order_delivered_carrier_date', 'order_delivered_customer_date',
        'order_estimated_delivery_date',
        'order_item_id', 'product_id', 'seller_id',
        'shipping_limit_date', 'price', 'freight_value',
        'payment_type', 'payment_installments', 'payment_value',
        'year', 'month'
    ]
    df = df[cols]

    table = pa.Table.from_pandas(df)
    out = os.path.join(PARQUET_DIR, 'orders')
    pq.write_to_dataset(
        table, root_path=out,
        partition_cols=['year', 'month'],
        compression='snappy'
    )
    print(f"  → {len(df):,} rows → {out}")


def convert_products():
    """Products with nested dimension and category structs → Parquet."""
    print("Converting products...")
    products = read_csv('olist_products_dataset.csv')
    categories = read_csv('product_category_name_translation.csv')

    df = products.merge(categories, on='product_category_name', how='left')

    dimensions = pa.StructArray.from_arrays(
        [
            pa.array(df['product_weight_g'].values, type=pa.float64()),
            pa.array(df['product_length_cm'].values, type=pa.float64()),
            pa.array(df['product_height_cm'].values, type=pa.float64()),
            pa.array(df['product_width_cm'].values, type=pa.float64()),
        ],
        names=['weight_g', 'length_cm', 'height_cm', 'width_cm']
    )
    category = pa.StructArray.from_arrays(
        [
            pa.array(df['product_category_name'].where(df['product_category_name'].notna(), other=None).tolist(), type=pa.string()),
            pa.array(df['product_category_name_english'].where(df['product_category_name_english'].notna(), other=None).tolist(), type=pa.string()),
        ],
        names=['portuguese', 'english']
    )

    table = pa.table({
        'product_id': pa.array(df['product_id'].values, type=pa.string()),
        'category': category,
        'dimensions': dimensions,
        'product_name_length': pa.array(df['product_name_lenght'].values, type=pa.float64()),
        'product_description_length': pa.array(df['product_description_lenght'].values, type=pa.float64()),
        'product_photos_qty': pa.array(df['product_photos_qty'].values, type=pa.float64()),
    })

    out = os.path.join(PARQUET_DIR, 'products')
    os.makedirs(out, exist_ok=True)
    pq.write_table(table, os.path.join(out, 'part-0.parquet'), compression='snappy')
    print(f"  → {len(df):,} rows → {out}")


def convert_customers():
    """Customers + geolocation (deduplicated) → Parquet with Zstd."""
    print("Converting customers...")
    customers = read_csv('olist_customers_dataset.csv')
    geo = read_csv('olist_geolocation_dataset.csv')

    geo_agg = geo.groupby('geolocation_zip_code_prefix').agg(
        geolocation_lat=('geolocation_lat', 'mean'),
        geolocation_lng=('geolocation_lng', 'mean')
    ).reset_index()
    geo_agg['geolocation_zip_code_prefix'] = geo_agg['geolocation_zip_code_prefix'].astype(str)
    customers['customer_zip_code_prefix'] = customers['customer_zip_code_prefix'].astype(str)

    df = customers.merge(
        geo_agg,
        left_on='customer_zip_code_prefix',
        right_on='geolocation_zip_code_prefix',
        how='left'
    ).drop(columns=['geolocation_zip_code_prefix'])

    table = pa.Table.from_pandas(df)
    out = os.path.join(PARQUET_DIR, 'customers')
    os.makedirs(out, exist_ok=True)
    pq.write_table(table, os.path.join(out, 'part-0.parquet'), compression='zstd')
    print(f"  → {len(df):,} rows → {out}")


def convert_reviews():
    """Reviews → partitioned by review_score, Snappy compression."""
    print("Converting reviews...")
    df = read_csv('olist_order_reviews_dataset.csv')
    df['review_creation_date'] = pd.to_datetime(df['review_creation_date'])
    df['review_answer_timestamp'] = pd.to_datetime(df['review_answer_timestamp'])

    df['review_comment_title'] = df['review_comment_title'].fillna('')
    df['review_comment_message'] = df['review_comment_message'].fillna('')

    table = pa.Table.from_pandas(df)
    out = os.path.join(PARQUET_DIR, 'reviews')
    pq.write_to_dataset(
        table, root_path=out,
        partition_cols=['review_score'],
        compression='snappy'
    )
    print(f"  → {len(df):,} rows → {out}")


def convert_sellers():
    """Sellers + geolocation → Parquet."""
    print("Converting sellers...")
    sellers = read_csv('olist_sellers_dataset.csv')
    geo = read_csv('olist_geolocation_dataset.csv')

    geo_agg = geo.groupby('geolocation_zip_code_prefix').agg(
        geolocation_lat=('geolocation_lat', 'mean'),
        geolocation_lng=('geolocation_lng', 'mean')
    ).reset_index()
    geo_agg['geolocation_zip_code_prefix'] = geo_agg['geolocation_zip_code_prefix'].astype(str)
    sellers['seller_zip_code_prefix'] = sellers['seller_zip_code_prefix'].astype(str)

    df = sellers.merge(
        geo_agg,
        left_on='seller_zip_code_prefix',
        right_on='geolocation_zip_code_prefix',
        how='left'
    ).drop(columns=['geolocation_zip_code_prefix'])

    table = pa.Table.from_pandas(df)
    out = os.path.join(PARQUET_DIR, 'sellers')
    os.makedirs(out, exist_ok=True)
    pq.write_table(table, os.path.join(out, 'part-0.parquet'), compression='snappy')
    print(f"  → {len(df):,} rows → {out}")


def print_summary():
    """Print size comparison: raw CSV vs Parquet."""
    csv_size = sum(
        os.path.getsize(os.path.join(RAW_DIR, f))
        for f in os.listdir(RAW_DIR) if f.endswith('.csv')
    )
    parquet_size = 0
    for root, dirs, files in os.walk(PARQUET_DIR):
        for f in files:
            if f.endswith('.parquet'):
                parquet_size += os.path.getsize(os.path.join(root, f))

    print(f"\n{'='*50}")
    print(f"CSV total:     {csv_size / 1024 / 1024:.1f} MB")
    print(f"Parquet total: {parquet_size / 1024 / 1024:.1f} MB")
    print(f"Compression:   {(1 - parquet_size/csv_size)*100:.0f}% smaller")
    print(f"{'='*50}")


if __name__ == '__main__':
    import shutil
    if os.path.exists(PARQUET_DIR):
        shutil.rmtree(PARQUET_DIR)
    os.makedirs(PARQUET_DIR, exist_ok=True)

    convert_orders()
    convert_products()
    convert_customers()
    convert_reviews()
    convert_sellers()
    print_summary()
