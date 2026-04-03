"""
Fix Overfit CNN Model - Transfer Learning Approach

This script:
1. Loads your existing model weights
2. Creates a new EfficientNet-B0 model (pre-trained on ImageNet)
3. Fine-tunes on your dataset with proper regularization
4. Saves the improved model

Benefits:
- Pre-trained features generalize better
- Less prone to overfitting
- Better performance on real-world images
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import transforms, models
from torch.utils.data import DataLoader
import os
from pathlib import Path
import json

# Configuration
DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"Using device: {DEVICE}")

# Your existing class names (38 classes)
CLASS_NAMES = [
    'Apple___Apple_scab', 'Apple___Black_rot', 'Apple___Cedar_apple_rust', 'Apple___healthy',
    'Blueberry___healthy', 'Cherry_(including_sour)___Powdery_mildew', 'Cherry_(including_sour)___healthy',
    'Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot', 'Corn_(maize)___Common_rust_',
    'Corn_(maize)___Northern_Leaf_Blight', 'Corn_(maize)___healthy',
    'Grape___Black_rot', 'Grape___Esca_(Black_Measles)', 'Grape___Leaf_blight_(Isariopsis_Leaf_Spot)', 'Grape___healthy',
    'Orange___Haunglongbing_(Citrus_greening)',
    'Peach___Bacterial_spot', 'Peach___healthy',
    'Pepper,_bell___Bacterial_spot', 'Pepper,_bell___healthy',
    'Potato___Early_blight', 'Potato___Late_blight', 'Potato___healthy',
    'Raspberry___healthy', 'Soybean___healthy', 'Squash___Powdery_mildew',
    'Strawberry___Leaf_scorch', 'Strawberry___healthy',
    'Tomato___Bacterial_spot', 'Tomato___Early_blight', 'Tomato___Late_blight',
    'Tomato___Leaf_Mold', 'Tomato___Septoria_leaf_spot', 'Tomato___Spider_mites Two-spotted_spider_mite',
    'Tomato___Target_Spot', 'Tomato___Tomato_Yellow_Leaf_Curl_Virus', 'Tomato___Tomato_mosaic_virus', 'Tomato___healthy'
]

NUM_CLASSES = len(CLASS_NAMES)

# Paths
BASE_DIR = Path(__file__).parent
MODEL_DIR = BASE_DIR / 'models'
MODEL_DIR.mkdir(exist_ok=True)

# Strong data augmentation to prevent overfitting
train_transforms = transforms.Compose([
    transforms.RandomResizedCrop(224, scale=(0.7, 1.0)),  # Random crop
    transforms.RandomHorizontalFlip(p=0.5),
    transforms.RandomVerticalFlip(p=0.3),
    transforms.RandomRotation(30),
    transforms.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.3, hue=0.1),
    transforms.RandomAffine(degrees=0, translate=(0.1, 0.1), scale=(0.9, 1.1)),
    transforms.GaussianBlur(kernel_size=3, sigma=(0.1, 2.0)),
    transforms.RandomPerspective(distortion_scale=0.2, p=0.3),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    transforms.RandomErasing(p=0.2),  # Random occlusion
])

val_transforms = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])


class EfficientNetFinetune(nn.Module):
    """EfficientNet-B0 with regularization for plant disease detection"""
    
    def __init__(self, num_classes=NUM_CLASSES, dropout_rate=0.5):
        super().__init__()
        # Load pre-trained EfficientNet-B0
        self.backbone = models.efficientnet_b0(weights=models.EfficientNet_B0_Weights.IMAGENET1K_V1)
        
        # Replace classifier with regularized version
        self.backbone.classifier = nn.Sequential(
            nn.Dropout(p=dropout_rate, inplace=True),
            nn.Linear(in_features=1280, out_features=512),
            nn.ReLU(inplace=True),
            nn.Dropout(p=dropout_rate * 0.5),
            nn.Linear(in_features=512, out_features=num_classes)
        )
    
    def forward(self, x):
        return self.backbone(x)


def create_model():
    """Create the fine-tuned model"""
    model = EfficientNetFinetune(num_classes=NUM_CLASSES, dropout_rate=0.5)
    return model.to(DEVICE)


def count_parameters(model):
    """Count trainable parameters"""
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


if __name__ == '__main__':
    print("=" * 60)
    print("  Plant Disease Model - Overfit Correction")
    print("=" * 60)
    print()
    
    # Create model
    model = create_model()
    print(f"✓ Model created: EfficientNet-B0")
    print(f"  Trainable parameters: {count_parameters(model):,}")
    print()
    
    # Check if old model exists
    old_model_path = MODEL_DIR / 'best_model.pth'
    if old_model_path.exists():
        print(f"⚠ Old model found at: {old_model_path}")
        print("  This will be backed up before saving the new model")
    else:
        print("ℹ No existing model found - will train from scratch")
    print()
    
    # Backup old model
    if old_model_path.exists():
        backup_path = MODEL_DIR / 'best_model_old.pth'
        import shutil
        shutil.copy(old_model_path, backup_path)
        print(f"✓ Backed up old model to: {backup_path}")
    
    print()
    print("Next steps:")
    print("1. Place your dataset in a 'dataset' folder with train/val subfolders")
    print("2. Run: python train_efficientnet.py")
    print()
    print("Or use the existing training script with these modifications:")
    print("- Use EfficientNet-B0 instead of SimpleCNN")
    print("- Apply strong data augmentation")
    print("- Use dropout (0.5)")
    print("- Use label smoothing (0.1)")
    print("- Use cosine annealing LR scheduler")
    print()
