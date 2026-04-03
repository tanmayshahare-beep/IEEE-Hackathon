# 🌾 VillageCrop - Yield Impact Analysis Feature

## Overview

The Yield Impact Analysis feature helps farmers understand the economic impact of crop diseases and make informed decisions about treatment. It calculates expected yield loss based on disease progression and provides economic impact estimates.

---

## 🎯 Key Features

### 1. **Location-Based Registration**
Users can provide their farm location during registration using:
- **GPS Location**: Automatic detection via browser geolocation API
- **Manual Entry**: Select state and district from dropdown lists

### 2. **Crop Information Collection**
For diseased plants, users are prompted to provide:
- **Total Affected Area** (in acres)
- **Planting Month** (when the crop was planted/pruned)
- **Farming Type** (Traditional or High Density for apples)

### 3. **Yield Loss Calculation**
The system calculates yield loss using disease-specific spread rates based on agricultural research:

- **Initial Disease Impact**: 12% yield loss at detection
- **Monthly Spread Rate**: Varies by disease type and severity

**Tomato Diseases:**
| Disease | Spread Rate | Rationale |
|---------|-------------|-----------|
| Early Blight | 10%/month | Moderate spread, fungal |
| Late Blight | 20%/month | Rapid spread, can destroy crop in weeks |
| Bacterial Spot | 8%/month | Moderate spread via water splash |
| Leaf Mold | 6%/month | Slower in protected conditions |
| Mosaic Virus | 12%/month | Spreads via aphid vectors |

**Grape Diseases:**
| Disease | Spread Rate | Rationale |
|---------|-------------|-----------|
| Downy Mildew | 15%/month | Fast in humid conditions |
| Powdery Mildew | 12%/month | Moderate-fast, airborne |
| Black Rot | 14%/month | Fast in warm, wet weather |
| Esca | 3%/month | Slow trunk disease |

**Apple Diseases:**
| Disease | Spread Rate | Rationale |
|---------|-------------|-----------|
| Apple Scab | 8%/month | Moderate in wet conditions |
| Black Rot | 10%/month | Faster in humid weather |
| Cedar Apple Rust | 6%/month | Requires alternate host |
| Fire Blight | 15%/month | Very rapid bacterial spread |

**Formula:**
```
Total Loss % = Initial Impact (12%) + (Disease-Specific Rate × Months to Harvest)
Maximum capped at 100% (total crop loss)
```

### 4. **Economic Impact Analysis**
Provides detailed economic calculations:
- Expected yield (healthy baseline)
- Salvageable yield (after disease loss)
- Lost yield (tonnes)
- Expected revenue (after loss)
- Treatment cost estimate
- Net revenue after treatment

---

## 📊 Crop Data (from Context_for_crops.txt)

### Tomato
| Parameter | Value |
|-----------|-------|
| Yield per Acre | 10-20 tonnes (avg: 15) |
| Investment per Acre | ₹60,000 - ₹1,25,000 |
| Market Price | ₹2-19/kg (varies widely) |
| Planting Seasons | Kharif (Jun-Jul), Rabi (Nov-Dec), Summer (Feb) |
| **Disease Spread Rates** | **Early Blight: 10%/mo, Late Blight: 20%/mo** |
| Major States | Maharashtra, Bihar, Karnataka, UP, Andhra Pradesh |

### Grape
| Parameter | Value |
|-----------|-------|
| Yield per Acre | 8-16 tonnes (avg: 12) |
| Investment per Acre | ₹1,50,000 - ₹3,00,000 |
| Market Price | ₹20-80/kg |
| Planting Seasons | Main (Sep-Nov), Early (Jul-Aug) |
| **Disease Spread Rates** | **Downy Mildew: 15%/mo, Black Rot: 14%/mo** |
| Major States | Maharashtra, Karnataka, Tamil Nadu |

### Apple
| Parameter | Value |
|-----------|-------|
| Yield (Traditional) | 4-5 tonnes/acre |
| Yield (High Density) | 20-28 tonnes/acre |
| Investment (Traditional) | ₹1,00,000 - ₹2,00,000 |
| Investment (High Density) | ₹3,00,000 - ₹5,00,000 |
| Market Price | ₹60-220/kg |
| **Disease Spread Rates** | **Scab: 8%/mo, Fire Blight: 15%/mo** |
| Major States | HP, J&K, Uttarakhand |

---

## 🔧 Technical Implementation

### Files Modified/Created

1. **`app/services/yield_calculator.py`**
   - Core yield calculation logic
   - Crop data from Context_for_crops.txt
   - Disease impact calculations

2. **`app/routes/auth.py`**
   - Updated registration to collect location
   - GPS or manual location entry

3. **`app/routes/predictions.py`**
   - New API endpoints:
     - `POST /predictions/api/save-crop-info`
     - `GET /predictions/api/crop-info/<prediction_id>`
   - Updated prediction schema

4. **`app/templates/auth/register.html`**
   - Location collection UI
   - GPS detection button
   - State/district dropdowns

5. **`app/templates/predictions/upload.html`**
   - Yield impact analysis section
   - Crop information modal
   - Economic impact display

---

## 📝 MongoDB Schema Updates

### User Document
```javascript
{
  _id: ObjectId,
  username: String,
  email: String,
  password: String,
  email_verified: Boolean,
  location: {
    type: "gps" | "manual",
    gps: {
      latitude: Number,
      longitude: Number
    },
    // OR
    manual: {
      state: String,
      district: String
    }
  },
  farm_boundaries: GeoJSON,
  predictions: [ObjectId],
  created_at: Date
}
```

### Prediction Document
```javascript
{
  _id: ObjectId,
  user_id: ObjectId,
  image_filename: String,
  image_data: Binary,
  disease: String,
  confidence: Number,
  recommendation: String,
  crop_info: {
    acres: Number,
    planting_month: Number,
    farming_type: String,
    crop_type: String,
    location: Object,
    submitted_at: Date
  },
  yield_analysis: {
    expected_yield: Object,
    disease_impact: Object,
    calculated_at: Date
  },
  timestamp: Date
}
```

---

## 🚀 Usage Flow

### 1. Registration (Location Collection)
```
User visits /auth/register
  ↓
Enters username, email, password
  ↓
Chooses location method:
  - GPS: Click "Get My Location" → Browser prompts for permission
  - Manual: Select State → Select District
  ↓
Submit → OTP verification → Account created
```

### 2. Disease Detection & Yield Analysis
```
User uploads leaf image
  ↓
CNN predicts disease (e.g., "Tomato___Early_blight")
  ↓
If DISEASED:
  - Show "Yield Impact Analysis" section
  - Display "Update Crop Information" button
  ↓
User clicks button → Modal opens
  ↓
User enters:
  - Acres: 2.5
  - Planting Month: June
  - Farming Type: Traditional
  ↓
Submit → API calculates yield impact
  ↓
Display results:
  - Months to harvest: 4 months
  - Total loss: 44% (12% initial + 8%×4 months)
  - Salvageable yield: 25.2 tonnes
  - Lost yield: 16.8 tonnes
  - Economic loss: ₹1,34,400
  - Treatment cost: ₹12,500
```

---

## 📱 UI Components

### Yield Impact Section
```
┌─────────────────────────────────────────────┐
│ 📊 Yield Impact Analysis                    │
├─────────────────────────────────────────────┤
│ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐        │
│ │🌱    │ │📏    │ │📅    │ │⏳    │        │
│ │Crop  │ │Area  │ │Month │ │Months│        │
│ │Tomato│ │2.5ac │ │Jun   │ │4     │        │
│ └──────┘ └──────┘ └──────┘ └──────┘        │
│                                             │
│ Initial Disease Impact:       12%           │
│ Monthly Spread Rate:          8%/month      │
│ ─────────────────────────────────           │
│ Total Expected Loss:          44%           │
│                                             │
│ [████████████████░░░░░░░░░░] 56% Salvageable│
│                                             │
│ Expected Yield:     25.2 tonnes             │
│ Potential Loss:     16.8 tonnes             │
│                                             │
│ 💰 Economic Impact                          │
│ Expected Revenue:   ₹ 2.01 Lakhs            │
│ Treatment Cost:     ₹ 12,500                │
│ Net Revenue:        ₹ 1.89 Lakhs            │
│                                             │
│ [📝 Update Crop Information]                │
└─────────────────────────────────────────────┘
```

---

## 🔐 API Endpoints

### Save Crop Information
```http
POST /predictions/api/save-crop-info
Content-Type: application/json
Cookie: session=<session_id>

{
  "prediction_id": "65f1234567890abcdef12345",
  "acres": 2.5,
  "planting_month": 6,
  "farming_type": "traditional"
}
```

**Response:**
```json
{
  "success": true,
  "crop_type": "Tomato",
  "expected_yield": {
    "average_tonnes": 37.5,
    "revenue": {...},
    "investment_inr": 162500
  },
  "disease_impact": {
    "acres": 2.5,
    "months_to_harvest": 4,
    "yield_loss": {
      "total_loss_percentage": 44.0,
      "lost_yield_tonnes": 16.5,
      "salvageable_yield_tonnes": 21.0
    },
    "economic_impact": {
      "economic_loss_inr": 132000,
      "expected_revenue_inr": 168000,
      "treatment_cost_inr": 12500
    }
  }
}
```

### Get Crop Information
```http
GET /predictions/api/crop-info/<prediction_id>
Cookie: session=<session_id>
```

---

## 🧪 Testing

### Test Scenarios

1. **Healthy Plant Detection**
   - Upload healthy leaf image
   - Verify yield impact section is HIDDEN
   - No crop info prompt shown

2. **Diseased Plant - With Crop Info**
   - Upload diseased leaf image
   - Click "Update Crop Information"
   - Enter acres: 2.5, planting month: June
   - Verify yield calculations display correctly

3. **Diseased Plant - Without Crop Info**
   - Upload diseased leaf image
   - Yield impact section visible but shows placeholder
   - User prompted to enter crop info

4. **Location Registration**
   - Register with GPS location
   - Verify coordinates saved in MongoDB
   - Register with manual location
   - Verify state/district saved

---

## 📈 Future Enhancements

1. **Weather Integration**
   - Pull local weather data based on GPS location
   - Adjust disease spread rate based on humidity/temperature

2. **Historical Analysis**
   - Track yield losses over time
   - Provide trend analysis for returning users

3. **Treatment Recommendations**
   - Connect with local agricultural suppliers
   - Estimate treatment availability by district

4. **Market Price Integration**
   - Real-time mandi prices via API
   - Price trend predictions

5. **Multi-Crop Support**
   - Expand to additional crops (Potato, Corn, etc.)
   - Region-specific crop recommendations

---

## 🐛 Known Limitations

1. **Disease Spread Rate**: Fixed rates used; actual spread varies based on:
   - Weather conditions
   - Crop variety resistance
   - Farming practices
   - Disease severity at detection

2. **Yield Estimates**: Based on average yields; actual yields depend on:
   - Soil quality
   - Irrigation availability
   - Farmer expertise
   - Input quality (seeds, fertilizers)

3. **Market Prices**: Conservative estimates used; actual prices vary by:
   - Market location
   - Season
   - Quality grading
   - Market volatility

---

## 📞 Support

For questions or issues with the Yield Impact Analysis feature:
1. Check calculation logic in `app/services/yield_calculator.py`
2. Verify crop data matches `Context_for_crops.txt`
3. Review API endpoint responses in browser dev tools
4. Check MongoDB documents for data structure

---

**Last Updated:** April 2026
**Version:** 1.0
