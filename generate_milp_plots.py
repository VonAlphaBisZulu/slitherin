#!/usr/bin/env python3
"""
Generate plots for MILP solver in style matching existing base_game_model plots.

Generates:
1. Score per run plot (matches existing style)
2. Scatter plot: Score vs Steps-to-Apple (new analysis)
"""

import csv
import os
import matplotlib
matplotlib.use('Agg')  # Headless backend
import matplotlib.pyplot as plt
import numpy as np


def generate_score_plot():
    """Generate score per run plot matching base_game_model._save_png() style."""
    input_path = "scores/milp.csv"
    output_path = "scores/milp.png"

    if not os.path.exists(input_path):
        print(f"❌ {input_path} not found")
        return False

    # Read scores (matching base_game_model logic exactly)
    x = []
    y = []
    with open(input_path, "r") as scores:
        reader = csv.reader(scores)
        data = list(reader)
        for i in range(0, len(data)):
            if data[i] and data[i][0]:  # Skip empty rows
                x.append(float(i))
                y.append(float(data[i][0]))

    if not y:
        print(f"❌ No valid scores in {input_path}")
        return False

    # Create plot (matching base_game_model._save_png() exactly)
    plt.subplots()
    plt.plot(x, y, label="score per run")

    # Average line
    average_range = len(x)
    plt.plot(x[-average_range:], [np.mean(y[-average_range:])] * len(y[-average_range:]),
             linestyle="--", label="average")

    # Styling (matches base_game_model)
    plt.title("milp")
    plt.xlabel("runs")
    plt.ylabel("scores")
    plt.legend(loc="upper left")

    # Save
    plt.savefig(output_path, bbox_inches="tight")
    plt.close()

    print(f"✅ Generated: {output_path}")
    print(f"   Stats: Min={min(y):.0f}, Max={max(y):.0f}, Avg={np.mean(y):.2f}")
    return True


def generate_scatter_plot():
    """Generate scatter plot: Score (x) vs Steps-to-Apple (y)."""
    input_path = "scores/milp_steps_per_apple.csv"
    output_path = "scores/milp_steps_analysis.png"

    if not os.path.exists(input_path):
        print(f"⚠️  {input_path} not found (run milp_trainer to generate)")
        return False

    # Read data
    scores = []
    steps = []
    with open(input_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            scores.append(int(row['score']))
            steps.append(int(row['steps_to_apple']))

    if not scores:
        print(f"❌ No data in {input_path}")
        return False

    # Create scatter plot
    fig, ax = plt.subplots(figsize=(10, 6))

    # Scatter with alpha for overlapping points
    ax.scatter(scores, steps, alpha=0.5, s=20, color='#2196F3', edgecolors='none')

    # Add trend line (moving average)
    if len(scores) > 10:
        # Group by score and calculate mean steps
        score_to_steps = {}
        for s, st in zip(scores, steps):
            if s not in score_to_steps:
                score_to_steps[s] = []
            score_to_steps[s].append(st)

        sorted_scores = sorted(score_to_steps.keys())
        avg_steps = [np.mean(score_to_steps[s]) for s in sorted_scores]

        ax.plot(sorted_scores, avg_steps, 'r-', linewidth=2, label='Average', alpha=0.7)

    # Styling
    ax.set_xlabel("Score (Snake Length)", fontsize=12)
    ax.set_ylabel("Steps to Reach Next Apple", fontsize=12)
    ax.set_title("MILP Solver: Efficiency Analysis", fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend()

    # Add statistics text
    avg_steps_overall = np.mean(steps)
    median_steps = np.median(steps)
    stats_text = f"Overall Avg: {avg_steps_overall:.1f} steps\nMedian: {median_steps:.0f} steps"
    ax.text(0.02, 0.98, stats_text, transform=ax.transAxes,
            fontsize=10, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    # Save
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()

    print(f"✅ Generated: {output_path}")
    print(f"   Data points: {len(scores)}")
    print(f"   Avg steps to apple: {avg_steps_overall:.2f}")
    print(f"   Min: {min(steps)}, Max: {max(steps)}")
    return True


def main():
    """Generate both plots."""
    print("📊 Generating MILP solver plots...\n")

    success = True
    success = generate_score_plot() and success
    print()
    success = generate_scatter_plot() and success

    if success:
        print("\n✅ All plots generated successfully!")
    else:
        print("\n⚠️  Some plots failed to generate")

    return 0 if success else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
