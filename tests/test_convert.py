"""Verify Parquet conversion output: schemas, row counts, partitions, compression."""
import os
import pyarrow.parquet as pq
import pytest

PARQUET_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'parquet')


def test_orders_table_exists_and_partitioned():
    orders_dir = os.path.join(PARQUET_DIR, 'orders')
    assert os.path.isdir(orders_dir), "orders/ directory missing"
    subdirs = os.listdir(orders_dir)
    year_dirs = [d for d in subdirs if d.startswith('year=')]
    assert len(year_dirs) >= 2, f"Expected year partitions, got: {subdirs}"


def test_orders_row_count():
    dataset = pq.ParquetDataset(os.path.join(PARQUET_DIR, 'orders'))
    table = dataset.read()
    assert len(table) > 90_000, f"Expected >90K order rows, got {len(table)}"


def test_orders_has_expected_columns():
    dataset = pq.ParquetDataset(os.path.join(PARQUET_DIR, 'orders'))
    table = dataset.read()
    expected = {'order_id', 'customer_id', 'order_status', 'price', 'freight_value'}
    actual = set(table.column_names)
    assert expected.issubset(actual), f"Missing columns: {expected - actual}"


def test_products_has_nested_structs():
    table = pq.read_table(os.path.join(PARQUET_DIR, 'products'))
    assert 'dimensions' in table.column_names, "products missing 'dimensions' struct"
    assert 'category' in table.column_names, "products missing 'category' struct"
    dims_type = table.schema.field('dimensions').type
    assert hasattr(dims_type, 'num_fields'), f"dimensions should be struct, got {dims_type}"


def test_products_row_count():
    table = pq.read_table(os.path.join(PARQUET_DIR, 'products'))
    assert len(table) > 30_000, f"Expected >30K products, got {len(table)}"


def test_reviews_partitioned_by_score():
    reviews_dir = os.path.join(PARQUET_DIR, 'reviews')
    assert os.path.isdir(reviews_dir), "reviews/ directory missing"
    subdirs = os.listdir(reviews_dir)
    score_dirs = [d for d in subdirs if d.startswith('review_score=')]
    assert len(score_dirs) == 5, f"Expected 5 review_score partitions (1-5), got {score_dirs}"


def test_customers_row_count():
    table = pq.read_table(os.path.join(PARQUET_DIR, 'customers'))
    assert len(table) > 90_000, f"Expected >90K customers, got {len(table)}"


def test_sellers_row_count():
    table = pq.read_table(os.path.join(PARQUET_DIR, 'sellers'))
    assert len(table) > 2_000, f"Expected >2K sellers, got {len(table)}"


def test_orders_compression_is_snappy():
    orders_dir = os.path.join(PARQUET_DIR, 'orders')
    for root, dirs, files in os.walk(orders_dir):
        for f in files:
            if f.endswith('.parquet'):
                meta = pq.read_metadata(os.path.join(root, f))
                codec = meta.row_group(0).column(0).compression
                assert codec == 'SNAPPY', f"Expected SNAPPY, got {codec}"
                return
    pytest.fail("No parquet files found in orders/")


def test_customers_compression_is_zstd():
    customers_dir = os.path.join(PARQUET_DIR, 'customers')
    for f in os.listdir(customers_dir):
        if f.endswith('.parquet'):
            meta = pq.read_metadata(os.path.join(customers_dir, f))
            codec = meta.row_group(0).column(0).compression
            assert codec == 'ZSTD', f"Expected ZSTD, got {codec}"
            return
    pytest.fail("No parquet files found in customers/")
