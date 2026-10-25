#csd4845 Dimitris Asimakopoulos - hy446 project
#python script to aggregate DaCapo-Chopin GC benchmark metrics per configuration to make it more readable

#!/usr/bin/env python3
import argparse
import pandas as pd

def main():
    parser = argparse.ArgumentParser(
        description="Aggregate DaCapo-Chopin GC benchmark metrics per configuration"
    )
    parser.add_argument(
        "input_csv",
        help="Path to the input CSV of raw benchmark runs"
    )
    parser.add_argument(
        "output_csv",
        help="Path where the aggregated per-config CSV will be written"
    )
    args = parser.parse_args()

    df = pd.read_csv(args.input_csv)
    required = [
        'config', 'total_time_ms', 'total_gc_ms', 'pct_gc_time',
        'min_pause_ms', 'max_pause_ms', 'p50_ms', 'p99_ms',
        'young_gc_count', 'full_gc_count'
    ]
    missing = set(required) - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")


    df['total_gc_events'] = df['young_gc_count'] + df['full_gc_count']


    agg = df.groupby('config').agg({
        'total_time_ms': 'mean',
        'total_gc_ms': 'mean',
        'pct_gc_time': 'mean',
        'min_pause_ms': 'mean',
        'max_pause_ms': 'mean',
        'p50_ms': 'mean',
        'p99_ms': 'mean',
        'total_gc_events': 'mean'
    }).reset_index()
    agg = agg.rename(columns={
        'total_time_ms': 'avg_total_time_ms',
        'total_gc_ms': 'avg_total_gc_ms',
        'pct_gc_time': 'avg_pct_gc_time',
        'min_pause_ms': 'avg_min_pause_ms',
        'max_pause_ms': 'avg_max_pause_ms',
        'p50_ms': 'avg_p50_ms',
        'p99_ms': 'avg_p99_ms',
        'total_gc_events': 'avg_total_gc_events'
    })

    agg.to_csv(args.output_csv, index=False)
    print(f"Wrote aggregated data for {len(agg)} configurations to {args.output_csv}")

if __name__ == "__main__":
    main()
