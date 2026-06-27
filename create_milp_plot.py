#!/usr/bin/env python3
"""
Generate PNG score plot for MILP solver.
"""

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import numpy as np

# Read MILP scores
with open('scores/milp.csv', 'r') as f:
    scores = [int(line.strip()) for line in f if line.strip()]

# Create figure
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
fig.suptitle('MILP Solver Performance', fontsize=16, fontweight='bold')

# Plot 1: Score over games
ax1.plot(scores, 'o-', color='#2196F3', markersize=4, linewidth=1, alpha=0.7)
ax1.axhline(y=np.mean(scores), color='red', linestyle='--', label=f'Mean: {np.mean(scores):.1f}')
ax1.axhline(y=143, color='green', linestyle='--', alpha=0.5, label='Perfect Score: 143')
ax1.set_xlabel('Game Number', fontsize=12)
ax1.set_ylabel('Score', fontsize=12)
ax1.set_title(f'Scores over {len(scores)} Games', fontsize=14)
ax1.grid(True, alpha=0.3)
ax1.legend(loc='lower right')
ax1.set_ylim([min(scores) - 5, 145])

# Plot 2: Score distribution histogram
bins = range(min(scores) - 1, max(scores) + 2)
ax2.hist(scores, bins=bins, color='#4CAF50', edgecolor='black', alpha=0.7)
ax2.axvline(x=np.mean(scores), color='red', linestyle='--', linewidth=2, label=f'Mean: {np.mean(scores):.1f}')
ax2.axvline(x=np.median(scores), color='orange', linestyle='--', linewidth=2, label=f'Median: {np.median(scores):.1f}')
ax2.set_xlabel('Score', fontsize=12)
ax2.set_ylabel('Frequency', fontsize=12)
ax2.set_title('Score Distribution', fontsize=14)
ax2.grid(True, alpha=0.3, axis='y')
ax2.legend()

# Add statistics text
stats_text = f"""Statistics:
Games: {len(scores)}
Min: {min(scores)}
Max: {max(scores)}
Mean: {np.mean(scores):.2f}
Median: {np.median(scores):.2f}
Std Dev: {np.std(scores):.2f}
Perfect Games (143): {scores.count(143)} ({100.0 * scores.count(143) / len(scores):.1f}%)
Win Rate (≥140): {sum(1 for s in scores if s >= 140)} ({100.0 * sum(1 for s in scores if s >= 140) / len(scores):.1f}%)"""

plt.figtext(0.02, 0.02, stats_text, fontsize=10, family='monospace',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

plt.tight_layout(rect=[0, 0.12, 1, 0.96])
plt.savefig('scores/milp.png', dpi=150, bbox_inches='tight')
print(f"✓ Saved plot to scores/milp.png")

# Print statistics
print(f"\nMILP Solver Statistics:")
print(f"  Games played: {len(scores)}")
print(f"  Min score: {min(scores)}")
print(f"  Max score: {max(scores)}")
print(f"  Mean score: {np.mean(scores):.2f}")
print(f"  Median score: {np.median(scores):.2f}")
print(f"  Std deviation: {np.std(scores):.2f}")
print(f"  Perfect games (143): {scores.count(143)} / {len(scores)} ({100.0 * scores.count(143) / len(scores):.1f}%)")
print(f"  Win rate (≥140): {sum(1 for s in scores if s >= 140)} / {len(scores)} ({100.0 * sum(1 for s in scores if s >= 140) / len(scores):.1f}%)")
