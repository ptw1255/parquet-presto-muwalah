-- Create schema
CREATE SCHEMA IF NOT EXISTS muwalah.main
WITH (location = 'file:///data/parquet');

-- Orders: partitioned by year/month
CREATE TABLE IF NOT EXISTS muwalah.main.orders (
    order_id VARCHAR,
    customer_id VARCHAR,
    order_status VARCHAR,
    order_purchase_timestamp TIMESTAMP,
    order_approved_at TIMESTAMP,
    order_delivered_carrier_date TIMESTAMP,
    order_delivered_customer_date TIMESTAMP,
    order_estimated_delivery_date TIMESTAMP,
    order_item_id BIGINT,
    product_id VARCHAR,
    seller_id VARCHAR,
    shipping_limit_date TIMESTAMP,
    price DOUBLE,
    freight_value DOUBLE,
    payment_type VARCHAR,
    payment_installments BIGINT,
    payment_value DOUBLE,
    year BIGINT,
    month BIGINT
) WITH (
    external_location = 'file:///data/parquet/orders',
    format = 'PARQUET',
    partitioned_by = ARRAY['year', 'month']
);

-- Sync order partitions
CALL muwalah.system.sync_partition_metadata('main', 'orders', 'FULL');

-- Products: nested structs
CREATE TABLE IF NOT EXISTS muwalah.main.products (
    product_id VARCHAR,
    category ROW(portuguese VARCHAR, english VARCHAR),
    dimensions ROW(weight_g DOUBLE, length_cm DOUBLE, height_cm DOUBLE, width_cm DOUBLE),
    product_name_length DOUBLE,
    product_description_length DOUBLE,
    product_photos_qty DOUBLE
) WITH (
    external_location = 'file:///data/parquet/products',
    format = 'PARQUET'
);

-- Customers: with geolocation
CREATE TABLE IF NOT EXISTS muwalah.main.customers (
    customer_id VARCHAR,
    customer_unique_id VARCHAR,
    customer_zip_code_prefix VARCHAR,
    customer_city VARCHAR,
    customer_state VARCHAR,
    geolocation_lat DOUBLE,
    geolocation_lng DOUBLE
) WITH (
    external_location = 'file:///data/parquet/customers',
    format = 'PARQUET'
);

-- Reviews: partitioned by score
CREATE TABLE IF NOT EXISTS muwalah.main.reviews (
    review_id VARCHAR,
    order_id VARCHAR,
    review_comment_title VARCHAR,
    review_comment_message VARCHAR,
    review_creation_date TIMESTAMP,
    review_answer_timestamp TIMESTAMP,
    review_score BIGINT
) WITH (
    external_location = 'file:///data/parquet/reviews',
    format = 'PARQUET',
    partitioned_by = ARRAY['review_score']
);

CALL muwalah.system.sync_partition_metadata('main', 'reviews', 'FULL');

-- Sellers: with geolocation
CREATE TABLE IF NOT EXISTS muwalah.main.sellers (
    seller_id VARCHAR,
    seller_zip_code_prefix VARCHAR,
    seller_city VARCHAR,
    seller_state VARCHAR,
    geolocation_lat DOUBLE,
    geolocation_lng DOUBLE
) WITH (
    external_location = 'file:///data/parquet/sellers',
    format = 'PARQUET'
);
