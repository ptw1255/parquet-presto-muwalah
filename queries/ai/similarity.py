"""
Product Similarity via Feature Vectors from Parquet Data.

Extracts product features from Parquet (via direct read),
builds simple feature vectors, and computes cosine similarity.

PM angle: Parquet bridges analytics and ML — same data, same format,
no ETL copy step. Structured features live alongside review text.
"""
import os
import sys

import numpy as np
import pyarrow.parquet as pq
import pandas as pd

PARQUET_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'parquet')


def load_product_features() -> pd.DataFrame:
    """Load product features directly from Parquet — demonstrating
    that ML pipelines can read the same Parquet files as analytics."""
    products = pq.read_table(os.path.join(PARQUET_DIR, 'products')).to_pandas()

    # Flatten nested category dict -> category_english
    products['category_english'] = products['category'].apply(
        lambda c: c.get('english', '') if isinstance(c, dict) else ''
    )

    # Flatten nested dimensions dict -> weight_g, length_cm, height_cm, width_cm
    for dim in ['weight_g', 'length_cm', 'height_cm', 'width_cm']:
        products[dim] = products['dimensions'].apply(
            lambda d, k=dim: d.get(k, 0.0) if isinstance(d, dict) else 0.0
        )

    # Load order stats per product
    orders = pq.read_table(
        os.path.join(PARQUET_DIR, 'orders'),
        columns=['product_id', 'price', 'order_id']
    ).to_pandas()
    product_stats = orders.groupby('product_id').agg(
        avg_price=('price', 'mean'),
        order_count=('order_id', 'nunique')
    ).reset_index()

    # Load average review score per product
    reviews = pq.read_table(os.path.join(PARQUET_DIR, 'reviews')).to_pandas()
    reviews['review_score'] = pd.to_numeric(reviews['review_score'], errors='coerce')
    order_products = orders[['order_id', 'product_id']].drop_duplicates()
    review_scores = reviews.merge(order_products, on='order_id')
    product_reviews = review_scores.groupby('product_id').agg(
        avg_review=('review_score', 'mean'),
        review_count=('review_id', 'nunique')
    ).reset_index()

    # Merge all features
    df = products.merge(product_stats, on='product_id', how='left')
    df = df.merge(product_reviews, on='product_id', how='left')
    df = df.fillna(0)

    return df


def build_feature_vectors(df: pd.DataFrame) -> tuple:
    """Build normalized feature vectors for similarity computation."""
    feature_cols = [
        'weight_g', 'length_cm', 'height_cm', 'width_cm',
        'avg_price', 'order_count', 'avg_review', 'review_count',
        'product_name_length', 'product_description_length', 'product_photos_qty'
    ]
    vectors = df[feature_cols].values.astype(float)

    # Normalize each feature to [0, 1]
    mins = vectors.min(axis=0)
    maxs = vectors.max(axis=0)
    ranges = maxs - mins
    ranges[ranges == 0] = 1
    normalized = (vectors - mins) / ranges

    return normalized, df


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    dot = np.dot(a, b)
    norm = np.linalg.norm(a) * np.linalg.norm(b)
    return dot / norm if norm > 0 else 0.0


def find_similar(product_id: str, top_n: int = 5):
    """Find products most similar to the given product."""
    print("Loading product features from Parquet...")
    df = load_product_features()
    vectors, products = build_feature_vectors(df)

    idx = products.index[products['product_id'] == product_id].tolist()
    if not idx:
        print(f"Product {product_id} not found.")
        print(f"\nSample product IDs:")
        for pid in products['product_id'].head(5):
            print(f"  {pid}")
        return
    idx = idx[0]

    target_vector = vectors[idx]
    target = products.iloc[idx]
    print(f"\nTarget product: {target['product_id']}")
    print(f"  Category: {target['category_english']}")
    print(f"  Price: ${target['avg_price']:.2f}")
    print(f"  Review: {target['avg_review']:.1f}/5 ({int(target['review_count'])} reviews)")

    similarities = []
    for i in range(len(vectors)):
        if i != idx:
            sim = cosine_similarity(target_vector, vectors[i])
            similarities.append((i, sim))
    similarities.sort(key=lambda x: x[1], reverse=True)

    print(f"\nTop {top_n} similar products:")
    print(f"{'Category':<30} {'Price':>8} {'Review':>8} {'Similarity':>10}")
    print("-" * 60)
    for i, sim in similarities[:top_n]:
        p = products.iloc[i]
        cat = str(p['category_english'])[:29] if p['category_english'] else 'unknown'
        print(f"{cat:<30} ${p['avg_price']:>7.2f} {p['avg_review']:>6.1f}/5 {sim:>10.4f}")


def main():
    if len(sys.argv) > 1:
        product_id = sys.argv[1]
    else:
        df = load_product_features()
        popular = df.nlargest(10, 'order_count')
        print("Popular products (pick one):")
        for _, row in popular.iterrows():
            cat = row['category_english'] if row['category_english'] else 'unknown'
            print(f"  {row['product_id']}  ({cat}, {int(row['order_count'])} orders)")
        product_id = input("\nEnter product_id: ")

    find_similar(product_id, top_n=10)


if __name__ == '__main__':
    main()
