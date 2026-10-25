#!/usr/bin/env python3

import argparse
import pandas as pd
import matplotlib.pyplot as plt

def main():
    parser = argparse.ArgumentParser(
        description="Plot GC Overhead (%) bar chart for all configurations"
    )
    parser.add_argument(
        "input_csv",
        help="Path to the per-config CSV file (must have columns 'config' and 'avg_pct_gc_time')"
    )
    parser.add_argument(
        "--output_png",
        help="Optional path to save the bar chart as a PNG instead of showing it",
        default=None
    )
    args = parser.parse_args()

    # Load the per-config metrics
    df = pd.read_csv(args.input_csv)

    # Ensure we have the necessary columns
    if 'config' not in df.columns or 'avg_pct_gc_time' not in df.columns:
        raise ValueError("Input CSV must contain 'config' and 'avg_pct_gc_time' columns")

    # Sort configs by descending overhead (so highest bars on left)
    df_sorted = df.sort_values('avg_pct_gc_time', ascending=False).reset_index(drop=True)

    # Plot
    plt.figure(figsize=(12, 6))
    plt.bar(
        df_sorted['config'],
        df_sorted['avg_pct_gc_time']
    )
    plt.xlabel('Configuration')
    plt.ylabel('Average GC Overhead (%)')
    plt.title('GC Overhead Comparison Across All Configurations')
    plt.xticks(rotation=90, fontsize=8)
    plt.tight_layout()

    # Show or save
    if args.output_png:
        plt.savefig(args.output_png, dpi=300, bbox_inches='tight')
        print(f"Saved overhead bar chart to {args.output_png}")
    else:
        plt.show()

if __name__ == "__main__":
    main()
