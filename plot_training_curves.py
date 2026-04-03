"""
Plot Training Curves - Loss and Accuracy over Epochs

Generates:
1. Training & Validation Loss curves
2. Training & Validation Accuracy curves
3. Combined Loss + Accuracy plot
4. Learning rate schedule (if available)
"""

import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# Configuration
MODEL_DIR = Path(__file__).parent / 'models'
HISTORY_FILE = MODEL_DIR / 'transfer_learning_history.json'
OUTPUT_DIR = MODEL_DIR / 'plots'
OUTPUT_DIR.mkdir(exist_ok=True)

# Load training history
print(f"Loading training history from: {HISTORY_FILE}")
with open(HISTORY_FILE, 'r') as f:
    history = json.load(f)

train_loss = history.get('train_loss', [])
train_acc = history.get('train_acc', [])
val_loss = history.get('val_loss', [])
val_acc = history.get('val_acc', [])
epochs = history.get('epochs', list(range(1, len(train_loss) + 1)))

print(f"Loaded {len(epochs)} epochs of training data")

# Calculate best metrics
best_val_acc_epoch = np.argmax(val_acc) + 1
best_val_acc = max(val_acc)
best_val_loss_epoch = np.argmin(val_loss) + 1
best_val_loss = min(val_loss)

print(f"\nTraining Summary:")
print(f"  Best Validation Accuracy: {best_val_acc:.2f}% (Epoch {best_val_acc_epoch})")
print(f"  Best Validation Loss: {best_val_loss:.4f} (Epoch {best_val_loss_epoch})")
print(f"  Final Training Accuracy: {train_acc[-1]:.2f}%")
print(f"  Final Validation Accuracy: {val_acc[-1]:.2f}%")

print("\nGenerating training curve plots...")

# ============================================
# Plot 1: Training & Validation Loss
# ============================================
print("  1. Training & Validation Loss...")
plt.figure(figsize=(12, 6))

plt.plot(epochs, train_loss, 'b-', linewidth=2, label='Training Loss', marker='o', markersize=6)
plt.plot(epochs, val_loss, 'r-', linewidth=2, label='Validation Loss', marker='s', markersize=6)

# Highlight best validation loss
plt.scatter([best_val_loss_epoch], [best_val_loss], c='darkred', s=150, 
            marker='*', zorder=5, label=f'Best Val Loss: {best_val_loss:.4f}')

plt.xlabel('Epoch', fontsize=12, fontweight='bold')
plt.ylabel('Loss (Cross-Entropy)', fontsize=12, fontweight='bold')
plt.title('Training & Validation Loss Over Epochs', fontsize=14, fontweight='bold', pad=20)
plt.legend(fontsize=11, loc='best')
plt.grid(True, alpha=0.3, linestyle='--')
plt.xticks(epochs)

# Add annotations
for i, (tl, vl) in enumerate(zip(train_loss, val_loss)):
    if i % 3 == 0:  # Annotate every 3rd point
        plt.annotate(f'{vl:.3f}', (epochs[i], vl), textcoords="offset points", 
                    xytext=(8, 5), fontsize=8, alpha=0.7)

plt.tight_layout()
plt.savefig(OUTPUT_DIR / 'training_loss_curve.png', dpi=300, bbox_inches='tight')
plt.close()
print(f"     Saved to: {OUTPUT_DIR / 'training_loss_curve.png'}")

# ============================================
# Plot 2: Training & Validation Accuracy
# ============================================
print("  2. Training & Validation Accuracy...")
plt.figure(figsize=(12, 6))

plt.plot(epochs, train_acc, 'b-', linewidth=2, label='Training Accuracy', marker='o', markersize=6)
plt.plot(epochs, val_acc, 'g-', linewidth=2, label='Validation Accuracy', marker='s', markersize=6)

# Highlight best validation accuracy
plt.scatter([best_val_acc_epoch], [best_val_acc], c='gold', s=200, 
            marker='*', zorder=5, label=f'Best Val Acc: {best_val_acc:.2f}%')

plt.xlabel('Epoch', fontsize=12, fontweight='bold')
plt.ylabel('Accuracy (%)', fontsize=12, fontweight='bold')
plt.title('Training & Validation Accuracy Over Epochs', fontsize=14, fontweight='bold', pad=20)
plt.legend(fontsize=11, loc='best')
plt.grid(True, alpha=0.3, linestyle='--')
plt.xticks(epochs)
plt.ylim(min(min(train_acc), min(val_acc)) - 2, 100)

# Add annotations
for i, (ta, va) in enumerate(zip(train_acc, val_acc)):
    if i % 3 == 0:  # Annotate every 3rd point
        plt.annotate(f'{va:.1f}%', (epochs[i], va), textcoords="offset points", 
                    xytext=(8, 5), fontsize=8, alpha=0.7)

plt.tight_layout()
plt.savefig(OUTPUT_DIR / 'training_accuracy_curve.png', dpi=300, bbox_inches='tight')
plt.close()
print(f"     Saved to: {OUTPUT_DIR / 'training_accuracy_curve.png'}")

# ============================================
# Plot 3: Combined Loss + Accuracy (Dual Axis)
# ============================================
print("  3. Combined Loss + Accuracy...")
fig, ax1 = plt.subplots(figsize=(14, 7))

# Loss on left y-axis
color = 'tab:red'
ax1.set_xlabel('Epoch', fontsize=12, fontweight='bold')
ax1.set_ylabel('Loss', color=color, fontsize=12, fontweight='bold')
ax1.plot(epochs, train_loss, 'b--', linewidth=2, label='Train Loss', alpha=0.7)
ax1.plot(epochs, val_loss, 'r-', linewidth=2, label='Val Loss')
ax1.tick_params(axis='y', labelcolor=color)
ax1.grid(True, alpha=0.3, linestyle='--')

# Accuracy on right y-axis
ax2 = ax1.twinx()
color = 'tab:green'
ax2.set_ylabel('Accuracy (%)', color=color, fontsize=12, fontweight='bold')
ax2.plot(epochs, train_acc, 'b:', linewidth=2, label='Train Acc', alpha=0.7)
ax2.plot(epochs, val_acc, 'g-', linewidth=2, label='Val Acc')
ax2.tick_params(axis='y', labelcolor=color)

# Combined legend
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='center left', fontsize=10)

plt.title('Training Performance: Loss & Accuracy Combined', fontsize=14, fontweight='bold', pad=20)
plt.xticks(epochs)
fig.tight_layout()
plt.savefig(OUTPUT_DIR / 'combined_training_curves.png', dpi=300, bbox_inches='tight')
plt.close()
print(f"     Saved to: {OUTPUT_DIR / 'combined_training_curves.png'}")

# ============================================
# Plot 4: Training Progress Summary (Multi-panel)
# ============================================
print("  4. Training Progress Summary...")
fig, axes = plt.subplots(2, 2, figsize=(16, 12))

# Top-left: Loss comparison
axes[0, 0].plot(epochs, train_loss, 'b-o', linewidth=2, label='Train Loss', markersize=6, alpha=0.7)
axes[0, 0].plot(epochs, val_loss, 'r-s', linewidth=2, label='Val Loss', markersize=6)
axes[0, 0].set_xlabel('Epoch', fontsize=11)
axes[0, 0].set_ylabel('Loss', fontsize=11)
axes[0, 0].set_title('Loss Comparison', fontsize=12, fontweight='bold')
axes[0, 0].legend(fontsize=10)
axes[0, 0].grid(True, alpha=0.3)

# Top-right: Accuracy comparison
axes[0, 1].plot(epochs, train_acc, 'b-o', linewidth=2, label='Train Acc', markersize=6, alpha=0.7)
axes[0, 1].plot(epochs, val_acc, 'g-s', linewidth=2, label='Val Acc', markersize=6)
axes[0, 1].set_xlabel('Epoch', fontsize=11)
axes[0, 1].set_ylabel('Accuracy (%)', fontsize=11)
axes[0, 1].set_title('Accuracy Comparison', fontsize=12, fontweight='bold')
axes[0, 1].legend(fontsize=10)
axes[0, 1].grid(True, alpha=0.3)
axes[0, 1].set_ylim(0, 100)

# Bottom-left: Validation metrics zoom
val_start_idx = max(0, len(epochs) - 10)  # Last 10 epochs
axes[1, 0].plot(epochs[val_start_idx:], train_loss[val_start_idx:], 'b-o', linewidth=2, label='Train Loss', markersize=8)
axes[1, 0].plot(epochs[val_start_idx:], val_loss[val_start_idx:], 'r-s', linewidth=2, label='Val Loss', markersize=8)
axes[1, 0].set_xlabel('Epoch (Recent)', fontsize=11)
axes[1, 0].set_ylabel('Loss (Zoomed)', fontsize=11)
axes[1, 0].set_title(f'Loss Trend (Last {len(epochs) - val_start_idx} Epochs)', fontsize=12, fontweight='bold')
axes[1, 0].legend(fontsize=10)
axes[1, 0].grid(True, alpha=0.3)

# Bottom-right: Gap analysis (overfitting indicator)
gap = [t - v for t, v in zip(train_acc, val_acc)]
axes[1, 1].bar(epochs, gap, color='orange', alpha=0.7, edgecolor='darkorange')
axes[1, 1].axhline(y=5, color='green', linestyle='--', linewidth=2, label='Acceptable Gap (<5%)')
axes[1, 1].axhline(y=10, color='red', linestyle='--', linewidth=2, label='Warning Gap (>10%)')
axes[1, 1].set_xlabel('Epoch', fontsize=11)
axes[1, 1].set_ylabel('Train-Val Gap (%)', fontsize=11)
axes[1, 1].set_title('Overfitting Indicator (Train-Val Accuracy Gap)', fontsize=12, fontweight='bold')
axes[1, 1].legend(fontsize=10)
axes[1, 1].grid(True, alpha=0.3)

plt.suptitle('Training Progress Summary - All Metrics', fontsize=16, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig(OUTPUT_DIR / 'training_summary_dashboard.png', dpi=300, bbox_inches='tight')
plt.close()
print(f"     Saved to: {OUTPUT_DIR / 'training_summary_dashboard.png'}")

# ============================================
# Plot 5: Convergence Analysis
# ============================================
print("  5. Convergence Analysis...")
plt.figure(figsize=(14, 8))

# Calculate moving averages
window = 3
train_loss_ma = np.convolve(train_loss, np.ones(window)/window, mode='valid')
val_loss_ma = np.convolve(val_loss, np.ones(window)/window, mode='valid')
train_acc_ma = np.convolve(train_acc, np.ones(window)/window, mode='valid')
val_acc_ma = np.convolve(val_acc, np.ones(window)/window, mode='valid')

epochs_ma = epochs[window-1:]

plt.subplot(2, 2, 1)
plt.plot(epochs, train_loss, 'b-', alpha=0.3, label='Raw Train Loss')
plt.plot(epochs, val_loss, 'r-', alpha=0.3, label='Raw Val Loss')
plt.plot(epochs_ma, train_loss_ma, 'b-', linewidth=3, label=f'{window}-Epoch MA Train')
plt.plot(epochs_ma, val_loss_ma, 'r-', linewidth=3, label=f'{window}-Epoch MA Val')
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.title('Loss Convergence (with Moving Average)')
plt.legend()
plt.grid(True, alpha=0.3)

plt.subplot(2, 2, 2)
plt.plot(epochs, train_acc, 'b-', alpha=0.3, label='Raw Train Acc')
plt.plot(epochs, val_acc, 'g-', alpha=0.3, label='Raw Val Acc')
plt.plot(epochs_ma, train_acc_ma, 'b-', linewidth=3, label=f'{window}-Epoch MA Train')
plt.plot(epochs_ma, val_acc_ma, 'g-', linewidth=3, label=f'{window}-Epoch MA Val')
plt.xlabel('Epoch')
plt.ylabel('Accuracy (%)')
plt.title('Accuracy Convergence (with Moving Average)')
plt.legend()
plt.grid(True, alpha=0.3)

# Convergence rate (derivative)
train_loss_deriv = np.diff(train_loss)
val_loss_deriv = np.diff(val_loss)

plt.subplot(2, 2, 3)
plt.plot(epochs[1:], train_loss_deriv, 'b-o', label='Train Loss Derivative', markersize=4)
plt.plot(epochs[1:], val_loss_deriv, 'r-s', label='Val Loss Derivative', markersize=4)
plt.axhline(y=0, color='k', linestyle='--', linewidth=1)
plt.xlabel('Epoch')
plt.ylabel('Rate of Change')
plt.title('Convergence Rate (Derivative)')
plt.legend()
plt.grid(True, alpha=0.3)

# Final metrics
plt.subplot(2, 2, 4)
metrics = ['Final\nTrain Acc', 'Final\nVal Acc', 'Best\nVal Acc', 'Best\nVal Loss\n(x10)']
values = [train_acc[-1], val_acc[-1], best_val_acc, best_val_loss * 10]
colors = ['steelblue', 'forestgreen', 'gold', 'firebrick']
bars = plt.bar(metrics, values, color=colors, alpha=0.8)

for bar, val in zip(bars, values):
    plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
             f'{val:.2f}' if val > 1 else f'{val:.4f}',
             ha='center', va='bottom', fontsize=11, fontweight='bold')

plt.ylabel('Value')
plt.title('Final Training Metrics')
plt.grid(axis='y', alpha=0.3)

plt.suptitle('Convergence Analysis', fontsize=14, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig(OUTPUT_DIR / 'convergence_analysis.png', dpi=300, bbox_inches='tight')
plt.close()
print(f"     Saved to: {OUTPUT_DIR / 'convergence_analysis.png'}")

# ============================================
# Print Summary
# ============================================
print("\n" + "="*70)
print("  TRAINING CURVES SUMMARY")
print("="*70)
print(f"\nTotal Epochs: {len(epochs)}")
print(f"\nFinal Metrics:")
print(f"  Training Accuracy:   {train_acc[-1]:.2f}%")
print(f"  Validation Accuracy: {val_acc[-1]:.2f}%")
print(f"  Training Loss:       {train_loss[-1]:.4f}")
print(f"  Validation Loss:     {val_loss[-1]:.4f}")
print(f"\nBest Metrics:")
print(f"  Best Validation Accuracy: {best_val_acc:.2f}% (Epoch {best_val_acc_epoch})")
print(f"  Best Validation Loss:     {best_val_loss:.4f} (Epoch {best_val_loss_epoch})")
print(f"\nOverfitting Analysis:")
final_gap = train_acc[-1] - val_acc[-1]
print(f"  Final Train-Val Gap: {final_gap:.2f}%")
if final_gap < 5:
    print(f"  ✓ Model is well-generalized (gap < 5%)")
elif final_gap < 10:
    print(f"  ⚠ Model shows slight overfitting (gap 5-10%)")
else:
    print(f"  ⚠ Model is overfitting (gap > 10%)")

print()
print("="*70)
print(f"\n✓ All training curve plots saved to: {OUTPUT_DIR}")
print("\nGenerated files:")
for f in sorted(OUTPUT_DIR.glob('*.png')):
    if 'training' in f.name or 'curve' in f.name or 'convergence' in f.name:
        print(f"  - {f.name}")
print()
