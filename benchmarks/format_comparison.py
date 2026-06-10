"""
Format Comparison Benchmark: CSV vs JSON vs Parquet

Measures read speed, query speed, and storage footprint for
the same data across three formats. Uses pandas/pyarrow locally
(not Trino) because the point is format comparison, not engine
comparison.

Diego's use case: "Build the business case for migration"
"""
import json
import os
import time

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import pyarrow.parquet as pq

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
RAW_DIR = os.path.join(DATA_DIR, 'raw')
PARQUET_DIR = os.path.join(DATA_DIR, 'parquet')
RESULTS_DIR = os.path.join(os.path.dirname(__file__), 'results')
JSON_DIR = os.path.join(DATA_DIR, 'json_tmp')


def setup_json_files():
    """Create JSON versions of the CSV files for benchmarking."""
    os.makedirs(JSON_DIR, exist_ok=True)
    for name in ['olist_orders_dataset', 'olist_order_items_dataset', 'olist_customers_dataset']:
        csv_path = os.path.join(RAW_DIR, f'{name}.csv')
        json_path = os.path.join(JSON_DIR, f'{name}.json')
        if not os.path.exists(json_path):
            df = pd.read_csv(csv_path)
            df.to_json(json_path, orient='records', lines=True)


def time_read(func, label, iterations=3):
    """Time a read function over multiple iterations, return average."""
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        result = func()
        elapsed = time.perf_counter() - start
        times.append(elapsed)
    avg = sum(times) / len(times)
    print(f"  {label}: {avg:.3f}s (avg of {iterations})")
    return avg, result


def benchmark_full_read():
    """Benchmark: read the full orders dataset."""
    print("\n--- Full Table Read: Orders ---")
    csv_time, _ = time_read(
        lambda: pd.read_csv(os.path.join(RAW_DIR, 'olist_orders_dataset.csv')),
        "CSV"
    )
    json_time, _ = time_read(
        lambda: pd.read_json(os.path.join(JSON_DIR, 'olist_orders_dataset.json'), lines=True),
        "JSON"
    )
    parquet_time, _ = time_read(
        lambda: pq.read_table(os.path.join(PARQUET_DIR, 'orders')).to_pandas(),
        "Parquet"
    )
    return {'csv': csv_time, 'json': json_time, 'parquet': parquet_time}


def benchmark_column_projection():
    """Benchmark: read only 2 columns from orders."""
    print("\n--- Column Projection: 2 of 19 columns ---")
    csv_time, _ = time_read(
        lambda: pd.read_csv(
            os.path.join(RAW_DIR, 'olist_orders_dataset.csv'),
            usecols=['order_id', 'order_status']
        ),
        "CSV (usecols)"
    )
    json_time, _ = time_read(
        lambda: pd.read_json(
            os.path.join(JSON_DIR, 'olist_orders_dataset.json'), lines=True
        )[['order_id', 'order_status']],
        "JSON (post-filter)"
    )
    parquet_time, _ = time_read(
        lambda: pq.read_table(
            os.path.join(PARQUET_DIR, 'orders'),
            columns=['order_id', 'order_status']
        ).to_pandas(),
        "Parquet (column projection)"
    )
    return {'csv': csv_time, 'json': json_time, 'parquet': parquet_time}


def benchmark_filtered_read():
    """Benchmark: read orders for a specific year/month (partition pruning)."""
    print("\n--- Filtered Read: year=2017, month=10 ---")
    csv_time, _ = time_read(
        lambda: pd.read_csv(os.path.join(RAW_DIR, 'olist_orders_dataset.csv')).query(
            "order_purchase_timestamp.str.startswith('2017-10')"
        ),
        "CSV (full scan + filter)"
    )
    json_time, _ = time_read(
        lambda: pd.read_json(
            os.path.join(JSON_DIR, 'olist_orders_dataset.json'), lines=True
        ).query("order_purchase_timestamp.str.startswith('2017-10')"),
        "JSON (full scan + filter)"
    )
    parquet_time, _ = time_read(
        lambda: pq.read_table(
            os.path.join(PARQUET_DIR, 'orders'),
            filters=[('year', '=', 2017), ('month', '=', 10)]
        ).to_pandas(),
        "Parquet (partition pruning)"
    )
    return {'csv': csv_time, 'json': json_time, 'parquet': parquet_time}


def measure_storage():
    """Measure file sizes across formats."""
    print("\n--- Storage Footprint ---")
    def dir_size(path):
        total = 0
        for root, dirs, files in os.walk(path):
            for f in files:
                fp = os.path.join(root, f)
                if not f.startswith('.'):
                    total += os.path.getsize(fp)
        return total

    csv_size = sum(
        os.path.getsize(os.path.join(RAW_DIR, f))
        for f in os.listdir(RAW_DIR) if f.endswith('.csv')
    )
    json_size = dir_size(JSON_DIR)
    parquet_size = dir_size(PARQUET_DIR)

    for label, size in [('CSV', csv_size), ('JSON', json_size), ('Parquet', parquet_size)]:
        print(f"  {label}: {size / 1024 / 1024:.1f} MB")

    return {
        'csv': csv_size / 1024 / 1024,
        'json': json_size / 1024 / 1024,
        'parquet': parquet_size / 1024 / 1024
    }


def generate_charts(results, storage):
    """Generate comparison charts."""
    os.makedirs(RESULTS_DIR, exist_ok=True)

    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    fig.suptitle('Format Comparison: CSV vs JSON vs Parquet', fontsize=14, fontweight='bold')

    formats = ['CSV', 'JSON', 'Parquet']
    colors = ['#e74c3c', '#f39c12', '#2ecc71']

    for idx, (title, data) in enumerate(results.items()):
        values = [data['csv'], data['json'], data['parquet']]
        bars = axes[idx].bar(formats, values, color=colors)
        axes[idx].set_title(title)
        axes[idx].set_ylabel('Time (seconds)')
        for bar, val in zip(bars, values):
            axes[idx].text(bar.get_x() + bar.get_width()/2., bar.get_height(),
                          f'{val:.3f}s', ha='center', va='bottom', fontsize=9)

    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_DIR, 'format_comparison.png'), dpi=150)
    print(f"\nSaved: {os.path.join(RESULTS_DIR, 'format_comparison.png')}")

    fig, ax = plt.subplots(figsize=(8, 5))
    values = [storage['csv'], storage['json'], storage['parquet']]
    bars = ax.bar(formats, values, color=colors)
    ax.set_title('Storage Footprint Comparison', fontsize=14, fontweight='bold')
    ax.set_ylabel('Size (MB)')
    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width()/2., bar.get_height(),
               f'{val:.1f} MB', ha='center', va='bottom', fontsize=10)
    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_DIR, 'storage_comparison.png'), dpi=150)
    print(f"Saved: {os.path.join(RESULTS_DIR, 'storage_comparison.png')}")


def main():
    print("=" * 60)
    print("FORMAT COMPARISON BENCHMARK")
    print("=" * 60)

    setup_json_files()

    results = {
        'Full Table Read': benchmark_full_read(),
        'Column Projection': benchmark_column_projection(),
        'Filtered Read (Partition)': benchmark_filtered_read(),
    }
    storage = measure_storage()

    os.makedirs(RESULTS_DIR, exist_ok=True)
    with open(os.path.join(RESULTS_DIR, 'benchmark_results.json'), 'w') as f:
        json.dump({'timings': results, 'storage_mb': storage}, f, indent=2)

    generate_charts(results, storage)

    import shutil
    shutil.rmtree(JSON_DIR, ignore_errors=True)

    print("\nDone! Results in benchmarks/results/")


if __name__ == '__main__':
    main()
