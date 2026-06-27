#!/usr/bin/env python3
"""
Generate GIF and PNG visualizations for Slitherin solvers

This script helps create demo GIFs and score plots for documentation.

For GIF generation (requires display):
    python3 generate_visuals.py --gif --solver milp --duration 30

For score plots (headless-compatible):
    python3 generate_visuals.py --scores --solver milp

For both:
    python3 generate_visuals.py --all --solver milp
"""

import argparse
import os
import sys

def generate_gif(solver_name, duration=30):
    """
    Generate animated GIF of solver gameplay.

    Requires:
    - Display server (or Xvfb for headless)
    - PIL/Pillow for GIF creation
    - pygame for game rendering

    Args:
        solver_name: Name of solver (e.g., 'milp', 'hamilton')
        duration: Duration in seconds to record
    """
    print(f"🎬 Generating GIF for {solver_name} solver...")
    print(f"   Duration: {duration} seconds")
    print()

    # Check if display available
    if not os.environ.get('DISPLAY'):
        print("⚠️  WARNING: No DISPLAY environment variable found.")
        print("   For headless systems, use Xvfb:")
        print(f"   xvfb-run -a python3 slitherin.py --{solver_name}")
        print()
        print("   To capture as GIF, you can use:")
        print("   1. byzanz-record (CLI screen recorder)")
        print(f"      byzanz-record -d {duration} assets/gifs/{solver_name}.gif")
        print("   2. Or run with display and use screen recording software")
        return False

    print("✅ Display found. Instructions:")
    print()
    print("Method 1: Using byzanz-record (recommended):")
    print(f"  1. Open terminal, run: python3 slitherin.py --{solver_name}")
    print(f"  2. In another terminal, run: byzanz-record -d {duration} -x X -y Y -w W -h H assets/gifs/{solver_name}.gif")
    print("     (Replace X, Y, W, H with window coordinates)")
    print()
    print("Method 2: Using OBS Studio or similar:")
    print(f"  1. Run: python3 slitherin.py --{solver_name}")
    print("  2. Record screen to video")
    print("  3. Convert to GIF using ffmpeg:")
    print(f"     ffmpeg -i recording.mp4 -vf 'fps=10,scale=400:-1' assets/gifs/{solver_name}.gif")
    print()
    print("Method 3: Using Python PIL (programmatic):")
    print("  See scripts/record_gameplay.py for frame-by-frame capture")
    print()

    return True

def generate_scores(solver_name):
    """
    Generate score plot PNG from CSV data.

    This works in headless environments.

    Args:
        solver_name: Name of solver (e.g., 'milp', 'hamilton')
    """
    print(f"📊 Generating score plot for {solver_name} solver...")

    csv_path = f"scores/{solver_name}.csv"
    png_path = f"scores/{solver_name}.png"

    if not os.path.exists(csv_path):
        print(f"⚠️  CSV file not found: {csv_path}")
        print(f"   Run benchmark first: python3 slitherin.py --{solver_name}_trainer")
        print(f"   Or run multiple games: python3 slitherin.py --{solver_name}")
        return False

    # Import here to avoid dependency issues
    try:
        import csv
        import matplotlib
        matplotlib.use('Agg')  # Headless backend
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("   Install with: pip install matplotlib numpy")
        return False

    # Read scores
    scores = []
    with open(csv_path, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            if row and row[0]:
                try:
                    scores.append(float(row[0]))
                except ValueError:
                    continue

    if not scores:
        print(f"❌ No valid scores found in {csv_path}")
        return False

    print(f"   Found {len(scores)} games")
    print(f"   Min: {min(scores)}, Max: {max(scores)}, Avg: {np.mean(scores):.2f}")

    # Create plot
    plt.figure(figsize=(10, 6))

    x = list(range(len(scores)))

    # Plot scores
    plt.plot(x, scores, alpha=0.6, linewidth=1, label='Score per run')

    # Plot average line
    avg_line = [np.mean(scores)] * len(scores)
    plt.plot(x, avg_line, 'r--', linewidth=2, label=f'Average: {np.mean(scores):.1f}')

    # Styling
    plt.title(f'{solver_name.upper()} Solver Performance', fontsize=16, fontweight='bold')
    plt.xlabel('Run Number', fontsize=12)
    plt.ylabel('Score', fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.legend(loc='upper left')

    # Save
    plt.tight_layout()
    plt.savefig(png_path, dpi=150, bbox_inches='tight')
    plt.close()

    print(f"✅ Score plot saved: {png_path}")
    return True

def main():
    parser = argparse.ArgumentParser(description='Generate visualizations for Slitherin solvers')
    parser.add_argument('--solver', required=True, help='Solver name (e.g., milp, hamilton)')
    parser.add_argument('--gif', action='store_true', help='Generate GIF demo')
    parser.add_argument('--scores', action='store_true', help='Generate score PNG')
    parser.add_argument('--all', action='store_true', help='Generate both GIF and scores')
    parser.add_argument('--duration', type=int, default=30, help='GIF duration in seconds (default: 30)')

    args = parser.parse_args()

    # Ensure directories exist
    os.makedirs('assets/gifs', exist_ok=True)
    os.makedirs('scores', exist_ok=True)

    success = True

    if args.all or args.gif:
        success = generate_gif(args.solver, args.duration) and success

    if args.all or args.scores:
        success = generate_scores(args.solver) and success

    if not (args.gif or args.scores or args.all):
        print("❌ Please specify --gif, --scores, or --all")
        parser.print_help()
        return 1

    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())
