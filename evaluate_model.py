"""
VillageCrop - Model Evaluation Script
Evaluates the best trained model and computes performance metrics:
- F1 Score (macro, weighted, per-class)
- Precision (macro, weighted, per-class)
- Recall (macro, weighted, per-class)
- Confusion Matrix
"""

import os
# Fix for OpenMP conflict on Windows
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import torch
import numpy as np
from PIL import Image
from torch.utils.data import DataLoader, Dataset
from sklearn.metrics import (
    f1_score, precision_score, recall_score, 
    confusion_matrix, classification_report
)
import matplotlib.pyplot as plt
import seaborn as sns
from tqdm import tqdm

# -------------------- Configuration --------------------
DATA_DIR = r"data\villagecrop\plantvillage dataset\color"
MODEL_PATH = r"models\best_model.pth"
BATCH_SIZE = 256  # Larger batch for faster CPU evaluation
IMG_SIZE = 224
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Print GPU info
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
else:
    print("WARNING: CUDA not available, using CPU (evaluation will be slower)")

# Enable TF32 and benchmark mode for faster CPU/GPU computation
torch.backends.cuda.matmul.allow_tf32 = True
torch.backends.cudnn.benchmark = True

# Get classes - use all classes from the checkpoint
all_classes = sorted(os.listdir(DATA_DIR))

# We'll determine the classes from the checkpoint
checkpoint_for_classes = torch.load(MODEL_PATH, map_location='cpu', weights_only=False)
saved_classes = checkpoint_for_classes.get('classes', None)

if saved_classes:
    classes = saved_classes
    print(f"Using {len(classes)} classes from checkpoint")
else:
    # Fallback: filter to Apple, Grape, Tomato
    def filter_classes(subdirs):
        allowed_prefixes = ('Apple', 'Grape', 'Tomato')
        return [d for d in subdirs if d.startswith(allowed_prefixes)]
    classes = filter_classes(all_classes)
    print(f"Using filtered classes: {len(classes)}")

class_to_idx = {cls: idx for idx, cls in enumerate(classes)}
idx_to_class = {idx: cls for cls, idx in class_to_idx.items()}
num_classes = len(classes)

print(f"Device: {DEVICE}")
print(f"Number of classes: {num_classes}")
print(f"Classes: {classes}")

# -------------------- Dataset --------------------
class EvaluationDataset(Dataset):
    def __init__(self, data_dir, classes, class_to_idx, transform=None):
        self.data_dir = data_dir
        self.classes = classes
        self.class_to_idx = class_to_idx
        self.transform = transform
        self.samples = []

        for cls in classes:
            cls_dir = os.path.join(data_dir, cls)
            if os.path.isdir(cls_dir):
                for img_name in os.listdir(cls_dir):
                    if img_name.lower().endswith(('.png', '.jpg', '.jpeg')):
                        self.samples.append((os.path.join(cls_dir, img_name), class_to_idx[cls]))

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        img_path, label = self.samples[idx]
        image = Image.open(img_path).convert('RGB')
        if self.transform:
            image = self.transform(image)
        return image, label

# -------------------- Data Transformation --------------------
def transform(image):
    image = image.resize((IMG_SIZE, IMG_SIZE))
    image_array = np.array(image).astype(np.float32) / 255.0
    mean = np.array([0.485, 0.456, 0.406]).reshape(1, 1, 3)
    std = np.array([0.229, 0.224, 0.225]).reshape(1, 1, 3)
    image_array = (image_array - mean) / std
    image_array = np.transpose(image_array, (2, 0, 1))
    return torch.from_numpy(image_array).float()

# -------------------- Model Definition --------------------
class SimpleCNN(torch.nn.Module):
    def __init__(self, num_classes):
        super(SimpleCNN, self).__init__()
        self.features = torch.nn.Sequential(
            # Block 1: 224 -> 112
            torch.nn.Conv2d(3, 32, 3, padding=1),
            torch.nn.BatchNorm2d(32),
            torch.nn.ReLU(inplace=True),
            torch.nn.Conv2d(32, 32, 3, padding=1),
            torch.nn.BatchNorm2d(32),
            torch.nn.ReLU(inplace=True),
            torch.nn.MaxPool2d(2, 2),
            torch.nn.Dropout2d(0.25),

            # Block 2: 112 -> 56
            torch.nn.Conv2d(32, 64, 3, padding=1),
            torch.nn.BatchNorm2d(64),
            torch.nn.ReLU(inplace=True),
            torch.nn.Conv2d(64, 64, 3, padding=1),
            torch.nn.BatchNorm2d(64),
            torch.nn.ReLU(inplace=True),
            torch.nn.MaxPool2d(2, 2),
            torch.nn.Dropout2d(0.25),

            # Block 3: 56 -> 28
            torch.nn.Conv2d(64, 128, 3, padding=1),
            torch.nn.BatchNorm2d(128),
            torch.nn.ReLU(inplace=True),
            torch.nn.Conv2d(128, 128, 3, padding=1),
            torch.nn.BatchNorm2d(128),
            torch.nn.ReLU(inplace=True),
            torch.nn.MaxPool2d(2, 2),
            torch.nn.Dropout2d(0.25),

            # Block 4: 28 -> 14
            torch.nn.Conv2d(128, 256, 3, padding=1),
            torch.nn.BatchNorm2d(256),
            torch.nn.ReLU(inplace=True),
            torch.nn.Conv2d(256, 256, 3, padding=1),
            torch.nn.BatchNorm2d(256),
            torch.nn.ReLU(inplace=True),
            torch.nn.MaxPool2d(2, 2),
            torch.nn.Dropout2d(0.25),

            # Block 5: 14 -> 7
            torch.nn.Conv2d(256, 512, 3, padding=1),
            torch.nn.BatchNorm2d(512),
            torch.nn.ReLU(inplace=True),
            torch.nn.Conv2d(512, 512, 3, padding=1),
            torch.nn.BatchNorm2d(512),
            torch.nn.ReLU(inplace=True),
            torch.nn.AdaptiveAvgPool2d((7, 7)),
        )

        self.classifier = torch.nn.Sequential(
            torch.nn.Flatten(),
            torch.nn.Linear(512 * 7 * 7, 1024),
            torch.nn.ReLU(inplace=True),
            torch.nn.Dropout(0.5),
            torch.nn.Linear(1024, num_classes)
        )

    def forward(self, x):
        x = self.features(x)
        x = self.classifier(x)
        return x

# -------------------- Load Model --------------------
print("\nLoading model...")
# Checkpoint already loaded for classes, reuse it
if isinstance(checkpoint_for_classes, dict) and 'model_state_dict' in checkpoint_for_classes:
    model_state = checkpoint_for_classes['model_state_dict']
elif isinstance(checkpoint_for_classes, dict):
    model_state = checkpoint_for_classes
else:
    model_state = checkpoint_for_classes

model = SimpleCNN(num_classes).to(DEVICE)
model.load_state_dict(model_state)
model.eval()
print(f"Model loaded from: {MODEL_PATH}")

# -------------------- Load Data --------------------
print("\nLoading dataset...")
dataset = EvaluationDataset(DATA_DIR, classes, class_to_idx, transform=transform)
loader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=False, num_workers=0)
print(f"Total samples: {len(dataset)}")

# -------------------- Evaluation --------------------
print("\nEvaluating model...")
all_preds = []
all_labels = []

with torch.no_grad():
    for images, labels in tqdm(loader, desc="Evaluating"):
        images = images.to(DEVICE)
        labels = labels.to(DEVICE)
        outputs = model(images)
        _, predicted = torch.max(outputs, 1)
        all_preds.extend(predicted.cpu().numpy())
        all_labels.extend(labels.cpu().numpy())

all_preds = np.array(all_preds)
all_labels = np.array(all_labels)

# -------------------- Calculate Metrics --------------------
print("\n" + "="*60)
print("PERFORMANCE METRICS")
print("="*60)

# Overall accuracy
accuracy = (all_preds == all_labels).sum() / len(all_labels)
print(f"\nOverall Accuracy: {accuracy:.4f} ({accuracy*100:.2f}%)")

# Per-class metrics
print("\n" + "-"*60)
print("PER-CLASS METRICS")
print("-"*60)
print(f"{'Class':<50} {'Precision':<12} {'Recall':<12} {'F1':<12}")
print("-"*60)

precision_per_class = precision_score(all_labels, all_preds, average=None, labels=range(num_classes))
recall_per_class = recall_score(all_labels, all_preds, average=None, labels=range(num_classes))
f1_per_class = f1_score(all_labels, all_preds, average=None, labels=range(num_classes))

for i, cls in enumerate(classes):
    print(f"{cls:<50} {precision_per_class[i]:<12.4f} {recall_per_class[i]:<12.4f} {f1_per_class[i]:<12.4f}")

# Macro averages
print("\n" + "-"*60)
print("AGGREGATE METRICS")
print("-"*60)
precision_macro = precision_score(all_labels, all_preds, average='macro')
recall_macro = recall_score(all_labels, all_preds, average='macro')
f1_macro = f1_score(all_labels, all_preds, average='macro')

precision_weighted = precision_score(all_labels, all_preds, average='weighted')
recall_weighted = recall_score(all_labels, all_preds, average='weighted')
f1_weighted = f1_score(all_labels, all_preds, average='weighted')

print(f"\nMacro Average:")
print(f"  Precision: {precision_macro:.4f}")
print(f"  Recall:    {recall_macro:.4f}")
print(f"  F1 Score:  {f1_macro:.4f}")

print(f"\nWeighted Average:")
print(f"  Precision: {precision_weighted:.4f}")
print(f"  Recall:    {recall_weighted:.4f}")
print(f"  F1 Score:  {f1_weighted:.4f}")

# Classification report
print("\n" + "-"*60)
print("CLASSIFICATION REPORT")
print("-"*60)
print(classification_report(all_labels, all_preds, target_names=classes))

# Confusion Matrix
print("\n" + "-"*60)
print("CONFUSION MATRIX (CM)")
print("-"*60)
cm = confusion_matrix(all_labels, all_preds, labels=range(num_classes))
print("\nConfusion Matrix Shape:", cm.shape)
print("Note: Full matrix saved as heatmap image")

# -------------------- Save Confusion Matrix Heatmap --------------------
print("\nSaving confusion matrix visualization...")

# Create figure with better sizing
plt.figure(figsize=(20, 16))

# Shorten class names for display
def shorten_name(name):
    parts = name.split('___')
    if len(parts) == 2:
        plant = parts[0][:8]  # First 8 chars of plant name
        disease = parts[1][:15]  # First 15 chars of disease
        return f"{plant}___{disease}"
    return name[:25]

short_names = [shorten_name(cls) for cls in classes]

# Plot heatmap
sns.heatmap(cm, annot=False, fmt='d', cmap='Blues', 
            xticklabels=short_names, yticklabels=short_names,
            cbar_kws={'label': 'Count'})
plt.title('Confusion Matrix', fontsize=16, fontweight='bold')
plt.xlabel('Predicted Label', fontsize=12)
plt.ylabel('True Label', fontsize=12)
plt.xticks(rotation=45, ha='right', fontsize=8)
plt.yticks(fontsize=8)
plt.tight_layout()
plt.savefig('confusion_matrix.png', dpi=150, bbox_inches='tight')
plt.close()
print("Confusion matrix saved to: confusion_matrix.png")

# Save normalized confusion matrix
cm_normalized = cm.astype('float') / cm.sum(axis=1, keepdims=True)
plt.figure(figsize=(20, 16))
sns.heatmap(cm_normalized, annot=False, fmt='.2f', cmap='Blues',
            xticklabels=short_names, yticklabels=short_names,
            cbar_kws={'label': 'Proportion'})
plt.title('Normalized Confusion Matrix', fontsize=16, fontweight='bold')
plt.xlabel('Predicted Label', fontsize=12)
plt.ylabel('True Label', fontsize=12)
plt.xticks(rotation=45, ha='right', fontsize=8)
plt.yticks(fontsize=8)
plt.tight_layout()
plt.savefig('confusion_matrix_normalized.png', dpi=150, bbox_inches='tight')
plt.close()
print("Normalized confusion matrix saved to: confusion_matrix_normalized.png")

# -------------------- Save Metrics to File --------------------
print("\nSaving metrics to file...")
metrics_text = f"""
AGRODOC-AI MODEL EVALUATION RESULTS
=====================================
Model: {MODEL_PATH}
Date: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'}

DATASET INFORMATION
-------------------
Total Samples: {len(dataset)}
Number of Classes: {num_classes}
Classes: {', '.join(classes)}

OVERALL METRICS
---------------
Accuracy: {accuracy:.4f} ({accuracy*100:.2f}%)

PER-CLASS METRICS (P: Precision, R: Recall, F1: F1 Score)
----------------------------------------------------------
"""

metrics_text += f"{'Class':<50} {'P':<10} {'R':<10} {'F1':<10}\n"
metrics_text += "-" * 80 + "\n"
for i, cls in enumerate(classes):
    metrics_text += f"{cls:<50} {precision_per_class[i]:<10.4f} {recall_per_class[i]:<10.4f} {f1_per_class[i]:<10.4f}\n"

metrics_text += f"""
AGGREGATE METRICS
-----------------
Macro Average:
  Precision (P): {precision_macro:.4f}
  Recall (R):    {recall_macro:.4f}
  F1 Score:      {f1_macro:.4f}

Weighted Average:
  Precision (P): {precision_weighted:.4f}
  Recall (R):    {recall_weighted:.4f}
  F1 Score:      {f1_weighted:.4f}

CONFUSION MATRIX (CM)
---------------------
Shape: {cm.shape}
Saved as: confusion_matrix.png (absolute counts)
          confusion_matrix_normalized.png (proportions)

CLASSIFICATION REPORT
---------------------
{classification_report(all_labels, all_preds, target_names=classes)}
"""

with open('model_metrics.txt', 'w', encoding='utf-8') as f:
    f.write(metrics_text)

print("Metrics saved to: model_metrics.txt")
print("\n" + "="*60)
print("EVALUATION COMPLETE")
print("="*60)
print(f"\nOutput files:")
print(f"  1. model_metrics.txt - All metrics in text format")
print(f"  2. confusion_matrix.png - Confusion matrix heatmap")
print(f"  3. confusion_matrix_normalized.png - Normalized confusion matrix")
