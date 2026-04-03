"""
Transfer Learning for Apple, Grape, Tomato Disease Detection

TRUE TRANSFER LEARNING (Not full retraining):
- Freezes EfficientNet-B0 backbone (pre-trained on ImageNet)
- Only trains the classifier head
- Fast training (~10-15 minutes)
- Minimal overfitting risk

DATASET:
- Only Apple, Grape, Tomato classes (18 classes total)
- 50% for training, 50% for validation
- Balanced split across all classes
"""

import os
# Fix for OpenMP library conflict
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import transforms, models
from torchvision.datasets import ImageFolder
from torch.utils.data import DataLoader, Subset
from torch.optim.lr_scheduler import ReduceLROnPlateau
from pathlib import Path
from datetime import datetime
import json
import random
import numpy as np
from PIL import Image

# Configuration
DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"Using device: {DEVICE}")

# Paths
BASE_DIR = Path(__file__).parent
DATASET_DIR = BASE_DIR / 'data' / 'processed_dataset' / 'train'
MODEL_DIR = BASE_DIR / 'models'
MODEL_DIR.mkdir(exist_ok=True)

# Only Apple, Grape, Tomato classes (18 classes)
TARGET_CLASSES = [
    # Apple (4)
    'Apple___Apple_scab',
    'Apple___Black_rot',
    'Apple___Cedar_apple_rust',
    'Apple___healthy',
    # Grape (4)
    'Grape___Black_rot',
    'Grape___Esca_(Black_Measles)',
    'Grape___Leaf_blight_(Isariopsis_Leaf_Spot)',
    'Grape___healthy',
    # Tomato (10)
    'Tomato___Bacterial_spot',
    'Tomato___Early_blight',
    'Tomato___Late_blight',
    'Tomato___Leaf_Mold',
    'Tomato___Septoria_leaf_spot',
    'Tomato___Spider_mites Two-spotted_spider_mite',
    'Tomato___Target_Spot',
    'Tomato___Tomato_Yellow_Leaf_Curl_Virus',
    'Tomato___Tomato_mosaic_virus',
    'Tomato___healthy',
]

NUM_CLASSES = len(TARGET_CLASSES)  # 18 classes

# Hyperparameters for transfer learning
BATCH_SIZE = 32
NUM_EPOCHS = 30  # Extended training for better convergence
LEARNING_RATE = 0.001  # Higher LR for classifier head only
WEIGHT_DECAY = 1e-3  # Stronger regularization
DROPOUT_RATE = 0.5
IMG_SIZE = 224
TRAIN_RATIO = 0.5  # 50% train, 50% validation


class TransferLearningModel(nn.Module):
    """EfficientNet-B0 with frozen backbone for transfer learning"""
    
    def __init__(self, num_classes=NUM_CLASSES, dropout_rate=DROPOUT_RATE):
        super().__init__()
        # Load pre-trained EfficientNet-B0
        weights = models.EfficientNet_B0_Weights.IMAGENET1K_V1
        self.backbone = models.efficientnet_b0(weights=weights)
        
        # FREEZE the backbone (feature extractor)
        for param in self.backbone.features.parameters():
            param.requires_grad = False
        
        # Replace classifier with new head (this will be trained)
        self.backbone.classifier = nn.Sequential(
            nn.Dropout(p=dropout_rate, inplace=True),
            nn.Linear(in_features=1280, out_features=512),
            nn.ReLU(inplace=True),
            nn.Dropout(p=dropout_rate * 0.5),
            nn.Linear(in_features=512, out_features=num_classes)
        )
    
    def forward(self, x):
        return self.backbone(x)
    
    def get_classifier_params(self):
        """Get only classifier parameters for training"""
        return list(self.backbone.classifier.parameters())
    
    def get_backbone_params(self):
        """Get backbone parameters (frozen)"""
        return list(self.backbone.features.parameters())


def filter_and_remap_dataset(dataset, target_classes):
    """
    Filter dataset to only include target classes and remap labels to 0-17
    
    Returns:
        indices: list of (original_index, new_label) tuples
    """
    class_to_idx = {cls: idx for idx, cls in enumerate(target_classes)}
    
    indexed_samples = []
    for idx, (path, old_label) in enumerate(dataset.samples):
        class_name = dataset.classes[old_label]
        if class_name in class_to_idx:
            new_label = class_to_idx[class_name]
            indexed_samples.append((idx, new_label))
    
    return indexed_samples


def split_indexed_samples(indexed_samples, train_ratio=0.5):
    """Split indexed samples into train and validation (50/50)"""
    random.shuffle(indexed_samples)
    split_point = int(len(indexed_samples) * train_ratio)
    return indexed_samples[:split_point], indexed_samples[split_point:]


class SubsetWithRemappedLabels(torch.utils.data.Dataset):
    """Dataset wrapper with remapped labels (0 to NUM_CLASSES-1)"""
    
    def __init__(self, dataset, indexed_samples, transform=None):
        self.dataset = dataset
        self.indexed_samples = indexed_samples
        self.transform = transform
    
    def __getitem__(self, idx):
        orig_idx, new_label = self.indexed_samples[idx]
        img_path, _ = self.dataset.samples[orig_idx]
        
        # Load image
        img = Image.open(img_path).convert('RGB')
        
        # Apply transform
        if self.transform is not None:
            img = self.transform(img)
        
        return img, new_label
    
    def __len__(self):
        return len(self.indexed_samples)


def create_model():
    """Create transfer learning model with frozen backbone"""
    model = TransferLearningModel(num_classes=NUM_CLASSES, dropout_rate=DROPOUT_RATE)
    model = model.to(DEVICE)
    
    # Count trainable parameters
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    frozen_params = total_params - trainable_params
    
    print(f"✓ Model: EfficientNet-B0 (Transfer Learning)")
    print(f"  Total parameters: {total_params:,}")
    print(f"  Trainable (classifier): {trainable_params:,}")
    print(f"  Frozen (backbone): {frozen_params:,}")
    print(f"  Training only: {100 * trainable_params / total_params:.1f}% of parameters")
    
    return model


def load_data():
    """Load only Apple, Grape, Tomato data with 50/50 split and label remapping"""

    # Transforms
    train_transform = transforms.Compose([
        transforms.RandomResizedCrop(IMG_SIZE, scale=(0.8, 1.0)),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomRotation(20),
        transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    val_transform = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(IMG_SIZE),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    # Load full dataset WITHOUT transforms (we'll apply them in our custom dataset)
    print(f"Loading dataset from: {DATASET_DIR}")
    full_dataset_no_transform = ImageFolder(DATASET_DIR, transform=None)

    # Filter to only Apple, Grape, Tomato AND remap labels to 0-17
    print(f"Filtering to {NUM_CLASSES} classes (Apple, Grape, Tomato only)...")
    indexed_samples = filter_and_remap_dataset(full_dataset_no_transform, TARGET_CLASSES)

    print(f"  Found {len(indexed_samples):,} images for target classes")

    # 50/50 split
    train_samples, val_samples = split_indexed_samples(indexed_samples, train_ratio=TRAIN_RATIO)

    print(f"  Training samples: {len(train_samples):,} ({TRAIN_RATIO*100:.0f}%)")
    print(f"  Validation samples: {len(val_samples):,} ({(1-TRAIN_RATIO)*100:.0f}%)")

    # Create subsets with remapped labels and transforms
    train_dataset = SubsetWithRemappedLabels(full_dataset_no_transform, train_samples, transform=train_transform)
    val_dataset = SubsetWithRemappedLabels(full_dataset_no_transform, val_samples, transform=val_transform)

    # Create loaders - use 0 workers on Windows to avoid multiprocessing issues
    import sys
    num_workers = 0 if sys.platform == 'win32' else 4
    
    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True,
                              num_workers=num_workers, pin_memory=True)
    val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False,
                            num_workers=num_workers, pin_memory=True)

    # Print class distribution
    print(f"\n  Class distribution:")
    class_counts = {}
    for _, new_label in train_samples:
        class_name = TARGET_CLASSES[new_label]
        class_counts[class_name] = class_counts.get(class_name, 0) + 1

    for class_name in sorted(class_counts.keys()):
        print(f"    {class_name}: {class_counts[class_name]:,}")

    return train_loader, val_loader, full_dataset_no_transform


def train_epoch(model, loader, criterion, optimizer, device):
    """Train for one epoch"""
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0
    
    for images, labels in loader:
        images, labels = images.to(device), labels.to(device)
        
        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        
        running_loss += loss.item()
        _, predicted = outputs.max(1)
        total += labels.size(0)
        correct += predicted.eq(labels).sum().item()
    
    epoch_loss = running_loss / len(loader)
    epoch_acc = 100. * correct / total
    
    return epoch_loss, epoch_acc


def validate(model, loader, criterion, device):
    """Validate"""
    model.eval()
    running_loss = 0.0
    correct = 0
    total = 0
    
    with torch.no_grad():
        for images, labels in loader:
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            loss = criterion(outputs, labels)
            
            running_loss += loss.item()
            _, predicted = outputs.max(1)
            total += labels.size(0)
            correct += predicted.eq(labels).sum().item()
    
    epoch_loss = running_loss / len(loader)
    epoch_acc = 100. * correct / total
    
    return epoch_loss, epoch_acc


def evaluate_model_comprehensive(model, loader, device, class_names):
    """Calculate comprehensive performance metrics"""
    model.eval()
    
    all_preds = []
    all_labels = []
    all_probs = []
    
    with torch.no_grad():
        for images, labels in loader:
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            probs = torch.softmax(outputs, dim=1)
            _, predicted = outputs.max(1)
            
            all_preds.extend(predicted.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())
            all_probs.extend(probs.cpu().numpy())
    
    all_preds = np.array(all_preds)
    all_labels = np.array(all_labels)
    all_probs = np.array(all_probs)
    
    # Overall accuracy
    accuracy = 100. * (all_preds == all_labels).sum() / len(all_labels)
    
    # Per-class metrics
    from sklearn.metrics import classification_report, confusion_matrix, f1_score, precision_score, recall_score
    
    # Classification report
    report = classification_report(all_labels, all_preds, target_names=class_names, output_dict=True)
    
    # Confusion matrix
    cm = confusion_matrix(all_labels, all_preds)
    
    # Per-class F1, Precision, Recall
    per_class_metrics = {}
    for i, class_name in enumerate(class_names):
        if str(i) in report:
            per_class_metrics[class_name] = {
                'precision': report[str(i)]['precision'],
                'recall': report[str(i)]['recall'],
                'f1-score': report[str(i)]['f1-score'],
                'support': report[str(i)]['support']
            }
    
    # Macro and weighted averages
    macro_f1 = f1_score(all_labels, all_preds, average='macro')
    weighted_f1 = f1_score(all_labels, all_preds, average='weighted')
    macro_precision = precision_score(all_labels, all_preds, average='macro')
    macro_recall = recall_score(all_labels, all_preds, average='macro')
    
    return {
        'overall_accuracy': accuracy,
        'macro_f1': macro_f1,
        'weighted_f1': weighted_f1,
        'macro_precision': macro_precision,
        'macro_recall': macro_recall,
        'per_class_metrics': per_class_metrics,
        'confusion_matrix': cm.tolist(),
        'class_names': class_names
    }


def print_performance_metrics(metrics):
    """Print comprehensive performance metrics"""
    print()
    print("=" * 70)
    print("  COMPREHENSIVE PERFORMANCE METRICS")
    print("=" * 70)
    print()
    
    print(f"Overall Accuracy: {metrics['overall_accuracy']:.2f}%")
    print(f"Macro F1-Score:   {metrics['macro_f1']:.4f}")
    print(f"Weighted F1-Score: {metrics['weighted_f1']:.4f}")
    print(f"Macro Precision:  {metrics['macro_precision']:.4f}")
    print(f"Macro Recall:     {metrics['macro_recall']:.4f}")
    print()
    
    print("Per-Class Performance:")
    print("-" * 70)
    print(f"{'Class':<50} {'Precision':>10} {'Recall':>10} {'F1':>10}")
    print("-" * 70)
    
    # Sort by F1-score (worst to best)
    sorted_classes = sorted(
        metrics['per_class_metrics'].items(),
        key=lambda x: x[1]['f1-score']
    )
    
    for class_name, class_metrics in sorted_classes:
        precision = class_metrics['precision']
        recall = class_metrics['recall']
        f1 = class_metrics['f1-score']
        support = class_metrics['support']
        
        # Color coding based on F1
        if f1 < 0.7:
            marker = "⚠️"
        elif f1 < 0.9:
            marker = "✓"
        else:
            marker = "✓✓"
        
        print(f"{marker} {class_name:<47} {precision:>10.3f} {recall:>10.3f} {f1:>10.3f} (n={support})")
    
    print("-" * 70)
    print()
    
    # Identify problematic classes
    print("Performance Summary:")
    poor_classes = [
        (name, m['f1-score']) 
        for name, m in metrics['per_class_metrics'].items() 
        if m['f1-score'] < 0.85
    ]
    
    if poor_classes:
        print(f"⚠️  Classes with F1 < 0.85 (may need more data):")
        for name, f1 in sorted(poor_classes, key=lambda x: x[1]):
            print(f"   - {name}: F1={f1:.3f}")
    else:
        print("✓ All classes have F1 > 0.85 (excellent!)")
    
    print()


def train():
    """Main training loop for transfer learning"""
    print("=" * 70)
    print("  Transfer Learning: Apple, Grape, Tomato Disease Detection")
    print("  EfficientNet-B0 (Frozen Backbone)")
    print("=" * 70)
    print()
    
    # Load data
    train_loader, val_loader, full_dataset = load_data()
    print()
    
    # Create model
    model = create_model()
    print()
    
    # Loss and optimizer (only classifier parameters)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.get_classifier_params(), lr=LEARNING_RATE,
                           weight_decay=WEIGHT_DECAY)
    
    # Learning rate scheduler
    scheduler = ReduceLROnPlateau(optimizer, mode='max', factor=0.5, patience=2,
                                   min_lr=1e-6)
    
    # Training tracking
    best_val_acc = 0.0
    patience_counter = 0
    max_patience = 5  # Early stopping for transfer learning
    history = {'train_loss': [], 'train_acc': [], 'val_loss': [], 'val_acc': []}
    
    print(f"\nStarting training for {NUM_EPOCHS} epochs...")
    print(f"  Batch size: {BATCH_SIZE}")
    print(f"  Learning rate: {LEARNING_RATE}")
    print(f"  Weight decay: {WEIGHT_DECAY}")
    print(f"  Dropout: {DROPOUT_RATE}")
    print(f"  Early stopping patience: {max_patience}")
    print(f"  Classes: {NUM_CLASSES} (Apple, Grape, Tomato only)")
    print()
    
    for epoch in range(NUM_EPOCHS):
        start_time = datetime.now()
        
        # Train
        train_loss, train_acc = train_epoch(model, train_loader, criterion, optimizer, DEVICE)
        
        # Validate
        val_loss, val_acc = validate(model, val_loader, criterion, DEVICE)
        
        # Update scheduler
        scheduler.step(val_acc)
        
        # Track history
        history['train_loss'].append(train_loss)
        history['train_acc'].append(train_acc)
        history['val_loss'].append(val_loss)
        history['val_acc'].append(val_acc)
        
        # Print progress
        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"Epoch {epoch+1:3d}/{NUM_EPOCHS} | "
              f"Train Loss: {train_loss:.4f} | Train Acc: {train_acc:6.2f}% | "
              f"Val Loss: {val_loss:.4f} | Val Acc: {val_acc:6.2f}% | "
              f"Time: {elapsed:.1f}s")
        
        # Save best model
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            save_path = MODEL_DIR / 'best_model.pth'
            torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'val_acc': val_acc,
                'train_acc': train_acc,
                'class_names': TARGET_CLASSES,
                'model_arch': 'EfficientNet-B0-Transfer',
                'backbone_frozen': True,
                'config': {
                    'dropout': DROPOUT_RATE,
                    'weight_decay': WEIGHT_DECAY,
                    'learning_rate': LEARNING_RATE,
                    'train_samples': len(train_loader.dataset),
                    'val_samples': len(val_loader.dataset),
                }
            }, save_path)
            print(f"  ✓ Saved best model (Val Acc: {val_acc:.2f}%)")
        
        # Early stopping
        if val_acc < best_val_acc - 0.5:  # Allow 0.5% tolerance
            patience_counter += 1
            if patience_counter >= max_patience:
                print(f"\n⚠ Early stopping triggered at epoch {epoch+1}")
                print(f"Best validation accuracy: {best_val_acc:.2f}%")
                break
        else:
            patience_counter = 0
    
    print()
    print("=" * 70)
    print(f"Transfer Learning Complete!")
    print(f"Best validation accuracy: {best_val_acc:.2f}%")
    print(f"Model saved to: {MODEL_DIR / 'best_model.pth'}")
    print("=" * 70)
    
    # Save training history
    history_path = MODEL_DIR / 'transfer_learning_history.json'
    with open(history_path, 'w') as f:
        json.dump(history, f, indent=2)
    print(f"Training history saved to: {history_path}")
    
    # Print overfitting analysis
    final_train_acc = history['train_acc'][-1]
    final_val_acc = history['val_acc'][-1]
    gap = final_train_acc - final_val_acc
    
    print()
    print(f"Overfitting Analysis:")
    print(f"  Final Train Accuracy: {final_train_acc:.2f}%")
    print(f"  Final Val Accuracy:   {final_val_acc:.2f}%")
    print(f"  Gap: {gap:.2f}%")
    
    if gap < 3:
        print(f"  ✓ Excellent! Model is well-regularized (gap < 3%)")
    elif gap < 7:
        print(f"  ✓ Good! Moderate gap (3-7%)")
    else:
        print(f"  ⚠ Some overfitting detected (gap > 7%)")
    
    # Save class mapping for inference
    class_mapping_path = MODEL_DIR / 'class_mapping.json'
    with open(class_mapping_path, 'w') as f:
        json.dump({
            'classes': TARGET_CLASSES,
            'class_to_idx': {cls: idx for idx, cls in enumerate(TARGET_CLASSES)}
        }, f, indent=2)
    print(f"Class mapping saved to: {class_mapping_path}")

    # ========================================
    # COMPREHENSIVE PERFORMANCE EVALUATION
    # ========================================
    print()
    print("Running comprehensive performance evaluation on validation set...")
    print()
    
    # Reload model in eval mode
    model.eval()
    
    # Calculate comprehensive metrics
    metrics = evaluate_model_comprehensive(model, val_loader, DEVICE, TARGET_CLASSES)
    
    # Print detailed metrics
    print_performance_metrics(metrics)
    
    # Save comprehensive metrics
    metrics_path = MODEL_DIR / 'performance_metrics.json'
    with open(metrics_path, 'w') as f:
        # Convert numpy types to Python types for JSON
        metrics_json = {
            'overall_accuracy': float(metrics['overall_accuracy']),
            'macro_f1': float(metrics['macro_f1']),
            'weighted_f1': float(metrics['weighted_f1']),
            'macro_precision': float(metrics['macro_precision']),
            'macro_recall': float(metrics['macro_recall']),
            'per_class_metrics': metrics['per_class_metrics'],
            'confusion_matrix': metrics['confusion_matrix'],
            'class_names': metrics['class_names']
        }
        json.dump(metrics_json, f, indent=2)
    
    print(f"Performance metrics saved to: {metrics_path}")
    print()
    print("Next steps:")
    print("1. Use for predictions: python run.py")
    print("2. View detailed metrics: Check models/performance_metrics.json")
    print()


if __name__ == '__main__':
    train()
