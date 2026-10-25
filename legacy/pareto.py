#!/usr/bin/env python3

import argparse
import pandas as pd
import matplotlib.pyplot as plt

def pareto_frontier(df, x_col, y_col):
    """
    Compute Pareto frontier for minimizing x_col and y_col.
    Returns two lists: frontier_x, frontier_y.
    """
    # Sort by X ascending
    df_sorted = df.sort_values(x_col)
    frontier = []
    best_y = float('inf')

    for _, row in df_sorted.iterrows():
        y = row[y_col]
        if y < best_y:
            frontier.append((row[x_col], y))
            best_y = y

    # Unzip into two sequences
    frontier_x, frontier_y = zip(*frontier)
    return list(frontier_x), list(frontier_y)


def main():
    parser = argparse.ArgumentParser(
        description="Plot Pareto frontier for G1 GC configurations"
    )
    parser.add_argument(
        "input_csv",
        help="Path to the per-config CSV file (must have columns 'config', 'avg_total_time_ms', 'avg_p99_ms')"
    )
    parser.add_argument(
        "--output_png",
        help="Optional path to save the plot as a PNG instead of showing it",
        default=None
    )
    args = parser.parse_args()

    # Load the per-config metrics
    df = pd.read_csv(args.input_csv)

    # Filter only G1 configurations
    df_g1 = df[df['config'].str.startswith('parallel-')]

    # Metrics to plot
    x_col = 'avg_total_time_ms'
    y_col = 'avg_p99_ms'

    # Compute Pareto frontier
    frontier_x, frontier_y = pareto_frontier(df_g1, x_col, y_col)

    # Create the plot
    plt.figure(figsize=(10, 8))
    plt.scatter(df_g1[x_col], df_g1[y_col], label='All G1 configs', alpha=0.7)

    # Annotate each point with its config name
    for _, row in df_g1.iterrows():
        plt.annotate(
            row['config'],
            (row[x_col], row[y_col]),
            textcoords="offset points",
            xytext=(5, 2),
            ha='left',
            fontsize=8
        )

    # Plot Pareto frontier
    plt.plot(frontier_x, frontier_y, color='red', linewidth=2, label='Pareto frontier')

    plt.xlabel('Average Total Time (ms)')
    plt.ylabel('Average P99 Pause (ms)')
    plt.title('G1 GC Configurations: Pareto Frontier')
    plt.legend()
    plt.grid(True)

    # Show or save
    if args.output_png:
        plt.savefig(args.output_png, dpi=300, bbox_inches='tight')
        print(f"Saved Pareto plot to {args.output_png}")
    else:
        plt.show()


if __name__ == "__main__":
    main()
