#!/usr/bin/env python3
"""Benchmark partitioning strategies with a synthetic Dask workload.

Creates a Dask DataFrame with `pop_size` rows, repartitions to `n_partitions`,
applies a CPU-bound map_partition workload that simulates per-person progression,
and records wall time and peak memory.

Usage example:
  python scripts/benchmark_partitioning.py --pop-sizes 10000 --partitions 4,8,16 --repeats 1 --out results/partition_bench.csv

Notes:
- This is a synthetic benchmark intended to emulate the CPU/memory characteristics of
  per-person progression. It doesn't call the lifecourse simulation API directly,
  which keeps the test lightweight and safe to run on developer machines.
- For a real evaluation, increase pop_sizes and run on a replica cluster or CI runner.
"""

import argparse
import csv
import os
import threading
import time

import numpy as np
import pandas as pd
import psutil
from dask.distributed import Client, LocalCluster
import dask.dataframe as dd


def monitor_memory(pid, interval, stop_event, out_dict):
    proc = psutil.Process(pid)
    peak = 0
    try:
        while not stop_event.is_set():
            try:
                rss = proc.memory_info().rss
            except psutil.NoSuchProcess:
                break
            if rss > peak:
                peak = rss
            time.sleep(interval)
    finally:
        out_dict['peak_rss'] = peak


def synthetic_partition_work(df: pd.DataFrame) -> pd.DataFrame:
    # Work on a copy to avoid SettingWithCopyWarning and preserve input
    df = df.copy()
    # Do some CPU-bound numeric work per row to simulate per-year progression
    x = df['x'].to_numpy()
    # repeated math to consume CPU
    for _ in range(12):
        x = np.log1p(x * 1.0001) + np.sin(x)
    df['y'] = x
    return df


def run_one(pop_size, n_partitions, repeat, temp_dir=None):
    # Create a small pandas DataFrame then convert to dask and repartition
    # keep memory footprint small by using float32 where possible
    N = int(pop_size)
    pdf = pd.DataFrame({'id': np.arange(N), 'x': np.random.random(N).astype(np.float64)})
    # Create dask dataframe
    ddf = dd.from_pandas(pdf, npartitions=1).repartition(npartitions=int(n_partitions))

    # Start a LocalCluster tuned for this partitioning
    n_workers = min(int(n_partitions), max(1, os.cpu_count() or 1))
    cluster = LocalCluster(n_workers=n_workers, threads_per_worker=1, processes=True, silence_logs=False)
    client = Client(cluster)

    # Warm-up
    _ = ddf.head(5)

    # Start memory monitor
    stop_event = threading.Event()
    mem_out = {}
    monitor_thread = threading.Thread(target=monitor_memory, args=(os.getpid(), 0.25, stop_event, mem_out))
    monitor_thread.start()

    t0 = time.perf_counter()
    # Prepare correct meta (include the output 'y' column) for dask
    meta = pdf.head(0).copy()
    meta['y'] = np.array([], dtype=np.float64)

    # Apply the synthetic workload across partitions
    res = ddf.map_partitions(synthetic_partition_work, meta=meta)
    # Trigger computation
    try:
        _ = res.compute()
    except Exception as e:
        client.close()
        cluster.close()
        raise
    wall = time.perf_counter() - t0

    # Stop monitor and collect peak
    stop_event.set()
    monitor_thread.join()
    peak_rss = mem_out.get('peak_rss', 0)

    client.close()
    cluster.close()

    return {'pop_size': N, 'n_partitions': int(n_partitions), 'repeat': repeat, 'wall_time_s': wall, 'peak_rss_mb': peak_rss / (1024 * 1024)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pop-sizes', default='10000', help='Comma-separated population sizes to test')
    parser.add_argument('--partitions', default='4,8,16', help='Comma-separated partition counts to test')
    parser.add_argument('--repeats', type=int, default=1)
    parser.add_argument('--out', default='results/partition_bench.csv')
    args = parser.parse_args()

    pop_sizes = [int(x) for x in args.pop_sizes.split(',') if x.strip()]
    partitions = [int(x) for x in args.partitions.split(',') if x.strip()]

    os.makedirs(os.path.dirname(args.out), exist_ok=True)

    fieldnames = ['pop_size', 'n_partitions', 'repeat', 'wall_time_s', 'peak_rss_mb']
    write_header = not os.path.exists(args.out)

    with open(args.out, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        for pop in pop_sizes:
            for n in partitions:
                for r in range(1, args.repeats + 1):
                    print(f"Running pop={pop}, partitions={n}, repeat={r}")
                    result = run_one(pop, n, r)
                    print(result)
                    writer.writerow(result)
                    f.flush()


if __name__ == '__main__':
    main()
