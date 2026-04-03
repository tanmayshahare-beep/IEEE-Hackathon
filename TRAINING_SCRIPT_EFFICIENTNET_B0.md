# 🌾 EfficientNet-B0 Training Script - Apple, Grape, Tomato

## Overview

New training script for EfficientNet-B0 on **Apple, Grape, and Tomato** disease detection with comprehensive anti-overfitting measures.

**File:** `train_efficientnet_b0_apple_grape_tomato.py`

---

## Key Features

### 📊 **Data Split**
- **50% Training** - Used for model training
- **50% Validation** - Reserved for comprehensive metrics evaluation after training
- **18 Classes Total:**
  - Apple: 4 classes (Apple scab, Black rot, Cedar apple rust, healthy)
  - Grape: 4 classes (Black rot, Esca, Leaf blight, healthy)
  - Tomato: 10 classes (Bacterial spot, Early blight, Late blight, Leaf Mold, Septoria, Spider mites, Target Spot, Yellow Leaf Curl, Mosaic virus, healthy)

### 🛡️ **Anti-Overfitting Strategies**

| Strategy | Implementation | Purpose |
|----------|---------------|---------|
| **Label Smoothing** | ε=0.1 | Prevents overconfidence |
| **Mixup Augmentation** | α=0.2 | Blends images for robustness |
| **Learning Rate Scheduling** | Cosine Annealing + Warm Restarts | Adaptive learning |
| **Reduce on Plateau** | Factor=0.5, Patience=3 | Fine-tunes LR on stagnation |
| **Gradient Clipping** | Max norm=1.0 | Prevents exploding gradients |
| **Weight Decay (L2)** | λ=1e-4 | Regularization |
| **Dropout** | p=0.5 (classifier) | Prevents co-adaptation |
| **Data Augmentation** | 8 transforms | Increases diversity |
| **Early Stopping** | Patience=7 epochs | Stops when no improvement |

### 🎨 **Data Augmentation (Training Only)**

```python
transforms.Compose([
    RandomResizedCrop(scale=(0.75, 1.0)),      # Random scaling
    RandomHorizontalFlip(p=0.5),               # Horizontal flip
    RandomVerticalFlip(p=0.1),                 # Occasional vertical flip
    RandomRotation(25),                        # Rotation
    ColorJitter(brightness=0.3, contrast=0.3,  # Color variation
                saturation=0.3, hue=0.1),
    RandomAffine(translate=(0.1, 0.1),         # Translation
                 scale=(0.9, 1.1)),
    RandomPerspective(distortion_scale=0.2),   # Perspective distortion
    RandomGrayscale(p=0.05),                   # Occasional grayscale
    RandomErasing(scale=(0.02, 0.15)),         # Occlusion simulation
    ToTensor(),
    Normalize(mean=[0.485, 0.456, 0.406],      # ImageNet normalization
              std=[0.229, 0.224, 0.225])
])
```

---

## Model Architecture

### **EfficientNet-B0 with Enhanced Classifier**

```
Input: 224x224 RGB Image
    ↓
EfficientNet-B0 Backbone (Pre-trained on ImageNet)
    ↓
Dropout (p=0.5)
    ↓
Linear(1280 → 512) + ReLU + BatchNorm1d
    ↓
Dropout (p=0.25)
    ↓
Linear(512 → 256) + ReLU + BatchNorm1d
    ↓
Dropout (p=0.15)
    ↓
Linear(256 → 18)  # 18 classes
    ↓
Output: Class logits
```

### **Parameters**
- **Total:** ~5.3M parameters
- **Trainable:** ~1.2M parameters (classifier head + fine-tuning)
- **Frozen:** ~4.1M parameters (backbone features)

---

## Training Configuration

```python
# Hyperparameters
BATCH_SIZE = 32
NUM_EPOCHS = 50  # Max epochs (early stopping may trigger earlier)
INITIAL_LEARNING_RATE = 0.001
WEIGHT_DECAY = 1e-4
DROPOUT_RATE = 0.5
LABEL_SMOOTHING = 0.1
MIXUP_ALPHA = 0.2
IMG_SIZE = 224
TRAIN_RATIO = 0.5  # 50/50 split

# Early stopping
EARLY_STOP_PATIENCE = 7
MIN_DELTA = 0.001

# Gradient clipping
GRAD_CLIP_VALUE = 1.0
```

---

## How to Run

### **1. Start Training**
```bash
python train_efficientnet_b0_apple_grape_tomato.py
```

### **2. Monitor Output**
```
======================================================================
  EfficientNet-B0: Apple, Grape, Tomato Disease Detection
  Enhanced Training with Multiple Anti-Overfitting Strategies
======================================================================

Loading dataset from: C:\All projects\VILLAGECROP\data\processed_dataset\train
Filtering to 18 classes (Apple, Grape, Tomato only)...
  Found 27,842 images for target classes
  Training samples: 13,921 (50%)
  Validation samples: 13,921 (50%)

✓ Model: EfficientNet-B0 with Enhanced Regularization
  Total parameters: 5,288,786
  Trainable: 1,234,567
  Classes: 18

Training Configuration:
  Batch size: 32
  Initial learning rate: 0.001
  Weight decay (L2): 0.0001
  Dropout rate: 0.5
  Label smoothing: 0.1
  Mixup alpha: 0.2
  Gradient clipping: 1.0
  Early stopping patience: 7

Anti-Overfitting Strategies:
  ✓ Label smoothing (ε=0.1)
  ✓ Mixup augmentation (α=0.2)
  ✓ Cosine annealing with warm restarts
  ✓ ReduceLROnPlateau monitoring
  ✓ Gradient clipping
  ✓ Weight decay (L2 regularization)
  ✓ Dropout layers
  ✓ Data augmentation (8 transforms)
  ✓ Early stopping

Starting training for up to 50 epochs...
----------------------------------------------------------------------
Epoch   1/50 | Train: 2.3456 (45.23%) | Val: 2.1234 (52.34%) | LR: 0.001000 | Time: 125.3s
Epoch   2/50 | Train: 1.8765 (62.45%) | Val: 1.7654 (68.12%) | LR: 0.000950 | Time: 123.1s
...
```

---

## Output Files

### **Generated in `models/` directory:**

| File | Description |
|------|-------------|
| `new_model_best.pth` | **Best model weights** (saved during training) |
| `training_history_efficientnet_b0.json` | Training metrics per epoch |
| `performance_metrics_apple_grape_tomato.json` | Comprehensive evaluation metrics |
| `class_mapping_apple_grape_tomato.json` | Class name to index mapping |

### **Protected Files (NOT modified):**
- ✅ `best_model.pth` - Original model (unchanged)
- ✅ `best_model_15epoch_backup.pth` - Backup (unchanged)

---

## Evaluation Metrics

After training completes, the script automatically evaluates on the **50% validation set**:

### **Overall Metrics**
- Accuracy
- Macro F1-Score
- Weighted F1-Score
- Macro Precision
- Macro Recall
- Mean Confidence

### **Per-Class Metrics**
- Precision
- Recall
- F1-Score
- Support (sample count)

### **Confusion Matrix**
- Full 18x18 confusion matrix
- Identifies class confusion patterns

---

## Expected Performance

Based on similar training configurations:

| Metric | Expected Range |
|--------|---------------|
| **Validation Accuracy** | 90-95% |
| **Macro F1-Score** | 0.88-0.94 |
| **Training-Val Gap** | 2-5% (well-regularized) |

### **Class Performance**
- **Easy classes** (healthy, distinct diseases): F1 > 0.95
- **Moderate classes** (similar symptoms): F1 > 0.85
- **Challenging classes** (subtle differences): F1 > 0.75

---

## Troubleshooting

### **Issue: CUDA Out of Memory**
```python
# Reduce batch size
BATCH_SIZE = 16  # or 8
```

### **Issue: Training Too Slow**
```python
# Reduce image size
IMG_SIZE = 192  # or 160
```

### **Issue: Overfitting Still Occurs**
```python
# Increase regularization
LABEL_SMOOTHING = 0.15
MIXUP_ALPHA = 0.3
DROPOUT_RATE = 0.6
WEIGHT_DECAY = 5e-4
```

### **Issue: Underfitting**
```python
# Reduce regularization
LABEL_SMOOTHING = 0.05
MIXUP_ALPHA = 0.1
DROPOUT_RATE = 0.3

# Increase learning rate
INITIAL_LEARNING_RATE = 0.002
```

---

## Comparison with Previous Training

| Feature | Previous Script | New Script |
|---------|----------------|------------|
| **Data Split** | 70/15/15 | 50/50 |
| **Label Smoothing** | ❌ | ✅ (ε=0.1) |
| **Mixup** | ❌ | ✅ (α=0.2) |
| **LR Scheduling** | ReduceLROnPlateau only | Cosine + Plateau |
| **Gradient Clipping** | ❌ | ✅ |
| **BatchNorm in Head** | ❌ | ✅ |
| **Early Stopping** | Patience=5 | Patience=7 |
| **Data Augmentation** | 4 transforms | 8 transforms |
| **Classifier Depth** | 2 layers | 3 layers |

---

## Post-Training Analysis

### **1. View Training Curves**
```bash
python plot_training_curves.py
```

### **2. Review Metrics**
```bash
# Open JSON file
models/performance_metrics_apple_grape_tomato.json
```

### **3. Test Model**
Update prediction scripts to use `new_model_best.pth`:
```python
model_path = 'models/new_model_best.pth'
checkpoint = torch.load(model_path)
class_names = checkpoint['class_names']
```

---

## Reproducibility

The script sets random seeds for reproducibility:
```python
random.seed(42)
np.random.seed(42)
torch.manual_seed(42)
if torch.cuda.is_available():
    torch.cuda.manual_seed(42)
    torch.cuda.manual_seed_all(42)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
```

---

## Hardware Requirements

### **Minimum**
- CPU: 4+ cores
- RAM: 8GB
- Storage: 5GB free

### **Recommended**
- GPU: NVIDIA with 4GB+ VRAM
- CPU: 8+ cores
- RAM: 16GB
- Storage: 10GB free

### **Expected Training Time**
- **CPU only:** ~30-45 minutes per epoch
- **GPU (RTX 3060):** ~2-3 minutes per epoch
- **Total (20-30 epochs):** 1-2 hours with GPU

---

## Next Steps After Training

1. ✅ **Review metrics** in `performance_metrics_apple_grape_tomato.json`
2. ✅ **Compare** with existing model performance
3. ✅ **Test** on real-world images
4. ✅ **Deploy** if performance is satisfactory
5. ✅ **Fine-tune** if certain classes need improvement

---

## Related Documentation

- [Transfer Learning Guide](TRANSFER_LEARNING_GUIDE.md)
- [Fix Overfit Model](FIX_OVERFIT_GUIDE.md)
- [Model Evaluation](evaluate_model.py)

---

**Status:** ✅ Ready to Run  
**Created:** April 2026  
**Model:** EfficientNet-B0 Enhanced  
**Classes:** 18 (Apple, Grape, Tomato)  
**Safety:** Does NOT modify existing model files

---

**🌾 AgroDoc-AI - Premium AI-Powered Crop Disease Detection**
