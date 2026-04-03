# 🗺️ AgroDoc-AI - Farm Map Feature

## Overview

The Farm Map feature displays your crop health data on an interactive map, showing the location and health status of all scanned plants. This helps farmers visualize disease distribution across their farm and make informed decisions about treatment priorities.

---

## 🎯 Key Features

### 1. **Interactive Farm Map**
- **Leaflet.js** powered interactive map
- Displays farm boundaries (if uploaded)
- Shows crop markers with health status
- Custom markers for each crop type

### 2. **Crop Health Markers**
Each scanned plant appears on the map with:
- **🍎/🍇/🍅 Icon** - Crop type indicator
- **Green marker** - Healthy plant
- **Red marker** - Diseased plant
- **Popup details** - Disease name, confidence, date

### 3. **Farm Statistics Dashboard**
Real-time statistics showing:
- Total scans performed
- Healthy vs. diseased count
- Crop type breakdown
- Health percentage per crop

### 4. **Crop Type Filtering**
Click on any crop in the sidebar to:
- Zoom to that crop's location
- View all instances of that crop
- See health distribution

---

## 📍 How Location Works

### **GPS Location (Precise)**
If user registered with GPS:
- Exact coordinates stored
- Markers placed at precise farm location
- Accuracy within meters

### **Manual Location (Approximate)**
If user registered with State/District:
- Uses state capital coordinates
- Markers spread randomly within ~1km radius
- Good for regional overview

### **Location Data Storage**
```javascript
// MongoDB User Document
{
  location: {
    type: "gps" | "manual",
    gps: {
      latitude: 19.0760,
      longitude: 72.8777
    },
    // OR
    manual: {
      state: "Maharashtra",
      district: "Mumbai"
    }
  }
}
```

---

## 🗺️ Map Features

### **Markers**
- **Custom styled** with crop emojis
- **Color-coded** by health status
- **Clickable** for detailed popup
- **Slightly randomized** to avoid overlap

### **Farm Boundaries**
If GeoJSON/KML uploaded:
- Displayed as yellow polygon overlay
- Shows exact farm perimeter
- Auto-zoom to fit boundaries + markers

### **Legend**
Bottom-right corner shows:
- Green marker = Healthy crop
- Red marker = Diseased crop

---

## 📊 Statistics Panel

### **Overview Stats**
| Stat | Description |
|------|-------------|
| Total Scans | All predictions uploaded |
| Healthy | Count of healthy plants |
| Diseased | Count of diseased plants |
| Crop Types | Number of different crops |

### **Crop Breakdown**
For each crop type (Apple, Grape, Tomato):
- Total count
- Healthy count (✓)
- Diseased count (⚠)

**Example:**
```
🍎 Apple
✓ 5 Healthy  ⚠ 2 Diseased

🍇 Grape
✓ 3 Healthy  ⚠ 1 Diseased

🍅 Tomato
✓ 8 Healthy  ⚠ 4 Diseased
```

---

## 🔧 Technical Implementation

### **Backend (farm.py)**

```python
@bp.route('/map')
@login_required
def view_farm_map():
    # Get user's predictions
    predictions = mongo.db.predictions.find({'user_id': user_id})
    
    # Process into markers
    for pred in predictions:
        crop_type = extract_crop_type(pred['disease'])
        is_healthy = 'healthy' in pred['disease'].lower()
        
        # Get location from user profile
        lat, lng = get_user_coordinates(user)
        
        # Add marker with randomness to spread
        markers.append({
            'lat': lat + random_offset,
            'lng': lng + random_offset,
            'disease': pred['disease'],
            'is_healthy': is_healthy,
            'crop_type': crop_type
        })
    
    return render_template('farm/farm_map.html', 
                         markers=markers, 
                         stats=crop_stats)
```

### **Frontend (farm_map.html)**

```javascript
// Initialize map centered on user location
map = L.map('farm-map').setView([userLat, userLng], zoom);

// Add crop markers
cropData.forEach(crop => {
    const icon = createCustomIcon(crop);
    const marker = L.marker([crop.lat, crop.lng], { icon })
        .addTo(map)
        .bindPopup(createPopup(crop));
});

// Load farm boundaries if available
fetch('/farm/api/boundaries')
    .then(data => {
        if (data.has_boundaries) {
            L.geoJSON(data.data).addTo(map);
        }
    });
```

---

## 🎨 Marker Styling

### **CSS Custom Marker**
```css
.custom-marker {
    background: white;
    border: 3px solid;
    border-radius: 50%;
    width: 30px;
    height: 30px;
    display: flex;
    align-items: center;
    justify-content: center;
}

.custom-marker.healthy {
    border-color: #22c55e;
    background: #dcfce7;
}

.custom-marker.diseased {
    border-color: #ef4444;
    background: #fee2e2;
}
```

### **Popup Content**
```html
<div class="popup-title">🍎 Apple</div>
<div>
  <div class="popup-label">Health Status</div>
  <div class="popup-value diseased">⚠ Apple - Apple scab</div>
</div>
<div>
  <div class="popup-label">Confidence</div>
  <div class="popup-value">87.3%</div>
</div>
<div>
  <div class="popup-label">Date</div>
  <div class="popup-value">Apr 2, 2026</div>
</div>
<a href="/predictions/123" class="popup-btn">View Details</a>
```

---

## 🚀 Usage Flow

### **First Time User**
1. Register with location (GPS or manual)
2. Upload plant images via Disease Detection
3. Each prediction stored with user_id
4. Navigate to "🗺️ Farm Map"
5. See all crops displayed on map

### **Returning User**
1. Go to Farm Map from navigation
2. View updated statistics
3. Click crop markers to see details
4. Click sidebar items to focus on crop type
5. View disease distribution patterns

---

## 📱 Responsive Design

### **Desktop (>1024px)**
- Map on left (full height)
- Sidebar on right (400px wide)
- Statistics + crop list visible

### **Tablet/Mobile (<1024px)**
- Map full width
- Sidebar stacks below map
- Scrollable crop list

---

## 🔐 Privacy & Security

### **Location Privacy**
- GPS coordinates stored encrypted
- Manual location uses approximate coordinates
- Markers slightly randomized to avoid exact position disclosure

### **Data Access**
- Users only see their own crop data
- Farm boundaries private to user
- No location data shared publicly

---

## 🐛 Troubleshooting

### **No Markers Showing**
**Problem:** Map shows but no crop markers

**Solutions:**
1. Check if user has location data (GPS or manual)
2. Verify predictions exist in database
3. Check browser console for errors

### **Map Not Centered Correctly**
**Problem:** Map shows wrong location

**Solutions:**
1. For GPS: Check browser location permissions
2. For manual: Verify state selection during registration
3. Default fallback: Central India (20.5937, 78.9629)

### **Farm Boundaries Not Displaying**
**Problem:** Uploaded boundaries not showing

**Solutions:**
1. Verify file format (GeoJSON or KML)
2. Check file validity at geojson.io
3. Ensure file size < 5MB
4. Re-upload if corrupted

---

## 📈 Future Enhancements

1. **Heat Maps** - Show disease density areas
2. **Timeline Slider** - View disease progression over time
3. **Treatment Zones** - Mark areas requiring treatment
4. **Yield Estimation** - Calculate expected yield per zone
5. **Weather Overlay** - Show weather patterns affecting crops
6. **Multi-Farm Support** - Manage multiple farm locations
7. **Export Options** - Download farm map as PDF/image
8. **Collaborative Mapping** - Share farm with advisors

---

## 📍 State Coordinate Reference

```python
STATE_COORDS = {
    'Maharashtra': (19.7515, 75.7139),
    'Karnataka': (15.3173, 75.7139),
    'Tamil Nadu': (11.1271, 78.6569),
    'Andhra Pradesh': (15.9129, 79.7400),
    'Telangana': (18.1124, 79.0193),
    'Himachal Pradesh': (31.8478, 77.2958),
    'Jammu & Kashmir': (33.7782, 76.5762),
    'Uttarakhand': (30.0668, 79.0193),
    'Punjab': (31.1471, 75.3412),
    'Haryana': (29.0588, 76.0856),
    'Uttar Pradesh': (26.8467, 80.9462),
    'Bihar': (25.0961, 85.3131),
    'West Bengal': (22.9868, 87.8550),
    'Orissa': (20.9517, 85.0985),
    'Madhya Pradesh': (22.9734, 78.6569),
    'Assam': (26.2006, 92.9376),
    'Gujarat': (22.2587, 71.1924),
    'Rajasthan': (27.0238, 74.2179),
    'Kerala': (10.8505, 76.2711)
}
```

---

## 📞 Support

For issues with the Farm Map feature:
1. Check browser console for JavaScript errors
2. Verify MongoDB connection
3. Ensure Leaflet.js CDN is accessible
4. Check user location data in database
5. Review farm.py route logs

---

**Last Updated:** April 2026  
**Version:** 1.0  
**Feature:** Farm Map with Crop Markers
