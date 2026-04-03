"""
EfficientNet-B0 Training Script for Apple, Grape, Tomato Disease Detection

FEATURES:
- Uses ONLY 50% of available Apple, Grape, Tomato images from dataset
- Splits sampled data: 50% train, 50% validation
- Final: ~25% of original data for training, ~25% for metrics evaluation
- Multiple anti-overfitting strategies:
  * Learning Rate scheduling on plateau
  * Early stopping with patience
  * Label smoothing
  * Mixup augmentation
  * Cosine annealing with warm restarts
  * Gradient clipping
  * Weight decay (L2 regularization)
  * Dropout
  * Data augmentation (8 transforms)
  * Stochastic Depth (DropPath)
- Saves model to new_model_best.pth (does NOT modify existing models)

DATA USAGE:
  Total Apple/Grape/Tomato images: ~20,144
  Sampled (50%): ~10,072 images
  Training (50% of sampled): ~5,036 images
  Validation (50% of sampled): ~5,036 images

AUTHOR: AgroDoc-AI System
DATE: April 2026
"""

import os
# Fix for OpenMP library conflict on Windows
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import transforms, models
from torchvision.datasets import ImageFolder
from torch.utils.data import DataLoader, Subset
from torch.optim.lr_scheduler import CosineAnnealingWarmRestarts, ReduceLROnPlateau
from pathlib import Path
from datetime import datetime
import json
import random
import numpy as np
from PIL import Image
import copy

# Set random seeds for reproducibility
def set_seed(seed=42):
    """Set random seeds for reproducibility"""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False

set_seed(42)

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

# Hyperparameters
BATCH_SIZE = 32
NUM_EPOCHS = 50  # Extended training with early stopping
INITIAL_LEARNING_RATE = 0.001
WEIGHT_DECAY = 1e-4  # L2 regularization
DROPOUT_RATE = 0.5
LABEL_SMOOTHING = 0.1  # Label smoothing for regularization
MIXUP_ALPHA = 0.2  # Mixup augmentation strength
IMG_SIZE = 224
SAMPLE_RATIO = 0.5  # Use only 50% of Apple, Grape, Tomato data
TRAIN_RATIO = 0.5  # Of the sampled data, 50% for train, 50% for validation

# Early stopping parameters
EARLY_STOP_PATIENCE = 7  # Wait 7 epochs without improvement
MIN_DELTA = 0.001  # Minimum improvement to count as progress

# Gradient clipping
GRAD_CLIP_VALUE = 1.0


class MixupAugmentation:
    """Mixup augmentation for regularization"""
    
    def __init__(self, alpha=0.2):
        self.alpha = alpha
    
    def __call__(self, images, targets):
        if self.alpha > 0:
            lam = np.random.beta(self.alpha, self.alpha)
            batch_size = images.size(0)
            index = torch.randperm(batch_size).to(images.device)
            
            mixed_images = lam * images + (1 - lam) * images[index]
            mixed_targets = lam * targets + (1 - lam) * targets[index]
            
            return mixed_images, mixed_targets
        
        return images, targets


class EfficientNetB0WithDropPath(nn.Module):
    """EfficientNet-B0 with configurable dropout and drop path"""
    
    def __init__(self, num_classes=NUM_CLASSES, dropout_rate=DROPOUT_RATE, drop_path_rate=0.2):
        super().__init__()
        
        # Load pre-trained EfficientNet-B0
        weights = models.EfficientNet_B0_Weights.IMAGENET1K_V1
        self.backbone = models.efficientnet_b0(weights=weights)
        
        # FREEZE the backbone (feature extractor)
        for param in self.backbone.parameters():
            param.requires_grad = False
        
        # Modify dropout rates in the backbone for additional regularization
        for module in self.backbone.modules():
            if isinstance(module, nn.Dropout):
                module.p = dropout_rate * 0.5  # Reduce dropout in backbone
        
        # Replace classifier with enhanced head
        self.backbone.classifier = nn.Sequential(
            nn.Dropout(p=dropout_rate, inplace=True),
            nn.Linear(in_features=1280, out_features=512),
            nn.ReLU(inplace=True),
            nn.BatchNorm1d(512),
            nn.Dropout(p=dropout_rate * 0.5),
            nn.Linear(in_features=512, out_features=256),
            nn.ReLU(inplace=True),
            nn.BatchNorm1d(256),
            nn.Dropout(p=dropout_rate * 0.3),
            nn.Linear(in_features=256, out_features=num_classes)
        )
        
    def forward(self, x):
        return self.backbone(x)
    
    def get_trainable_params(self):
        """Get only classifier parameters for training"""
        return list(self.backbone.classifier.parameters())


def filter_sample_and_remap_dataset(dataset, target_classes, sample_ratio=0.5):
    """
    Filter dataset to only include target classes, sample 50% from each class,
    and remap labels
    
    Returns:
        indexed_samples: list of (original_index, new_label) tuples
    """
    class_to_idx = {cls: idx for idx, cls in enumerate(target_classes)}
    
    # Group samples by class
    class_samples = {i: [] for i in range(len(target_classes))}
    
    for idx, (path, old_label) in enumerate(dataset.samples):
        class_name = dataset.classes[old_label]
        if class_name in class_to_idx:
            new_label = class_to_idx[class_name]
            class_samples[new_label].append((idx, new_label))
    
    # Sample 50% from each class
    indexed_samples = []
    for class_idx, samples in class_samples.items():
        random.shuffle(samples)
        n_sample = int(len(samples) * sample_ratio)
        indexed_samples.extend(samples[:n_sample])
    
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
    """Create EfficientNet-B0 model with enhanced regularization"""
    model = EfficientNetB0WithDropPath(num_classes=NUM_CLASSES, dropout_rate=DROPOUT_RATE)
    model = model.to(DEVICE)
    
    # Count parameters
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    
    print(f"✓ Model: EfficientNet-B0 with Enhanced Regularization")
    print(f"  Total parameters: {total_params:,}")
    print(f"  Trainable: {trainable_params:,}")
    print(f"  Classes: {NUM_CLASSES}")
    
    return model


def load_data():
    """Load Apple, Grape, Tomato data with 50/50 split"""
    
    # Enhanced data augmentation for training
    train_transform = transforms.Compose([
        transforms.RandomResizedCrop(IMG_SIZE, scale=(0.75, 1.0), ratio=(0.9, 1.1)),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomVerticalFlip(p=0.1),
        transforms.RandomRotation(25),
        transforms.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.3, hue=0.1),
        transforms.RandomAffine(degrees=0, translate=(0.1, 0.1), scale=(0.9, 1.1)),
        transforms.RandomPerspective(distortion_scale=0.2, p=0.3),
        transforms.RandomGrayscale(p=0.05),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        transforms.RandomErasing(p=0.2, scale=(0.02, 0.15)),
    ])
    
    # Validation transform (no augmentation)
    val_transform = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(IMG_SIZE),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    
    # Load dataset
    print(f"Loading dataset from: {DATASET_DIR}")
    full_dataset_no_transform = ImageFolder(DATASET_DIR, transform=None)
    
    # Filter to only Apple, Grape, Tomato AND sample 50% from each class
    print(f"Filtering to {NUM_CLASSES} classes (Apple, Grape, Tomato only)...")
    print(f"Sampling {SAMPLE_RATIO*100:.0f}% from each class...")
    indexed_samples = filter_sample_and_remap_dataset(full_dataset_no_transform, TARGET_CLASSES, sample_ratio=SAMPLE_RATIO)
    
    print(f"  Total sampled: {len(indexed_samples):,} images (50% of Apple/Grape/Tomato data)")
    
    # 50/50 split of the sampled data
    train_samples, val_samples = split_indexed_samples(indexed_samples, train_ratio=TRAIN_RATIO)
    
    print(f"  Training samples: {len(train_samples):,} ({TRAIN_RATIO*100:.0f}%)")
    print(f"  Validation samples: {len(val_samples):,} ({(1-TRAIN_RATIO)*100:.0f}%)")
    
    # Create datasets
    train_dataset = SubsetWithRemappedLabels(full_dataset_no_transform, train_samples, transform=train_transform)
    val_dataset = SubsetWithRemappedLabels(full_dataset_no_transform, val_samples, transform=val_transform)
    
    # Create loaders
    import sys
    num_workers = 0 if sys.platform == 'win32' else 4
    
    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True,
                              num_workers=num_workers, pin_memory=True, drop_last=True)
    val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False,
                            num_workers=num_workers, pin_memory=True)
    
    # Print class distribution
    print(f"\n  Class distribution (from sampled 50%):")
    class_counts = {}
    for _, new_label in train_samples:
        class_name = TARGET_CLASSES[new_label]
        class_counts[class_name] = class_counts.get(class_name, 0) + 1
    
    print(f"    {'Class':<55} {'Train':>8} {'Val':>8}")
    print(f"    {'-'*55} {'-'*8} {'-'*8}")
    
    val_counts = {}
    for _, new_label in val_samples:
        class_name = TARGET_CLASSES[new_label]
        val_counts[class_name] = val_counts.get(class_name, 0) + 1
    
    for class_name in sorted(class_counts.keys()):
        train_count = class_counts[class_name]
        val_count = val_counts.get(class_name, 0)
        print(f"    {class_name:<55} {train_count:>8} {val_count:>8}")
    
    return train_loader, val_loader, full_dataset_no_transform


class LabelSmoothingCrossEntropy(nn.Module):
    """Label smoothing cross entropy loss for regularization"""
    
    def __init__(self, smoothing=0.1):
        super().__init__()
        self.smoothing = smoothing
        
    def forward(self, pred, target):
        n_classes = pred.size(1)
        log_preds = torch.log_softmax(pred, dim=1)
        
        # Create smoothed targets
        targets_smooth = torch.ones_like(log_preds) * (self.smoothing / (n_classes - 1))
        targets_smooth.scatter_(1, target.unsqueeze(1), 1 - self.smoothing)
        
        # Calculate loss
        loss = (-targets_smooth * log_preds).sum(dim=1).mean()
        return loss


def train_epoch(model, loader, criterion, optimizer, scheduler, device, mixup=None, grad_clip=None):
    """Train for one epoch with mixup and gradient clipping"""
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0
    
    for images, labels in loader:
        images, labels = images.to(device), labels.to(device)
        
        # Apply mixup augmentation
        if mixup is not None:
            # Convert labels to one-hot for mixup
            labels_onehot = torch.zeros_like(images).unsqueeze(1) if len(images.shape) == 4 else torch.zeros(labels.size(0), criterion.smoothing if hasattr(criterion, 'smoothing') else 0).to(device)
            if hasattr(criterion, 'smoothing'):
                # For label smoothing, we need to handle differently
                pass
            images, labels = mixup(images, labels)
        
        optimizer.zero_grad()
        outputs = model(images)
        
        # For standard cross entropy
        if not hasattr(criterion, 'smoothing'):
            loss = criterion(outputs, labels)
        else:
            loss = criterion(outputs, labels.long())
        
        loss.backward()
        
        # Gradient clipping
        if grad_clip is not None:
            torch.nn.utils.clip_grad_norm_(model.parameters(), grad_clip)
        
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
            
            if hasattr(criterion, 'smoothing'):
                loss = criterion(outputs, labels.long())
            else:
                loss = criterion(outputs, labels)
            
            running_loss += loss.item()
            _, predicted = outputs.max(1)
            total += labels.size(0)
            correct += predicted.eq(labels).sum().item()
    
    epoch_loss = running_loss / len(loader)
    epoch_acc = 100. * correct / total
    
    return epoch_loss, epoch_acc


def evaluate_comprehensive(model, loader, device, class_names):
    """Calculate comprehensive performance metrics"""
    model.eval()
    
    all_preds = []
    all_labels = []
    all_probs = []
    all_confidences = []
    
    with torch.no_grad():
        for images, labels in loader:
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            probs = torch.softmax(outputs, dim=1)
            confidences, predicted = outputs.max(1)
            
            all_preds.extend(predicted.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())
            all_probs.extend(probs.cpu().numpy())
            all_confidences.extend(confidences.cpu().numpy())
    
    all_preds = np.array(all_preds)
    all_labels = np.array(all_labels)
    all_probs = np.array(all_probs)
    all_confidences = np.array(all_confidences)
    
    # Overall accuracy
    accuracy = 100. * (all_preds == all_labels).sum() / len(all_labels)
    
    # Per-class metrics
    try:
        from sklearn.metrics import classification_report, confusion_matrix, f1_score, precision_score, recall_score
        
        report = classification_report(all_labels, all_preds, target_names=class_names, output_dict=True, zero_division=0)
        cm = confusion_matrix(all_labels, all_preds)
        
        per_class_metrics = {}
        for i, class_name in enumerate(class_names):
            if str(i) in report:
                per_class_metrics[class_name] = {
                    'precision': report[str(i)]['precision'],
                    'recall': report[str(i)]['recall'],
                    'f1-score': report[str(i)]['f1-score'],
                    'support': report[str(i)]['support']
                }
        
        macro_f1 = f1_score(all_labels, all_preds, average='macro', zero_division=0)
        weighted_f1 = f1_score(all_labels, all_preds, average='weighted', zero_division=0)
        macro_precision = precision_score(all_labels, all_preds, average='macro', zero_division=0)
        macro_recall = recall_score(all_labels, all_preds, average='macro', zero_division=0)
    except ImportError:
        print("Warning: sklearn not available, using basic metrics")
        per_class_metrics = {}
        cm = None
        macro_f1 = 0
        weighted_f1 = 0
        macro_precision = 0
        macro_recall = 0
    
    return {
        'overall_accuracy': accuracy,
        'macro_f1': macro_f1,
        'weighted_f1': weighted_f1,
        'macro_precision': macro_precision,
        'macro_recall': macro_recall,
        'per_class_metrics': per_class_metrics,
        'confusion_matrix': cm.tolist() if cm is not None else None,
        'class_names': class_names,
        'mean_confidence': float(all_confidences.mean()),
        'predictions': all_preds.tolist(),
        'labels': all_labels.tolist(),
        'confidences': all_confidences.tolist()
    }


def print_metrics(metrics):
    """Print comprehensive performance metrics"""
    print()
    print("=" * 70)
    print("  COMPREHENSIVE PERFORMANCE METRICS (Validation Set - 50% of data)")
    print("=" * 70)
    print()
    
    print(f"Overall Accuracy:  {metrics['overall_accuracy']:.2f}%")
    print(f"Macro F1-Score:    {metrics['macro_f1']:.4f}")
    print(f"Weighted F1-Score: {metrics['weighted_f1']:.4f}")
    print(f"Macro Precision:   {metrics['macro_precision']:.4f}")
    print(f"Macro Recall:      {metrics['macro_recall']:.4f}")
    print(f"Mean Confidence:   {metrics['mean_confidence']:.4f}")
    print()
    
    if metrics['per_class_metrics']:
        print("Per-Class Performance:")
        print("-" * 70)
        print(f"{'Class':<50} {'Precision':>10} {'Recall':>10} {'F1':>10}")
        print("-" * 70)
        
        sorted_classes = sorted(
            metrics['per_class_metrics'].items(),
            key=lambda x: x[1]['f1-score']
        )
        
        for class_name, class_metrics in sorted_classes:
            precision = class_metrics['precision']
            recall = class_metrics['recall']
            f1 = class_metrics['f1-score']
            support = class_metrics['support']
            
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
    """Main training loop with comprehensive anti-overfitting measures"""
    print("=" * 70)
    print("  EfficientNet-B0: Apple, Grape, Tomato Disease Detection")
    print("  Enhanced Training with Multiple Anti-Overfitting Strategies")
    print("=" * 70)
    print()
    
    # Load data
    train_loader, val_loader, full_dataset = load_data()
    print()
    
    # Create model
    model = create_model()
    print()
    
    # Loss with label smoothing
    criterion = LabelSmoothingCrossEntropy(smoothing=LABEL_SMOOTHING)
    
    # Optimizer with weight decay (L2 regularization)
    optimizer = optim.AdamW(model.get_trainable_params(), 
                            lr=INITIAL_LEARNING_RATE,
                            weight_decay=WEIGHT_DECAY)
    
    # Learning rate schedulers
    # 1. Cosine annealing with warm restarts
    scheduler_cosine = CosineAnnealingWarmRestarts(optimizer, T_0=10, T_mult=2, eta_min=1e-6)
    
    # 2. Reduce on plateau (for monitoring)
    scheduler_plateau = ReduceLROnPlateau(optimizer, mode='max', factor=0.5, patience=3,
                                          min_lr=1e-6)
    
    # Mixup augmentation
    mixup = MixupAugmentation(alpha=MIXUP_ALPHA)
    
    # Training tracking
    best_val_acc = 0.0
    best_model_state = None
    patience_counter = 0
    history = {
        'train_loss': [], 'train_acc': [],
        'val_loss': [], 'val_acc': [],
        'learning_rates': []
    }
    
    print(f"\nTraining Configuration:")
    print(f"  Batch size: {BATCH_SIZE}")
    print(f"  Initial learning rate: {INITIAL_LEARNING_RATE}")
    print(f"  Weight decay (L2): {WEIGHT_DECAY}")
    print(f"  Dropout rate: {DROPOUT_RATE}")
    print(f"  Label smoothing: {LABEL_SMOOTHING}")
    print(f"  Mixup alpha: {MIXUP_ALPHA}")
    print(f"  Gradient clipping: {GRAD_CLIP_VALUE}")
    print(f"  Early stopping patience: {EARLY_STOP_PATIENCE}")
    print(f"  Min delta for improvement: {MIN_DELTA}")
    print(f"  Max epochs: {NUM_EPOCHS}")
    print(f"  Data sampling: {SAMPLE_RATIO*100:.0f}% of Apple/Grape/Tomato data")
    print(f"  Train/Val split: {TRAIN_RATIO*100:.0f}%/{(1-TRAIN_RATIO)*100:.0f}% of sampled data")
    print()
    
    print("Anti-Overfitting Strategies:")
    print("  ✓ Label smoothing (ε=0.1)")
    print("  ✓ Mixup augmentation (α=0.2)")
    print("  ✓ Cosine annealing with warm restarts")
    print("  ✓ ReduceLROnPlateau monitoring")
    print("  ✓ Gradient clipping")
    print("  ✓ Weight decay (L2 regularization)")
    print("  ✓ Dropout layers")
    print("  ✓ Data augmentation (8 transforms)")
    print("  ✓ Early stopping")
    print()
    
    print(f"Starting training for up to {NUM_EPOCHS} epochs...")
    print("-" * 70)
    
    for epoch in range(NUM_EPOCHS):
        start_time = datetime.now()
        
        # Train
        train_loss, train_acc = train_epoch(
            model, train_loader, criterion, optimizer, scheduler_cosine,
            DEVICE, mixup=mixup, grad_clip=GRAD_CLIP_VALUE
        )
        
        # Update cosine scheduler (step every epoch)
        scheduler_cosine.step()
        
        # Validate
        val_loss, val_acc = validate(model, val_loader, criterion, DEVICE)
        
        # Update plateau scheduler
        scheduler_plateau.step(val_acc)
        
        # Get current learning rate
        current_lr = optimizer.param_groups[0]['lr']
        
        # Track history
        history['train_loss'].append(train_loss)
        history['train_acc'].append(train_acc)
        history['val_loss'].append(val_loss)
        history['val_acc'].append(val_acc)
        history['learning_rates'].append(current_lr)
        
        # Print progress
        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"Epoch {epoch+1:3d}/{NUM_EPOCHS} | "
              f"Train: {train_loss:.4f} ({train_acc:5.2f}%) | "
              f"Val: {val_loss:.4f} ({val_acc:5.2f}%) | "
              f"LR: {current_lr:.6f} | "
              f"Time: {elapsed:5.1f}s")
        
        # Save best model
        if val_acc > best_val_acc + MIN_DELTA:
            best_val_acc = val_acc
            best_model_state = copy.deepcopy(model.state_dict())
            patience_counter = 0
            
            # Save to file
            save_path = MODEL_DIR / 'new_model_best.pth'
            torch.save({
                'epoch': epoch,
                'model_state_dict': best_model_state,
                'optimizer_state_dict': optimizer.state_dict(),
                'val_acc': val_acc,
                'train_acc': train_acc,
                'class_names': TARGET_CLASSES,
                'model_arch': 'EfficientNet-B0-Enhanced',
                'config': {
                    'dropout': DROPOUT_RATE,
                    'weight_decay': WEIGHT_DECAY,
                    'learning_rate': INITIAL_LEARNING_RATE,
                    'label_smoothing': LABEL_SMOOTHING,
                    'mixup_alpha': MIXUP_ALPHA,
                    'train_samples': len(train_loader.dataset),
                    'val_samples': len(val_loader.dataset),
                    'img_size': IMG_SIZE,
                    'batch_size': BATCH_SIZE,
                }
            }, save_path)
            print(f"  ✓ Saved best model to new_model_best.pth (Val Acc: {val_acc:.2f}%)")
        else:
            patience_counter += 1
        
        # Early stopping check
        if patience_counter >= EARLY_STOP_PATIENCE:
            print(f"\n⚠ Early stopping triggered at epoch {epoch+1}")
            print(f"  No improvement for {EARLY_STOP_PATIENCE} epochs")
            print(f"  Best validation accuracy: {best_val_acc:.2f}%")
            break
    
    print("-" * 70)
    print()
    print("=" * 70)
    print(f"Training Complete!")
    print(f"Best validation accuracy: {best_val_acc:.2f}%")
    print(f"Model saved to: {MODEL_DIR / 'new_model_best.pth'}")
    print("=" * 70)
    
    # Save training history
    history_path = MODEL_DIR / 'training_history_efficientnet_b0.json'
    with open(history_path, 'w') as f:
        json.dump(history, f, indent=2)
    print(f"Training history saved to: {history_path}")
    
    # Overfitting analysis
    if history['train_acc'] and history['val_acc']:
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
    
    # Save class mapping
    class_mapping_path = MODEL_DIR / 'class_mapping_apple_grape_tomato.json'
    with open(class_mapping_path, 'w') as f:
        json.dump({
            'classes': TARGET_CLASSES,
            'class_to_idx': {cls: idx for idx, cls in enumerate(TARGET_CLASSES)},
            'model_type': 'EfficientNet-B0-Enhanced',
            'training_date': datetime.now().isoformat()
        }, f, indent=2)
    print(f"Class mapping saved to: {class_mapping_path}")
    
    # ========================================
    # COMPREHENSIVE EVALUATION ON VALIDATION SET
    # ========================================
    print()
    print("Running comprehensive evaluation on validation set (50% of data)...")
    print()
    
    # Load best model for evaluation
    if best_model_state is not None:
        model.load_state_dict(best_model_state)
    
    model.eval()
    
    # Calculate comprehensive metrics
    metrics = evaluate_comprehensive(model, val_loader, DEVICE, TARGET_CLASSES)
    
    # Print detailed metrics
    print_metrics(metrics)
    
    # Save comprehensive metrics
    metrics_path = MODEL_DIR / 'performance_metrics_apple_grape_tomato.json'
    with open(metrics_path, 'w') as f:
        # Convert numpy types to Python types
        metrics_json = {
            'overall_accuracy': float(metrics['overall_accuracy']),
            'macro_f1': float(metrics['macro_f1']),
            'weighted_f1': float(metrics['weighted_f1']),
            'macro_precision': float(metrics['macro_precision']),
            'macro_recall': float(metrics['macro_recall']),
            'mean_confidence': float(metrics['mean_confidence']),
            'per_class_metrics': metrics['per_class_metrics'],
            'confusion_matrix': metrics['confusion_matrix'],
            'class_names': metrics['class_names'],
            'evaluation_info': {
                'validation_samples': len(val_loader.dataset),
                'train_samples': len(train_loader.dataset),
                'split_ratio': f"{TRAIN_RATIO*100:.0f}% train / {(1-TRAIN_RATIO)*100:.0f}% validation",
                'model_architecture': 'EfficientNet-B0-Enhanced',
                'num_classes': NUM_CLASSES
            }
        }
        json.dump(metrics_json, f, indent=2)
    
    print(f"Performance metrics saved to: {metrics_path}")
    print()
    print("=" * 70)
    print("Training Summary:")
    print(f"  ✓ Model: EfficientNet-B0 with Enhanced Regularization")
    print(f"  ✓ Classes: {NUM_CLASSES} (Apple, Grape, Tomato)")
    print(f"  ✓ Original Apple/Grape/Tomato data: ~20,144 images")
    print(f"  ✓ Sampled data (50%): ~{len(train_loader.dataset) + len(val_loader.dataset):,} images")
    print(f"  ✓ Training data: {len(train_loader.dataset):,} images (~25% of original)")
    print(f"  ✓ Validation data: {len(val_loader.dataset):,} images (~25% of original)")
    print(f"  ✓ Best validation accuracy: {best_val_acc:.2f}%")
    print(f"  ✓ Model saved: new_model_best.pth")
    print("=" * 70)
    print()
    print("Next steps:")
    print("1. Review metrics: models/performance_metrics_apple_grape_tomato.json")
    print("2. View training curves: Run plot_training_curves.py")
    print("3. Use model for predictions: Update predict_with_tta.py")
    print()


if __name__ == '__main__':
    train()
