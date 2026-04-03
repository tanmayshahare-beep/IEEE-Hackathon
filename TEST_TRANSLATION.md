# 🧪 Translation System Testing Guide

## ✅ What's Fixed

### Backend Translation
1. **Ollama Service** - Now properly passes language to Ollama API
2. **Healthy Messages** - `get_healthy_message()` now accepts language parameter
3. **Summary Generation** - `generate_formatted_summary()` now accepts language parameter
4. **CNN Predictions** - Results translated before returning to frontend

### Frontend Translation
1. **Dynamic Translator** - New `translatePage()` function for dynamically loaded content
2. **Exported Functions** - `translatePage()` now available globally
3. **Better Error Handling** - Improved logging for debugging

## 🚀 How to Test

### Test 1: Language Selector (Frontend)

```bash
# 1. Start the application
python run.py

# 2. Open browser to http://localhost:5000

# 3. Open browser console (F12)

# 4. Test translation functions in console:
console.log(window.currentLanguage);  // Should show current language
console.log(window.translate('welcome_back'));  // Should translate

# 5. Click 🌐 EN button → Select Hindi

# 6. Verify:
#    - All text changes to Hindi
#    - Toast notification appears
#    - Language persists on refresh
```

### Test 2: CNN Prediction Translation (Backend)

```bash
# 1. Login to the application

# 2. Change language to Hindi

# 3. Go to Disease Detection page

# 4. Upload a plant image

# 5. Check the response in browser Network tab:
#    - Look for /predictions/api/predict
#    - Response should have:
#      {
#        "disease": "टमाटर - अर्ली ब्लाइट",  # Translated!
#        "disease_original": "Tomato___Early_blight",
#        "recommendation": "कवकनाशकों का प्रयोग करें...",  # Translated!
#        "language": "hi"
#      }

# 6. Verify disease name and recommendation are in Hindi
```

### Test 3: Ollama AI Translation (Backend)

```bash
# 1. Make sure Ollama is running:
ollama serve

# 2. Login and change language to Hindi

# 3. Upload an image and get prediction

# 4. Click "Generate AI Answers" or go to AI Answers page

# 5. Check browser console for:
#    "Generating Ollama responses for: Tomato___Early_blight in language: hi"

# 6. Verify responses are in Hindi:
#    - Look for Hindi text in responses
#    - Should see Devanagari script
#    - Technical terms may have English note
```

### Test 4: Dynamic Content Translation

```javascript
// In browser console, test translating dynamic content:

// 1. Change language to Hindi
window.setLanguage('hi');

// 2. Simulate dynamic content (like prediction results)
const resultCard = document.createElement('div');
resultCard.setAttribute('data-translate', 'confidence');
resultCard.textContent = 'Confidence';
document.body.appendChild(resultCard);

// 3. Translate the new content
window.translatePage();

// 4. Verify resultCard now shows Hindi text
console.log(resultCard.textContent);  // Should show "विश्वास"
```

## 🐛 Debugging

### Check Backend Translation

```python
# In Python shell or Flask route, test:
from app.services.translation_service import translate_disease, translate_recommendation

# Test disease translation
print(translate_disease('Tomato___Early_blight', 'hi'))
# Should print: टमाटर - अर्ली ब्लाइट

print(translate_disease('Tomato___Early_blight', 'kn'))
# Should print: ಟೊಮ್ಯಾಟೋ - ಅರ್ಲಿ ಬ್ಲೈಟ್

# Test recommendation translation
print(translate_recommendation('Tomato___Early_blight', 'Apply fungicides', 'hi'))
# Should print Hindi translation
```

### Check Ollama Translation

```python
# Test Ollama service with language
from app.services.ollama_service import call_ollama

# Test Hindi
response = call_ollama('List symptoms', 'Tomato___Early_blight', 'hi')
print(response)  # Should have Hindi text

# Test Kannada
response = call_ollama('List symptoms', 'Tomato___Early_blight', 'kn')
print(response)  # Should have Kannada text
```

### Check Frontend Translation

```javascript
// In browser console:

// 1. Check if translations loaded
console.log(window.translations);  // Should show translation object

// 2. Check current language
console.log(window.currentLanguage);  // Should show 'hi', 'kn', or 'en'

// 3. Test translation function
console.log(window.translate('welcome_back'));  // Should translate

// 4. Test translatePage function
window.translatePage();  // Should translate all elements with data-translate

// 5. Check for errors
// Look for any red errors in console
```

## 📊 Expected Results

### CNN Prediction (Hindi)

```json
{
  "success": true,
  "disease": "टमाटर - अर्ली ब्लाइट",
  "disease_original": "Tomato___Early_blight",
  "confidence": 0.92,
  "recommendation": "क्लोरथालोनिल जैसे कवकनाशकों का प्रयोग करें...",
  "language": "hi"
}
```

### Ollama Response (Hindi)

```
🔍 लक्षण (Symptoms):
• पत्तियों पर भूरे धब्बे
• निचली पत्तियां पहले प्रभावित
• धब्बों के चारों ओर पीला हलो

💊 उपचार (Treatment):
• क्लोरथालोनिल कवकनाशक लगाएं
• संक्रमित पत्तियों को हटाएं
• 7-10 दिन के अंतराल पर छिड़काव करें
```

### Healthy Plant Message (Hindi)

```
🌿 **अच्छी खबर! आपका टमाटर स्वस्थ है!**

**वर्तमान स्थिति:** ✅ कोई रोग का पता नहीं चला

**पौधे के स्वास्थ्य को बनाए रखने के लिए सिफारिशें:**
• अपनी वर्तमान देखभाल की दिनचर्या जारी रखें
• पत्तियों के रंग या बनावट में बदलाव के लिए निगरानी करें
```

## ⚠️ Common Issues

### Issue 1: Ollama Not Responding in Hindi/Kannada

**Cause:** Ollama model (Phi-3) has limited Hindi/Kannada support

**Solution:**
- The system adds language context to prompts
- But Phi-3 may still respond in English
- Translation note is added: "[नोट: तकनीकी जानकारी अंग्रेजी में है]"
- For better results, use a multilingual model

### Issue 2: Dynamic Content Not Translating

**Cause:** Content loaded after page load

**Solution:**
```javascript
// After adding dynamic content, call:
window.translatePage();

// Example: After prediction results load
fetch('/api/predict')
  .then(res => res.json())
  .then(data => {
    // Update UI with results
    document.getElementById('result').textContent = data.disease;
    
    // Translate the new content
    window.translatePage();
  });
```

### Issue 3: Language Not Persisting

**Cause:** Session or localStorage issue

**Solution:**
1. Check browser localStorage:
   ```javascript
   console.log(localStorage.getItem('preferredLanguage'));
   ```
2. Check Flask session in backend
3. Clear browser cache and try again

### Issue 4: Disease Name Not Translating

**Cause:** Disease name not in translation dictionary

**Solution:**
```python
# Check if disease exists in translations
from app.services.translation_service import DISEASE_TRANSLATIONS
print('Tomato___Early_blight' in DISEASE_TRANSLATIONS)  # Should be True

# If not, add it to translation_service.py
```

## 📝 Test Checklist

- [ ] Language selector modal opens
- [ ] Can select Hindi
- [ ] Can select Kannada
- [ ] UI text translates immediately
- [ ] Language persists after refresh
- [ ] CNN predictions return translated disease names
- [ ] CNN predictions return translated recommendations
- [ ] Ollama receives language parameter
- [ ] Ollama responses include Hindi/Kannada text
- [ ] Healthy plant messages are translated
- [ ] Dynamic content can be translated with translatePage()
- [ ] No console errors related to translation

## 🎯 Success Criteria

✅ **Working:**
- Language selector changes all UI text
- CNN predictions translated
- Ollama attempts to respond in selected language
- Language preference persists
- No errors in console

⚠️ **Known Limitations:**
- Phi-3 model has limited Hindi/Kannada support
- Technical terms may remain in English
- Some UI pages still need data-translate attributes

---

**Last Updated:** April 2026
**Translation Version:** 2.0
**Test Status:** Ready for Testing
