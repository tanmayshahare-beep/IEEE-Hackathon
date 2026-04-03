"""
Plot EfficientNet-B0 Training Performance Metrics

Generates for the NEW model (train_efficientnet_b0_apple_grape_tomato.py):
1. Confusion Matrix heatmap
2. Per-class F1-Score bar chart
3. Per-class Precision/Recall comparison
4. Overall metrics summary
5. Class-wise accuracy distribution
6. Support vs F1-Score scatter

Saves to: models/plots2/
"""

import json
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Configuration
MODEL_DIR = Path(__file__).parent / 'models'
METRICS_FILE = MODEL_DIR / 'performance_metrics_apple_grape_tomato.json'
OUTPUT_DIR = MODEL_DIR / 'plots2'  # Different folder for new model
OUTPUT_DIR.mkdir(exist_ok=True)

# Load metrics
print(f"Loading metrics from: {METRICS_FILE}")
if not METRICS_FILE.exists():
    print(f"\n⚠️  Metrics file not found: {METRICS_FILE}")
    print("Please run training first: python train_efficientnet_b0_apple_grape_tomato.py")
    exit(1)

with open(METRICS_FILE, 'r') as f:
    metrics = json.load(f)

class_names = metrics['class_names']
confusion_matrix = np.array(metrics['confusion_matrix'])
overall_accuracy = metrics['overall_accuracy']
macro_f1 = metrics['macro_f1']
weighted_f1 = metrics['weighted_f1']
macro_precision = metrics.get('macro_precision', 0)
macro_recall = metrics.get('macro_recall', 0)

print(f"Loaded metrics for {len(class_names)} classes")
print(f"Overall Accuracy: {overall_accuracy:.2f}%")
print(f"Macro F1-Score:   {macro_f1:.4f}")
print(f"Weighted F1-Score: {weighted_f1:.4f}")

# Calculate per-class metrics from confusion matrix
def calculate_per_class_metrics(cm):
    """Calculate precision, recall, F1 for each class"""
    n_classes = cm.shape[0]
    precision = np.zeros(n_classes)
    recall = np.zeros(n_classes)
    f1 = np.zeros(n_classes)
    support = np.zeros(n_classes)

    for i in range(n_classes):
        tp = cm[i, i]
        fp = cm[:, i].sum() - tp
        fn = cm[i, :].sum() - tp

        precision[i] = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall[i] = tp / (tp + fn) if (tp + fn) > 0 else 0

        if precision[i] + recall[i] > 0:
            f1[i] = 2 * (precision[i] * recall[i]) / (precision[i] + recall[i])
        else:
            f1[i] = 0

        support[i] = tp + fn

    return precision, recall, f1, support

precision, recall, f1, support = calculate_per_class_metrics(confusion_matrix)

# Normalize confusion matrix for visualization
cm_normalized = confusion_matrix.astype('float') / confusion_matrix.sum(axis=1)[:, np.newaxis]
cm_normalized = np.nan_to_num(cm_normalized)  # Handle division by zero

print("\nGenerating plots...")

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.facecolor'] = 'white'
plt.rcParams['axes.facecolor'] = 'white'

# ============================================
# Plot 1: Confusion Matrix
# ============================================
print("  1. Confusion Matrix...")
plt.figure(figsize=(16, 14))
sns.heatmap(cm_normalized, annot=False, cmap='YlOrRd', fmt='.2f',
            xticklabels=class_names, yticklabels=class_names,
            cbar_kws={'label': 'Normalized Frequency'})
plt.title('Confusion Matrix - EfficientNet-B0 (Apple/Grape/Tomato)', fontsize=16, pad=20, fontweight='bold')
plt.xlabel('Predicted Label', fontsize=12)
plt.ylabel('True Label', fontsize=12)
plt.xticks(rotation=45, ha='right', fontsize=8)
plt.yticks(rotation=0, fontsize=8)
plt.tight_layout()
plt.savefig(OUTPUT_DIR / 'confusion_matrix.png', dpi=300, bbox_inches='tight')
plt.close()
print(f"     Saved to: {OUTPUT_DIR / 'confusion_matrix.png'}")

# ============================================
# Plot 2: Per-Class F1-Score (Sorted)
# ============================================
print("  2. Per-Class F1-Score...")
sorted_indices = np.argsort(f1)[::-1]  # Sort descending

plt.figure(figsize=(14, 8))
colors = []
for f1_score in f1[sorted_indices]:
    if f1_score < 0.7:
        colors.append('#ef4444')  # Red - Poor
    elif f1_score < 0.85:
        colors.append('#facc15')  # Yellow - Moderate
    else:
        colors.append('#22c55e')  # Green - Good

bars = plt.barh(range(len(class_names)), f1[sorted_indices], color=colors)

plt.yticks(range(len(class_names)), [class_names[i] for i in sorted_indices], fontsize=9)
plt.xlabel('F1-Score', fontsize=12)
plt.title('Per-Class F1-Score - EfficientNet-B0 (Sorted by Performance)', fontsize=14, pad=20, fontweight='bold')
plt.xlim(0, 1.0)

# Add value labels
for i, v in enumerate(f1[sorted_indices]):
    plt.text(v + 0.01, i, f'{v:.3f}', va='center', fontsize=8)

plt.grid(axis='x', alpha=0.3, linestyle='--')
plt.tight_layout()
plt.savefig(OUTPUT_DIR / 'per_class_f1_score.png', dpi=300, bbox_inches='tight')
plt.close()
print(f"     Saved to: {OUTPUT_DIR / 'per_class_f1_score.png'}")

# ============================================
# Plot 3: Precision vs Recall Comparison
# ============================================
print("  3. Precision vs Recall...")
x = np.arange(len(class_names))
width = 0.35

plt.figure(figsize=(16, 8))
bars1 = plt.bar(x - width/2, precision, width, label='Precision', color='#3b82f6', alpha=0.8)
bars2 = plt.bar(x + width/2, recall, width, label='Recall', color='#22c55e', alpha=0.8)

plt.xlabel('Class', fontsize=12)
plt.ylabel('Score', fontsize=12)
plt.title('Precision vs Recall by Class - EfficientNet-B0', fontsize=14, pad=20, fontweight='bold')
plt.xticks(x, class_names, rotation=45, ha='right', fontsize=8)
plt.ylim(0, 1.0)
plt.legend(fontsize=12)
plt.grid(axis='y', alpha=0.3, linestyle='--')
plt.tight_layout()
plt.savefig(OUTPUT_DIR / 'precision_recall_comparison.png', dpi=300, bbox_inches='tight')
plt.close()
print(f"     Saved to: {OUTPUT_DIR / 'precision_recall_comparison.png'}")

# ============================================
# Plot 4: Overall Metrics Summary
# ============================================
print("  4. Overall Metrics Summary...")
metrics_names = ['Overall\nAccuracy', 'Macro\nF1', 'Weighted\nF1', 'Macro\nPrecision', 'Macro\nRecall']
metrics_values = [overall_accuracy/100, macro_f1, weighted_f1, macro_precision, macro_recall]

plt.figure(figsize=(10, 6))
colors = ['#eab308', '#22c55e', '#3b82f6', '#f97316', '#a855f7']
bars = plt.bar(metrics_names, metrics_values, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)

plt.ylabel('Score', fontsize=12)
plt.title('Overall Performance Metrics - EfficientNet-B0', fontsize=14, pad=20, fontweight='bold')
plt.ylim(0, 1.0)

# Add value labels
for bar, value in zip(bars, metrics_values):
    plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
             f'{value:.3f}', ha='center', va='bottom', fontsize=11, fontweight='bold')

plt.grid(axis='y', alpha=0.3, linestyle='--')
plt.tight_layout()
plt.savefig(OUTPUT_DIR / 'overall_metrics.png', dpi=300, bbox_inches='tight')
plt.close()
print(f"     Saved to: {OUTPUT_DIR / 'overall_metrics.png'}")

# ============================================
# Plot 5: Class-wise Accuracy Distribution
# ============================================
print("  5. Class-wise Accuracy Distribution...")
class_accuracy = np.diag(confusion_matrix) / confusion_matrix.sum(axis=1)
class_accuracy = np.nan_to_num(class_accuracy)

plt.figure(figsize=(14, 8))
sorted_acc_indices = np.argsort(class_accuracy)[::-1]

colors = []
for acc in class_accuracy[sorted_acc_indices]:
    if acc < 0.7:
        colors.append('#ef4444')  # Red - Poor
    elif acc < 0.85:
        colors.append('#facc15')  # Yellow - Moderate
    else:
        colors.append('#22c55e')  # Green - Good

bars = plt.barh(range(len(class_names)), class_accuracy[sorted_acc_indices], color=colors)

plt.yticks(range(len(class_names)), [class_names[i] for i in sorted_acc_indices], fontsize=9)
plt.xlabel('Class Accuracy', fontsize=12)
plt.title('Class-wise Accuracy Distribution - EfficientNet-B0 (Sorted)', fontsize=14, pad=20, fontweight='bold')
plt.xlim(0, 1.0)

# Add value labels
for i, v in enumerate(class_accuracy[sorted_acc_indices]):
    plt.text(v + 0.01, i, f'{v:.3f}', va='center', fontsize=8)

plt.grid(axis='x', alpha=0.3, linestyle='--')
plt.tight_layout()
plt.savefig(OUTPUT_DIR / 'class_accuracy_distribution.png', dpi=300, bbox_inches='tight')
plt.close()
print(f"     Saved to: {OUTPUT_DIR / 'class_accuracy_distribution.png'}")

# ============================================
# Plot 6: Support vs F1-Score (Scatter)
# ============================================
print("  6. Support vs F1-Score Scatter...")
plt.figure(figsize=(12, 8))

# Normalize support for better visualization
support_normalized = support / support.max()

scatter = plt.scatter(support, f1, s=support_normalized*200, alpha=0.6,
                      c=f1, cmap='RdYlGn', vmin=0.5, vmax=1.0, edgecolors='black', linewidth=0.5)

# Add labels for worst performing classes
for i, (s, f, name) in enumerate(zip(support, f1, class_names)):
    if f < 0.85:  # Label poor performers
        plt.annotate(name[:30], (s, f), fontsize=7,
                    xytext=(5, 5), textcoords='offset points',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7))

plt.xlabel('Support (Number of Samples)', fontsize=12)
plt.ylabel('F1-Score', fontsize=12)
plt.title('Support vs F1-Score - EfficientNet-B0 (Bubble Size = Sample Count)', fontsize=14, pad=20, fontweight='bold')
plt.grid(alpha=0.3, linestyle='--')
plt.colorbar(scatter, label='F1-Score')
plt.tight_layout()
plt.savefig(OUTPUT_DIR / 'support_vs_f1.png', dpi=300, bbox_inches='tight')
plt.close()
print(f"     Saved to: {OUTPUT_DIR / 'support_vs_f1.png'}")

# ============================================
# Plot 7: Training Curves (if available)
# ============================================
HISTORY_FILE = MODEL_DIR / 'training_history_efficientnet_b0.json'
if HISTORY_FILE.exists():
    print("  7. Training Curves...")
    with open(HISTORY_FILE, 'r') as f:
        history = json.load(f)
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # Plot 1: Loss curves
    axes[0, 0].plot(history['train_loss'], label='Train Loss', color='#3b82f6', linewidth=2)
    axes[0, 0].plot(history['val_loss'], label='Val Loss', color='#ef4444', linewidth=2)
    axes[0, 0].set_xlabel('Epoch', fontsize=12)
    axes[0, 0].set_ylabel('Loss', fontsize=12)
    axes[0, 0].set_title('Training and Validation Loss', fontsize=14, fontweight='bold')
    axes[0, 0].legend(fontsize=11)
    axes[0, 0].grid(alpha=0.3, linestyle='--')
    
    # Plot 2: Accuracy curves
    axes[0, 1].plot(history['train_acc'], label='Train Accuracy', color='#22c55e', linewidth=2)
    axes[0, 1].plot(history['val_acc'], label='Val Accuracy', color='#3b82f6', linewidth=2)
    axes[0, 1].set_xlabel('Epoch', fontsize=12)
    axes[0, 1].set_ylabel('Accuracy (%)', fontsize=12)
    axes[0, 1].set_title('Training and Validation Accuracy', fontsize=14, fontweight='bold')
    axes[0, 1].legend(fontsize=11)
    axes[0, 1].grid(alpha=0.3, linestyle='--')
    
    # Plot 3: Learning Rate
    if 'learning_rates' in history:
        axes[1, 0].plot(history['learning_rates'], color='#f97316', linewidth=2)
        axes[1, 0].set_xlabel('Epoch', fontsize=12)
        axes[1, 0].set_ylabel('Learning Rate', fontsize=12)
        axes[1, 0].set_title('Learning Rate Schedule', fontsize=14, fontweight='bold')
        axes[1, 0].grid(alpha=0.3, linestyle='--')
        axes[1, 0].set_yscale('log')
    
    # Plot 4: Train-Val Gap
    gap = np.array(history['train_acc']) - np.array(history['val_acc'])
    axes[1, 1].plot(gap, color='#a855f7', linewidth=2)
    axes[1, 1].axhline(y=3, color='#22c55e', linestyle='--', label='Excellent (<3%)', alpha=0.7)
    axes[1, 1].axhline(y=7, color='#facc15', linestyle='--', label='Moderate (3-7%)', alpha=0.7)
    axes[1, 1].set_xlabel('Epoch', fontsize=12)
    axes[1, 1].set_ylabel('Accuracy Gap (%)', fontsize=12)
    axes[1, 1].set_title('Train-Validation Gap (Overfitting Indicator)', fontsize=14, fontweight='bold')
    axes[1, 1].legend(fontsize=10)
    axes[1, 1].grid(alpha=0.3, linestyle='--')
    
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'training_curves.png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f"     Saved to: {OUTPUT_DIR / 'training_curves.png'}")
else:
    print("  7. Skipping training curves (history file not found)")

# ============================================
# Print Summary Report
# ============================================
print("\n" + "="*70)
print("  EFFICIENTNET-B0 PERFORMANCE SUMMARY")
print("  (50% Apple/Grape/Tomato Data)")
print("="*70)
print(f"\nOverall Accuracy: {overall_accuracy:.2f}%")
print(f"Macro F1-Score:   {macro_f1:.4f}")
print(f"Weighted F1-Score: {weighted_f1:.4f}")
print(f"Macro Precision:  {macro_precision:.4f}")
print(f"Macro Recall:     {macro_recall:.4f}")
print()

# Best and worst performing classes
best_indices = np.argsort(f1)[::-1][:5]
worst_indices = np.argsort(f1)[:5]

print("Top 5 Best Performing Classes:")
for i, idx in enumerate(best_indices, 1):
    print(f"  {i}. {class_names[idx]}: F1={f1[idx]:.3f}, Acc={class_accuracy[idx]:.3f}")

print("\nBottom 5 Worst Performing Classes:")
for i, idx in enumerate(worst_indices, 1):
    print(f"  {i}. {class_names[idx]}: F1={f1[idx]:.3f}, Acc={class_accuracy[idx]:.3f}")

print()
print("="*70)
print(f"\n✓ All plots saved to: {OUTPUT_DIR}")
print("\nGenerated files:")
for f in sorted(OUTPUT_DIR.glob('*.png')):
    print(f"  - {f.name}")
print()

# Overfitting analysis
if HISTORY_FILE.exists():
    final_train_acc = history['train_acc'][-1]
    final_val_acc = history['val_acc'][-1]
    gap = final_train_acc - final_val_acc
    
    print("\nOverfitting Analysis:")
    print(f"  Final Train Accuracy: {final_train_acc:.2f}%")
    print(f"  Final Val Accuracy:   {final_val_acc:.2f}%")
    print(f"  Gap: {gap:.2f}%")
    
    if gap < 3:
        print(f"  ✓ Excellent! Model is well-regularized (gap < 3%)")
    elif gap < 7:
        print(f"  ✓ Good! Moderate gap (3-7%)")
    else:
        print(f"  ⚠ Warning: Some overfitting detected (gap > 7%)")
    
    print()
