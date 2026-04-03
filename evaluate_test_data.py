"""
VillageCrop - Test on New Unseen Dataset
Evaluates the model on the Fruit And Vegetable Diseases Dataset
Maps new dataset classes to closest matching trained model classes
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
    confusion_matrix, classification_report, accuracy_score
)
import matplotlib.pyplot as plt
import seaborn as sns
from tqdm import tqdm
from collections import defaultdict

# -------------------- Configuration --------------------
TEST_DATA_DIR = r"Test_data\Fruit And Vegetable Diseases Dataset"
MODEL_PATH = r"models\best_model.pth"
BATCH_SIZE = 256
IMG_SIZE = 224
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Print GPU info
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
else:
    print("WARNING: CUDA not available, using CPU (evaluation will be slower)")

# Enable optimizations
torch.backends.cuda.matmul.allow_tf32 = True
torch.backends.cudnn.benchmark = True

# -------------------- Class Mapping --------------------
# New dataset classes (28 classes: 14 crops × 2 states)
NEW_DATASET_CLASSES = [
    'Apple__Healthy', 'Apple__Rotten',
    'Banana__Healthy', 'Banana__Rotten',
    'Bellpepper__Healthy', 'Bellpepper__Rotten',
    'Carrot__Healthy', 'Carrot__Rotten',
    'Cucumber__Healthy', 'Cucumber__Rotten',
    'Grape__Healthy', 'Grape__Rotten',
    'Guava__Healthy', 'Guava__Rotten',
    'Jujube__Healthy', 'Jujube__Rotten',
    'Mango__Healthy', 'Mango__Rotten',
    'Orange__Healthy', 'Orange__Rotten',
    'Pomegranate__Healthy', 'Pomegranate__Rotten',
    'Potato__Healthy', 'Potato__Rotten',
    'Strawberry__Healthy', 'Strawberry__Rotten',
    'Tomato__Healthy', 'Tomato__Rotten'
]

# Mapping from new dataset classes to trained model classes
# The model was trained on PlantVillage dataset with specific disease classes
CLASS_MAPPING = {
    # Apple
    'Apple__Healthy': 'Apple___healthy',
    'Apple__Rotten': 'Apple___Apple_scab',  # Map rotten to most common apple disease
    
    # Banana (not in training data - will use closest match)
    'Banana__Healthy': 'Apple___healthy',  # No banana in training, use generic healthy
    'Banana__Rotten': 'Apple___Apple_scab',
    
    # Bellpepper -> Pepper bell
    'Bellpepper__Healthy': 'Pepper,_bell___healthy',
    'Bellpepper__Rotten': 'Pepper,_bell___Bacterial_spot',
    
    # Carrot (not in training data)
    'Carrot__Healthy': 'Apple___healthy',
    'Carrot__Rotten': 'Apple___Apple_scab',
    
    # Cucumber (not in training data)
    'Cucumber__Healthy': 'Apple___healthy',
    'Cucumber__Rotten': 'Tomato___Early_blight',
    
    # Grape
    'Grape__Healthy': 'Grape___healthy',
    'Grape__Rotten': 'Grape___Black_rot',
    
    # Guava (not in training data)
    'Guava__Healthy': 'Apple___healthy',
    'Guava__Rotten': 'Apple___Apple_scab',
    
    # Jujube (not in training data)
    'Jujube__Healthy': 'Apple___healthy',
    'Jujube__Rotten': 'Apple___Apple_scab',
    
    # Mango (not in training data)
    'Mango__Healthy': 'Apple___healthy',
    'Mango__Rotten': 'Apple___Apple_scab',
    
    # Orange
    'Orange__Healthy': 'Orange___Haunglongbing_(Citrus_greening)',  # Only orange class in training
    'Orange__Rotten': 'Orange___Haunglongbing_(Citrus_greening)',
    
    # Pomegranate (not in training data)
    'Pomegranate__Healthy': 'Apple___healthy',
    'Pomegranate__Rotten': 'Apple___Apple_scab',
    
    # Potato
    'Potato__Healthy': 'Potato___healthy',
    'Potato__Rotten': 'Potato___Early_blight',
    
    # Strawberry
    'Strawberry__Healthy': 'Strawberry___healthy',
    'Strawberry__Rotten': 'Strawberry___Leaf_scorch',
    
    # Tomato
    'Tomato__Healthy': 'Tomato___healthy',
    'Tomato__Rotten': 'Tomato___Early_blight',  # Most common tomato disease
}

# Reverse mapping: trained class -> index in new dataset
TRAINED_CLASSES = list(set(CLASS_MAPPING.values()))

print("\n" + "="*60)
print("CLASS MAPPING (New Dataset -> Trained Model)")
print("="*60)
for new_cls, trained_cls in CLASS_MAPPING.items():
    print(f"  {new_cls:<35} -> {trained_cls}")

# -------------------- Data Transformation --------------------
def transform(image):
    """Same transformation used during training"""
    image = image.resize((IMG_SIZE, IMG_SIZE))
    image_array = np.array(image).astype(np.float32) / 255.0
    mean = np.array([0.485, 0.456, 0.406]).reshape(1, 1, 3)
    std = np.array([0.229, 0.224, 0.225]).reshape(1, 1, 3)
    image_array = (image_array - mean) / std
    image_array = np.transpose(image_array, (2, 0, 1))
    return torch.from_numpy(image_array).float()

# -------------------- Dataset --------------------
class TestDataset(Dataset):
    def __init__(self, data_dir, classes, transform=None):
        self.data_dir = data_dir
        self.classes = classes
        self.transform = transform
        self.samples = []
        self.class_to_idx = {cls: idx for idx, cls in enumerate(classes)}
        
        for cls in classes:
            cls_dir = os.path.join(data_dir, cls)
            if os.path.isdir(cls_dir):
                for img_name in os.listdir(cls_dir):
                    if img_name.lower().endswith(('.png', '.jpg', '.jpeg')):
                        self.samples.append((os.path.join(cls_dir, img_name), self.class_to_idx[cls]))
        
        # Shuffle samples
        np.random.shuffle(self.samples)

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        img_path, label = self.samples[idx]
        try:
            image = Image.open(img_path).convert('RGB')
            if self.transform:
                image = self.transform(image)
            return image, label
        except Exception as e:
            # Return a blank image if there's an error
            print(f"Error loading {img_path}: {e}")
            return torch.zeros(3, IMG_SIZE, IMG_SIZE), label

# -------------------- Model Definition --------------------
class SimpleCNN(torch.nn.Module):
    def __init__(self, num_classes):
        super(SimpleCNN, self).__init__()
        self.features = torch.nn.Sequential(
            torch.nn.Conv2d(3, 32, 3, padding=1),
            torch.nn.BatchNorm2d(32),
            torch.nn.ReLU(inplace=True),
            torch.nn.Conv2d(32, 32, 3, padding=1),
            torch.nn.BatchNorm2d(32),
            torch.nn.ReLU(inplace=True),
            torch.nn.MaxPool2d(2, 2),
            torch.nn.Dropout2d(0.25),
            torch.nn.Conv2d(32, 64, 3, padding=1),
            torch.nn.BatchNorm2d(64),
            torch.nn.ReLU(inplace=True),
            torch.nn.Conv2d(64, 64, 3, padding=1),
            torch.nn.BatchNorm2d(64),
            torch.nn.ReLU(inplace=True),
            torch.nn.MaxPool2d(2, 2),
            torch.nn.Dropout2d(0.25),
            torch.nn.Conv2d(64, 128, 3, padding=1),
            torch.nn.BatchNorm2d(128),
            torch.nn.ReLU(inplace=True),
            torch.nn.Conv2d(128, 128, 3, padding=1),
            torch.nn.BatchNorm2d(128),
            torch.nn.ReLU(inplace=True),
            torch.nn.MaxPool2d(2, 2),
            torch.nn.Dropout2d(0.25),
            torch.nn.Conv2d(128, 256, 3, padding=1),
            torch.nn.BatchNorm2d(256),
            torch.nn.ReLU(inplace=True),
            torch.nn.Conv2d(256, 256, 3, padding=1),
            torch.nn.BatchNorm2d(256),
            torch.nn.ReLU(inplace=True),
            torch.nn.MaxPool2d(2, 2),
            torch.nn.Dropout2d(0.25),
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
print("\n" + "="*60)
print("LOADING MODEL")
print("="*60)

checkpoint = torch.load(MODEL_PATH, map_location='cpu', weights_only=False)
if isinstance(checkpoint, dict) and 'model_state_dict' in checkpoint:
    model_state = checkpoint['model_state_dict']
    saved_classes = checkpoint.get('classes', None)
else:
    model_state = checkpoint
    saved_classes = None

# Model uses 38 classes from PlantVillage
num_trained_classes = 38
model = SimpleCNN(num_trained_classes).to(DEVICE)
model.load_state_dict(model_state)
model.eval()
print(f"Model loaded: {MODEL_PATH}")
print(f"Model trained on {num_trained_classes} classes")

# -------------------- Load Test Data --------------------
print("\n" + "="*60)
print("LOADING TEST DATA")
print("="*60)

test_dataset = TestDataset(TEST_DATA_DIR, NEW_DATASET_CLASSES, transform=transform)
test_loader = DataLoader(test_dataset, batch_size=BATCH_SIZE, shuffle=False, num_workers=0)

print(f"Test dataset location: {TEST_DATA_DIR}")
print(f"Total test samples: {len(test_dataset)}")
print(f"Number of test classes: {len(NEW_DATASET_CLASSES)}")

# Count samples per class
class_counts = defaultdict(int)
for _, label in test_dataset.samples:
    class_counts[NEW_DATASET_CLASSES[label]] += 1

print("\nSamples per class:")
for cls, count in sorted(class_counts.items()):
    print(f"  {cls}: {count}")

# -------------------- Evaluation --------------------
print("\n" + "="*60)
print("EVALUATING MODEL ON TEST DATA")
print("="*60)

all_preds = []
all_labels = []
all_probs = []

with torch.no_grad():
    for images, labels in tqdm(test_loader, desc="Evaluating"):
        images = images.to(DEVICE)
        labels = labels.to(DEVICE)
        outputs = model(images)
        probs = torch.softmax(outputs, dim=1)
        _, predicted = torch.max(outputs, 1)
        all_preds.extend(predicted.cpu().numpy())
        all_labels.extend(labels.cpu().numpy())
        all_probs.extend(probs.cpu().numpy())

all_preds = np.array(all_preds)
all_labels = np.array(all_labels)
all_probs = np.array(all_probs)

# Map predictions to trained class names
pred_class_names = []
for pred_idx in all_preds:
    pred_class_names.append(saved_classes[pred_idx] if saved_classes else f"Class_{pred_idx}")

# Map true labels to new dataset class names
true_class_names = [NEW_DATASET_CLASSES[label] for label in all_labels]

# Map true labels to expected trained class names (what the model should predict)
expected_trained_names = [CLASS_MAPPING[NEW_DATASET_CLASSES[label]] for label in all_labels]

# -------------------- Calculate Metrics --------------------
print("\n" + "="*60)
print("RESULTS")
print("="*60)

# Overall accuracy (did model predict the mapped trained class?)
# Create label arrays for evaluation
true_labels_idx = []
for label in all_labels:
    new_class = NEW_DATASET_CLASSES[label]
    expected_trained = CLASS_MAPPING[new_class]
    if saved_classes and expected_trained in saved_classes:
        true_labels_idx.append(saved_classes.index(expected_trained))
    else:
        true_labels_idx.append(-1)  # Unknown class

# Filter out unknown classes
valid_indices = [i for i, idx in enumerate(true_labels_idx) if idx != -1]
filtered_preds = all_preds[valid_indices]
filtered_true = np.array([true_labels_idx[i] for i in valid_indices])

if len(valid_indices) > 0:
    accuracy = accuracy_score(filtered_true, filtered_preds)
    print(f"\nOverall Accuracy: {accuracy:.4f} ({accuracy*100:.2f}%)")
    print(f"Valid samples (with known class mapping): {len(valid_indices)} / {len(all_labels)}")
    
    # Per-class metrics
    print("\n" + "-"*60)
    print("PER-CLASS METRICS (New Dataset Classes)")
    print("-"*60)
    print(f"{'New Class':<35} {'Samples':<10} {'Correct':<10} {'Accuracy':<10}")
    print("-"*60)
    
    class_results = {}
    for new_class_idx, new_class in enumerate(NEW_DATASET_CLASSES):
        expected_trained = CLASS_MAPPING[new_class]
        if saved_classes and expected_trained in saved_classes:
            expected_idx = saved_classes.index(expected_trained)
        else:
            continue
            
        # Get indices for this class
        class_indices = [i for i, label in enumerate(all_labels) if label == new_class_idx]
        if not class_indices:
            continue
            
        class_preds = all_preds[class_indices]
        correct = sum(1 for p in class_preds if p == expected_idx)
        total = len(class_preds)
        acc = correct / total if total > 0 else 0
        
        class_results[new_class] = {
            'samples': total,
            'correct': correct,
            'accuracy': acc,
            'expected_class': expected_trained
        }
        print(f"{new_class:<35} {total:<10} {correct:<10} {acc:.4f}")
    
    # Aggregate metrics
    print("\n" + "-"*60)
    print("AGGREGATE METRICS")
    print("-"*60)
    
    # Macro averages
    accuracies = [r['accuracy'] for r in class_results.values()]
    macro_avg = np.mean(accuracies)
    weighted_avg = np.average(accuracies, weights=[r['samples'] for r in class_results.values()])
    
    print(f"Macro Average Accuracy: {macro_avg:.4f}")
    print(f"Weighted Average Accuracy: {weighted_avg:.4f}")
    
    # Calculate F1, Precision, Recall using sklearn
    print("\n" + "-"*60)
    print("SKLEARN METRICS (Multi-class)")
    print("-"*60)
    
    f1_macro = f1_score(filtered_true, filtered_preds, average='macro')
    f1_weighted = f1_score(filtered_true, filtered_preds, average='weighted')
    precision_macro = precision_score(filtered_true, filtered_preds, average='macro')
    precision_weighted = precision_score(filtered_true, filtered_preds, average='weighted')
    recall_macro = recall_score(filtered_true, filtered_preds, average='macro')
    recall_weighted = recall_score(filtered_true, filtered_preds, average='weighted')
    
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
    if saved_classes:
        target_names = [saved_classes[i] if i < len(saved_classes) else f"Class_{i}" for i in range(num_trained_classes)]
        print(classification_report(filtered_true, filtered_preds, target_names=target_names[:len(set(filtered_true))], zero_division=0))
    
    # Confusion Matrix
    print("\n" + "-"*60)
    print("CONFUSION MATRIX")
    print("-"*60)
    
    cm = confusion_matrix(filtered_true, filtered_preds, labels=range(num_trained_classes))
    
    # Save confusion matrix
    plt.figure(figsize=(20, 16))
    
    # Get labels that were actually predicted or true
    active_labels = sorted(set(filtered_true) | set(filtered_preds))
    active_label_names = [saved_classes[i] if saved_classes and i < len(saved_classes) else f"Class_{i}" for i in active_labels]
    
    # Shorten names for display
    def shorten_name(name):
        parts = name.split('___')
        if len(parts) == 2:
            plant = parts[0][:10]
            disease = parts[1][:15]
            return f"{plant}___{disease}"
        return name[:25]
    
    short_names = [shorten_name(n) for n in active_label_names]
    
    cm_active = cm[active_labels][:, active_labels]
    
    sns.heatmap(cm_active, annot=False, fmt='d', cmap='Blues',
                xticklabels=short_names, yticklabels=short_names,
                cbar_kws={'label': 'Count'})
    plt.title('Confusion Matrix - Test Data', fontsize=16, fontweight='bold')
    plt.xlabel('Predicted Class', fontsize=12)
    plt.ylabel('Expected Class (Mapped)', fontsize=12)
    plt.xticks(rotation=45, ha='right', fontsize=7)
    plt.yticks(fontsize=7)
    plt.tight_layout()
    plt.savefig('test_confusion_matrix.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("Confusion matrix saved to: test_confusion_matrix.png")
    
    # Save normalized confusion matrix
    cm_normalized = cm_active.astype('float') / cm_active.sum(axis=1, keepdims=True)
    plt.figure(figsize=(20, 16))
    sns.heatmap(cm_normalized, annot=False, fmt='.2f', cmap='Blues',
                xticklabels=short_names, yticklabels=short_names,
                cbar_kws={'label': 'Proportion'})
    plt.title('Normalized Confusion Matrix - Test Data', fontsize=16, fontweight='bold')
    plt.xlabel('Predicted Class', fontsize=12)
    plt.ylabel('Expected Class (Mapped)', fontsize=12)
    plt.xticks(rotation=45, ha='right', fontsize=7)
    plt.yticks(fontsize=7)
    plt.tight_layout()
    plt.savefig('test_confusion_matrix_normalized.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("Normalized confusion matrix saved to: test_confusion_matrix_normalized.png")
    
    # Save metrics to file
    print("\nSaving metrics to file...")
    metrics_text = f"""
AGRODOC-AI - TEST DATA EVALUATION RESULTS
==========================================
Model: {MODEL_PATH}
Test Data: {TEST_DATA_DIR}
Device: {DEVICE}

DATASET INFORMATION
-------------------
Total Test Samples: {len(test_dataset)}
Number of Test Classes: {len(NEW_DATASET_CLASSES)}
Valid Samples (mapped to trained classes): {len(valid_indices)}

CLASS MAPPING
-------------
"""
    for new_cls, trained_cls in CLASS_MAPPING.items():
        metrics_text += f"  {new_cls:<35} -> {trained_cls}\n"
    
    metrics_text += f"""
OVERALL METRICS
---------------
Overall Accuracy: {accuracy:.4f} ({accuracy*100:.2f}%)

PER-CLASS RESULTS
-----------------
"""
    metrics_text += f"{'New Class':<35} {'Samples':<10} {'Correct':<10} {'Accuracy':<10}\n"
    metrics_text += "-" * 65 + "\n"
    for new_class, results in sorted(class_results.items()):
        metrics_text += f"{new_class:<35} {results['samples']:<10} {results['correct']:<10} {results['accuracy']:.4f}\n"
    
    metrics_text += f"""
AGGREGATE METRICS
-----------------
Macro Average Accuracy: {macro_avg:.4f}
Weighted Average Accuracy: {weighted_avg:.4f}

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
Shape: {cm_active.shape}
Saved as: test_confusion_matrix.png (absolute counts)
          test_confusion_matrix_normalized.png (proportions)
"""
    
    with open('test_data_metrics.txt', 'w', encoding='utf-8') as f:
        f.write(metrics_text)
    
    print("Metrics saved to: test_data_metrics.txt")
else:
    print("ERROR: No valid samples with known class mapping!")

print("\n" + "="*60)
print("EVALUATION COMPLETE")
print("="*60)
print(f"\nOutput files:")
print(f"  1. test_data_metrics.txt - All metrics in text format")
print(f"  2. test_confusion_matrix.png - Confusion matrix heatmap")
print(f"  3. test_confusion_matrix_normalized.png - Normalized CM")
