"""
Plot Transfer Learning Performance Metrics

Generates:
1. Confusion Matrix heatmap
2. Per-class F1-Score bar chart
3. Per-class Precision/Recall comparison
4. Overall metrics summary
5. Class-wise accuracy distribution
"""

import json
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Configuration
MODEL_DIR = Path(__file__).parent / 'models'
METRICS_FILE = MODEL_DIR / 'performance_metrics.json'
OUTPUT_DIR = MODEL_DIR / 'plots'
OUTPUT_DIR.mkdir(exist_ok=True)

# Load metrics
print(f"Loading metrics from: {METRICS_FILE}")
with open(METRICS_FILE, 'r') as f:
    metrics = json.load(f)

class_names = metrics['class_names']
confusion_matrix = np.array(metrics['confusion_matrix'])
overall_accuracy = metrics['overall_accuracy']
macro_f1 = metrics['macro_f1']
weighted_f1 = metrics['weighted_f1']

print(f"Loaded metrics for {len(class_names)} classes")
print(f"Overall Accuracy: {overall_accuracy:.2f}%")

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

# ============================================
# Plot 1: Confusion Matrix
# ============================================
print("  1. Confusion Matrix...")
plt.figure(figsize=(16, 14))
sns.heatmap(cm_normalized, annot=False, cmap='Blues', fmt='.2f',
            xticklabels=class_names, yticklabels=class_names,
            cbar_kws={'label': 'Normalized Frequency'})
plt.title('Confusion Matrix - Transfer Learning Performance', fontsize=16, pad=20)
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
sorted_indices = np.argsort(f1)
sorted_indices = sorted_indices[::-1]  # Sort descending

plt.figure(figsize=(14, 8))
colors = plt.cm.viridis(np.linspace(0.2, 0.8, len(class_names)))
bars = plt.barh(range(len(class_names)), f1[sorted_indices], color=colors)

# Color coding
for i, (idx, f1_score) in enumerate(zip(sorted_indices, f1[sorted_indices])):
    if f1_score < 0.7:
        bars[i].set_color('#ef4444')  # Red - Poor
    elif f1_score < 0.85:
        bars[i].set_color('#facc15')  # Yellow - Moderate
    else:
        bars[i].set_color('#22c55e')  # Green - Good

plt.yticks(range(len(class_names)), [class_names[i] for i in sorted_indices], fontsize=9)
plt.xlabel('F1-Score', fontsize=12)
plt.title('Per-Class F1-Score (Sorted by Performance)', fontsize=14, pad=20)
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
plt.title('Precision vs Recall by Class', fontsize=14, pad=20)
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
metrics_values = [overall_accuracy/100, macro_f1, weighted_f1, 
                  metrics.get('macro_precision', precision.mean()), 
                  metrics.get('macro_recall', recall.mean())]

plt.figure(figsize=(10, 6))
colors = ['#eab308', '#22c55e', '#3b82f6', '#f97316', '#a855f7']
bars = plt.bar(metrics_names, metrics_values, color=colors, alpha=0.8)

plt.ylabel('Score', fontsize=12)
plt.title('Overall Performance Metrics', fontsize=14, pad=20)
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
plt.title('Class-wise Accuracy Distribution (Sorted)', fontsize=14, pad=20)
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
                      c=f1, cmap='RdYlGn', vmin=0.5, vmax=1.0)

# Add labels for worst performing classes
for i, (s, f, name) in enumerate(zip(support, f1, class_names)):
    if f < 0.85:  # Label poor performers
        plt.annotate(name[:30], (s, f), fontsize=7, 
                    xytext=(5, 5), textcoords='offset points',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7))

plt.xlabel('Support (Number of Samples)', fontsize=12)
plt.ylabel('F1-Score', fontsize=12)
plt.title('Support vs F1-Score (Bubble Size = Sample Count)', fontsize=14, pad=20)
plt.grid(alpha=0.3, linestyle='--')
plt.colorbar(scatter, label='F1-Score')
plt.tight_layout()
plt.savefig(OUTPUT_DIR / 'support_vs_f1.png', dpi=300, bbox_inches='tight')
plt.close()
print(f"     Saved to: {OUTPUT_DIR / 'support_vs_f1.png'}")

# ============================================
# Print Summary Report
# ============================================
print("\n" + "="*70)
print("  PERFORMANCE SUMMARY")
print("="*70)
print(f"\nOverall Accuracy: {overall_accuracy:.2f}%")
print(f"Macro F1-Score:   {macro_f1:.4f}")
print(f"Weighted F1-Score: {weighted_f1:.4f}")
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
for f in OUTPUT_DIR.glob('*.png'):
    print(f"  - {f.name}")
print()
