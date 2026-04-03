"""
Image Processing Service

Handles:
1. Blur detection using Laplacian variance
2. Image preprocessing for CNN model
"""

import cv2
import numpy as np
from PIL import Image
import torch
import torch.nn as nn
import torchvision.transforms as transforms
from io import BytesIO
from pathlib import Path

from ..config import BLUR_THRESHOLD, IMAGE_SIZE, CLASS_NAMES, MODEL_PATH, CONFIDENCE_THRESHOLD

# Leaf Detection Configuration
GREEN_LOWER_HSV = (25, 30, 30)       # Lower bound for green in HSV (more lenient)
GREEN_UPPER_HSV = (75, 255, 255)     # Upper bound for green in HSV (more lenient)
MIN_GREEN_AREA_RATIO = 0.08          # At least 8% of image should be green (reduced)
MIN_LEAF_CIRCULARITY = 0.02          # Minimum circularity (very lenient - leaves vary)
MIN_LEAF_SOLIDITY = 0.5              # Minimum solidity for leaf shape


# -------------------- Leaf Detection --------------------
def detect_leaf(image_path: str) -> dict:
    """
    Detect if an image contains a leaf.
    
    Uses:
    1. Green color segmentation in HSV space
    2. Shape analysis (circularity, solidity)
    3. Area ratio check
    
    Returns:
        dict with 'is_leaf', 'confidence', and 'message'
    """
    try:
        # Read image
        image = cv2.imread(str(image_path))
        if image is None:
            return {
                'is_leaf': False,
                'confidence': 0.0,
                'message': 'Failed to read image file',
                'reason': 'read_error'
            }
        
        # Convert to HSV color space
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # Threshold for green color
        lower_green = np.array(GREEN_LOWER_HSV, dtype=np.uint8)
        upper_green = np.array(GREEN_UPPER_HSV, dtype=np.uint8)
        mask = cv2.inRange(hsv, lower_green, upper_green)
        
        # Calculate green area ratio
        total_pixels = image.shape[0] * image.shape[1]
        green_pixels = cv2.countNonZero(mask)
        green_ratio = green_pixels / total_pixels
        
        if green_ratio < MIN_GREEN_AREA_RATIO:
            return {
                'is_leaf': False,
                'confidence': green_ratio / MIN_GREEN_AREA_RATIO,
                'message': f'Insufficient green area ({green_ratio:.1%} < {MIN_GREEN_AREA_RATIO:.0%})',
                'reason': 'insufficient_green',
                'green_ratio': green_ratio
            }
        
        # Find contours in the mask
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return {
                'is_leaf': False,
                'confidence': 0.0,
                'message': 'No leaf-like contours detected',
                'reason': 'no_contours'
            }
        
        # Analyze the largest contour
        largest_contour = max(contours, key=cv2.contourArea)
        contour_area = cv2.contourArea(largest_contour)
        
        if contour_area < 1000:  # Minimum area threshold
            return {
                'is_leaf': False,
                'confidence': 0.0,
                'message': 'Leaf area too small',
                'reason': 'area_too_small'
            }
        
        # Calculate shape metrics
        perimeter = cv2.arcLength(largest_contour, True)
        if perimeter == 0:
            return {
                'is_leaf': False,
                'confidence': 0.0,
                'message': 'Invalid contour',
                'reason': 'invalid_contour'
            }
        
        # Circularity: 4π * area / perimeter² (1.0 = perfect circle)
        circularity = 4 * np.pi * contour_area / (perimeter * perimeter)
        
        # Convex hull and solidity
        hull = cv2.convexHull(largest_contour)
        hull_area = cv2.contourArea(hull)
        solidity = float(contour_area) / hull_area if hull_area > 0 else 0
        
        # Calculate leaf score
        circularity_score = min(circularity / 0.5, 1.0)  # Leaves are somewhat elongated
        solidity_score = min(solidity / 0.7, 1.0)
        area_score = min(green_ratio / 0.3, 1.0)
        
        leaf_confidence = (circularity_score * 0.3 + solidity_score * 0.3 + area_score * 0.4)
        
        # Check if it passes leaf detection
        if circularity < MIN_LEAF_CIRCULARITY or solidity < MIN_LEAF_SOLIDITY:
            return {
                'is_leaf': False,
                'confidence': leaf_confidence,
                'message': f'Shape does not match leaf (circularity={circularity:.2f}, solidity={solidity:.2f})',
                'reason': 'invalid_shape',
                'circularity': circularity,
                'solidity': solidity
            }
        
        # Passed all checks - it's a leaf!
        return {
            'is_leaf': True,
            'confidence': leaf_confidence,
            'message': f'Leaf detected (confidence: {leaf_confidence:.1%})',
            'green_ratio': green_ratio,
            'circularity': circularity,
            'solidity': solidity,
            'contour_area': contour_area
        }
        
    except Exception as e:
        return {
            'is_leaf': False,
            'confidence': 0.0,
            'message': f'Leaf detection error: {str(e)}',
            'reason': 'error'
        }


def detect_leaf_from_bytes(image_bytes: bytes) -> dict:
    """Detect leaf from image bytes."""
    try:
        image = Image.open(BytesIO(image_bytes))
        image_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Save temporarily for processing
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            cv2.imwrite(tmp.name, image_cv)
            tmp_path = tmp.name
        
        result = detect_leaf(tmp_path)
        os.unlink(tmp_path)
        return result
        
    except Exception as e:
        return {
            'is_leaf': False,
            'confidence': 0.0,
            'message': f'Leaf detection error: {str(e)}',
            'reason': 'error'
        }


# -------------------- Blur Detection --------------------
def detect_blur(image_path: str, threshold: float = None) -> dict:
    """
    Detect if an image is too blurry for analysis.
    
    Returns:
        dict with 'is_blurry', 'variance', and 'message'
    """
    if threshold is None:
        threshold = BLUR_THRESHOLD
    
    image = cv2.imread(str(image_path))
    
    if image is None:
        return {
            'is_blurry': True,
            'variance': 0.0,
            'message': 'Failed to read image file'
        }
    
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    variance = laplacian.var()
    is_blurry = bool(variance < threshold)

    return {
        'is_blurry': is_blurry,
        'variance': float(variance),
        'message': f'Image variance: {variance:.2f} (threshold: {threshold})'
    }


def detect_blur_from_bytes(image_bytes: bytes, threshold: float = None) -> dict:
    """Detect blur from image bytes."""
    if threshold is None:
        threshold = BLUR_THRESHOLD

    image = Image.open(BytesIO(image_bytes))
    image_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    variance = laplacian.var()
    is_blurry = bool(variance < threshold)

    return {
        'is_blurry': is_blurry,
        'variance': float(variance),
        'message': f'Image variance: {variance:.2f} (threshold: {threshold})'
    }


# -------------------- CNN Model --------------------
class SimpleCNN(nn.Module):
    """CNN architecture for plant disease classification"""

    def __init__(self, num_classes: int = 18):
        super(SimpleCNN, self).__init__()

        self.features = nn.Sequential(
            nn.Conv2d(3, 32, 3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.Conv2d(32, 32, 3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2, 2),
            nn.Dropout2d(0.25),

            nn.Conv2d(32, 64, 3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.Conv2d(64, 64, 3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2, 2),
            nn.Dropout2d(0.25),

            nn.Conv2d(64, 128, 3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.Conv2d(128, 128, 3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2, 2),
            nn.Dropout2d(0.25),

            nn.Conv2d(128, 256, 3, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
            nn.Conv2d(256, 256, 3, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2, 2),
            nn.Dropout2d(0.25),

            nn.Conv2d(256, 512, 3, padding=1),
            nn.BatchNorm2d(512),
            nn.ReLU(inplace=True),
            nn.Conv2d(512, 512, 3, padding=1),
            nn.BatchNorm2d(512),
            nn.ReLU(inplace=True),
            nn.AdaptiveAvgPool2d((1, 1)),
        )

        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Dropout(0.5),
            nn.Linear(512, 1024),
            nn.ReLU(inplace=True),
            nn.Dropout(0.5),
            nn.Linear(1024, num_classes)
        )

    def forward(self, x):
        x = self.features(x)
        x = self.classifier(x)
        return x


class EfficientNetTransfer(nn.Module):
    """EfficientNet-B0 with frozen backbone for transfer learning"""
    
    def __init__(self, num_classes: int = 18):
        super().__init__()
        from torchvision import models
        
        # Load EfficientNet-B0
        weights = models.EfficientNet_B0_Weights.IMAGENET1K_V1
        self.backbone = models.efficientnet_b0(weights=weights)
        
        # Replace classifier
        self.backbone.classifier = nn.Sequential(
            nn.Dropout(p=0.5, inplace=True),
            nn.Linear(in_features=1280, out_features=512),
            nn.ReLU(inplace=True),
            nn.Dropout(p=0.25),
            nn.Linear(in_features=512, out_features=num_classes)
        )
    
    def forward(self, x):
        return self.backbone(x)


# -------------------- Prediction Service --------------------
class PlantDiseasePredictor:
    """Complete prediction pipeline"""
    
    def __init__(self, model_path: str = None, device: str = None):
        if model_path is None:
            model_path = MODEL_PATH
        
        self.model_path = model_path
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = self._load_model()
        self.class_names = CLASS_NAMES
        
        # Preprocessing transforms
        self.transform = transforms.Compose([
            transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])
    
    def _load_model(self):
        """Load trained CNN model (auto-detects SimpleCNN or EfficientNet Transfer)"""
        if not Path(self.model_path).exists():
            raise FileNotFoundError(f"Model not found at: {self.model_path}")

        checkpoint = torch.load(self.model_path, map_location=self.device, weights_only=True)

        # Handle both checkpoint dict and raw state_dict formats
        if isinstance(checkpoint, dict):
            state_dict = checkpoint.get('model_state_dict', checkpoint)
            model_arch = checkpoint.get('model_arch', 'SimpleCNN')
            saved_classes = checkpoint.get('class_names', CLASS_NAMES)
        else:
            state_dict = checkpoint
            model_arch = 'SimpleCNN'
            saved_classes = CLASS_NAMES

        # Update class names if model was trained on subset
        self.class_names = saved_classes
        
        # Determine model architecture
        if 'EfficientNet' in model_arch or 'transfer' in model_arch.lower():
            print(f"Loading EfficientNet-B0 Transfer Learning model...")
            model = EfficientNetTransfer(num_classes=len(saved_classes))
        else:
            print(f"Loading SimpleCNN model...")
            model = SimpleCNN(num_classes=len(saved_classes))

        model.load_state_dict(state_dict)
        model.to(self.device)
        model.eval()
        return model
    
    def predict(self, image_path: str) -> dict:
        """Run full prediction pipeline with validation"""
        # Step 1: Leaf detection (NEW - first filter)
        leaf_result = detect_leaf(image_path)
        
        if not leaf_result['is_leaf']:
            return {
                'success': False,
                'error': f'No leaf detected. {leaf_result["message"]}. Please upload a clear image of a plant leaf.',
                'leaf_detection': leaf_result,
                'needs_retake': True,
                'retake_reason': 'not_a_leaf'
            }

        # Step 2: Blur detection
        blur_result = detect_blur(image_path)

        if blur_result['is_blurry']:
            return {
                'success': False,
                'error': 'Image too blurry for analysis',
                'leaf_detection': leaf_result,
                'blur_result': blur_result,
                'needs_retake': True,
                'retake_reason': 'blurry'
            }

        # Step 3: Preprocess and predict
        try:
            image = Image.open(image_path).convert('RGB')
            input_tensor = self.transform(image).unsqueeze(0).to(self.device)

            with torch.no_grad():
                outputs = self.model(input_tensor)
                probabilities = torch.nn.functional.softmax(outputs[0], dim=0)
                confidence, predicted_idx = torch.max(probabilities, 0)

                disease = self.class_names[predicted_idx.item()]
                confidence_score = confidence.item()

                # Get top 3 predictions for debugging
                top3_conf, top3_idx = torch.topk(probabilities, 3)
                top3_predictions = [
                    {
                        'disease': self.class_names[idx.item()],
                        'confidence': conf.item()
                    }
                    for conf, idx in zip(top3_conf, top3_idx)
                ]

        except Exception as e:
            return {
                'success': False,
                'error': f'Prediction failed: {str(e)}',
                'leaf_detection': leaf_result,
                'blur_result': blur_result,
                'needs_retake': False
            }

        # Step 4: Validate confidence (reject non-leaf or unknown objects)
        if confidence_score < CONFIDENCE_THRESHOLD:
            return {
                'success': False,
                'error': f'Low confidence detection ({confidence_score:.1%}). Our AI is uncertain about this image. Please retake the photo ensuring: (1) Good lighting, (2) Clear focus on leaf, (3) Apple/Grape/Tomato leaves only.',
                'leaf_detection': leaf_result,
                'blur_result': blur_result,
                'confidence': confidence_score,
                'disease': disease,
                'top3_predictions': top3_predictions,
                'is_low_confidence': True,
                'needs_retake': True,
                'retake_reason': 'low_confidence'
            }

        # Step 5: Get recommendation
        from ..config import DISEASE_RECOMMENDATIONS
        recommendation = DISEASE_RECOMMENDATIONS.get(
            disease,
            'Consult a local agronomist for treatment recommendations.'
        )

        return {
            'success': True,
            'disease': disease,
            'confidence': confidence_score,
            'leaf_detection': leaf_result,
            'blur_result': blur_result,
            'recommendation': recommendation,
            'top3_predictions': top3_predictions,
            'needs_retake': False
        }


# Singleton predictor instance
_predictor = None

def get_predictor():
    """Get or create predictor instance (lazy loading)"""
    global _predictor
    if _predictor is None:
        try:
            _predictor = PlantDiseasePredictor()
            print(f"✓ CNN model loaded from {MODEL_PATH}")
        except Exception as e:
            print(f"⚠ Could not load CNN model: {e}")
            _predictor = None
    return _predictor
