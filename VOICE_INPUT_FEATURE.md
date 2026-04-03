# 🎤 Voice Input with Translation Feature

## Overview

The Voice Input feature allows users to speak their questions in **Hindi, Kannada, or English**, automatically translates to English for Ollama processing, then translates the AI response back to the user's language with text-to-speech support.

---

## 🌟 Key Features

### 1. **Voice Input (Speech-to-Text)**
- Click microphone button 🎤 in chatbot
- Speak in your language (Hindi/Kannada/English)
- Browser's Web Speech API captures speech
- Automatically translates to English for Ollama

### 2. **Translation Pipeline**
```
User speaks Hindi/Kannada
    ↓
Speech Recognition (browser)
    ↓
Text in user's language
    ↓
Google Translate → English
    ↓
Ollama processes English
    ↓
AI response in English
    ↓
Google Translate → Hindi/Kannada
    ↓
Display + Text-to-Speech
```

### 3. **Text-to-Speech Output**
- AI responses displayed in user's language
- Speaker button 🔊 on each AI message
- Click to hear response spoken aloud
- Uses browser's SpeechSynthesis API

---

## 🎯 User Flow

### **Hindi User Example:**

1. **User clicks microphone** 🎤
2. **Speaks in Hindi:** "इस बीमारी का इलाज क्या है?"
3. **Speech recognition** converts to text
4. **Translation:** Hindi → English
   - "What is the treatment for this disease?"
5. **Ollama processes** the English question
6. **AI generates** English response
7. **Translation:** English → Hindi
   - "इस रोग के लिए अनुशंसित उपचार..."
8. **Display** Hindi response in chatbot
9. **User can click** 🔊 to hear it spoken

---

## 🔧 Technical Implementation

### **Backend Components**

#### 1. **translation_service.py** - Translation Functions

```python
def translate_speech_to_text(text, source_lang, target_lang='en'):
    """Translate speech-to-text from user language to English"""
    # Uses Google Translate via deep-translator
    
def translate_text_to_speech(text, source_lang='en', target_lang):
    """Translate text for TTS output"""
    # Uses Google Translate via deep-translator
    
def get_speech_recognition_language(lang_code):
    """Get BCP-47 language code for Web Speech API"""
    # Returns: hi-IN, kn-IN, en-US
```

#### 2. **ollama.py** - API Endpoints

```python
@bp.route('/api/translate-speech', methods=['POST'])
def translate_speech():
    """Translate voice input from user language to English"""
    # Receives: {text, source_lang, target_lang}
    # Returns: {translated_text}

@bp.route('/api/user-language')
def get_user_language():
    """Get user's preferred language"""
    # Returns: {language: 'hi'|'kn'|'en'}

@bp.route('/api/chat', methods=['POST'])
def chat():
    """Chat with AI - translates response to user language"""
    # Already implemented in previous translation fixes
```

### **Frontend Components**

#### 1. **upload.html** - Voice Input UI

**HTML:**
```html
<div class="chat-input-area">
    <textarea id="chat-input"></textarea>
    <button id="voice-btn" onclick="toggleVoiceInput()">🎤</button>
    <button id="send-btn" onclick="handleSendMessage()">📤 Send</button>
</div>
```

**JavaScript:**
```javascript
// Speech recognition initialization
function initSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || 
                               window.webkitSpeechRecognition;
    recognition = new SpeechRecognition();
    recognition.lang = langCodes[userLanguage];  // hi-IN, kn-IN, en-US
    recognition.onresult = function(event) {
        // Get transcribed text
        transcript = event.results[0][0].transcript;
        // Send for translation
        translateVoiceInput(transcript);
    };
}

// Translate voice input
async function translateVoiceInput(text) {
    const response = await fetch('/ollama/api/translate-speech', {
        text: text,
        source_lang: userLanguage,
        target_lang: 'en'
    });
    const data = await response.json();
    // Put translated text in input
    document.getElementById('chat-input').value = data.translated_text;
    // Auto-send
    handleSendMessage();
}

// Text-to-speech
function speakText(text) {
    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.lang = langCodes[userLanguage];  // hi-IN, kn-IN
    window.speechSynthesis.speak(utterance);
}
```

---

## 📱 Browser Support

### **Speech Recognition**
| Browser | Support | Notes |
|---------|---------|-------|
| Chrome | ✅ Full | Best support |
| Edge | ✅ Full | Chromium-based |
| Firefox | ⚠️ Limited | May need flags |
| Safari | ⚠️ Limited | iOS support varies |

### **Text-to-Speech**
| Browser | Support | Notes |
|---------|---------|-------|
| Chrome | ✅ Full | Good Hindi/Kannada voices |
| Edge | ✅ Full | Natural voices |
| Firefox | ✅ Full | Basic voices |
| Safari | ✅ Full | iOS voices |

---

## 🎨 UI Components

### **Voice Button States**

**Idle:**
```
🎤 Blue button, hover effect
```

**Listening:**
```
🎤 Red button, pulsing animation
```

**Processing:**
```
⏳ Hourglass, disabled
```

### **Speak Button**

Appears on AI responses for non-English users:
```
┌─────────────────────────┐
│ AI response text...     │
│                         │
│              🔊 [Speak] │
└─────────────────────────┘
```

---

## 🌐 Language Codes

### **Speech Recognition (BCP-47)**
```javascript
const langCodes = {
    'en': 'en-US',  // English (US)
    'hi': 'hi-IN',  // Hindi (India)
    'kn': 'kn-IN'   // Kannada (India)
};
```

### **Google Translate**
```python
lang_map = {
    'hi': 'hindi',
    'kn': 'kannada',
    'en': 'english'
}
```

---

## 🧪 Testing Guide

### **Test Voice Input (Hindi)**

1. **Setup:**
   - Login with Hindi language selected
   - Upload diseased plant image
   - Wait for chatbot to appear

2. **Voice Test:**
   - Click 🎤 microphone button
   - Allow microphone permission if prompted
   - Speak: "इस बीमारी के लक्षण क्या हैं?"
   - Watch for red pulsing button (listening)
   - See transcribed Hindi text
   - See translation to English
   - Wait for AI response in Hindi

3. **Verify:**
   - ✅ Hindi speech recognized
   - ✅ Translated to English
   - ✅ Ollama responded
   - ✅ Response translated to Hindi
   - ✅ Click 🔊 to hear spoken Hindi

### **Test Voice Input (Kannada)**

1. **Setup:**
   - Switch language to Kannada
   - Upload new image

2. **Voice Test:**
   - Click 🎤
   - Speak: "ಈ ರೋಗಕ್ಕೆ ಚಿಕಿತ್ಸೆ ಏನು?"
   - Verify translation and response

3. **Verify:**
   - ✅ Kannada speech recognized
   - ✅ Response in Kannada
   - ✅ Text-to-speech works

---

## 🐛 Troubleshooting

### **Issue: Microphone not working**

**Solutions:**
1. Check browser microphone permissions
2. Use HTTPS or localhost (required for mic access)
3. Try Chrome browser (best support)
4. Check system microphone settings

### **Issue: Speech not recognized**

**Solutions:**
1. Speak clearly and at moderate pace
2. Reduce background noise
3. Check if language matches selected language
4. Try typing to verify backend is working

### **Issue: Translation incorrect**

**Solutions:**
1. Check internet connection (Google Translate API)
2. Try simpler sentences
3. Verify deep-translator package installed
4. Check backend logs for translation errors

### **Issue: Text-to-speech not working**

**Solutions:**
1. Check browser TTS support
2. Verify language voices installed
3. Check system volume
4. Try different browser

---

## 📦 Dependencies

### **Python Packages**
```txt
deep-translator  # Google Translate integration
```

### **Browser APIs**
- Web Speech API (SpeechRecognition)
- SpeechSynthesis API (Text-to-Speech)

---

## 🔒 Privacy & Security

### **Microphone Access**
- Requires explicit user permission
- Only active when button is clicked
- Visual indicator (red pulsing) when listening
- No audio is recorded or stored

### **Data Flow**
```
User speech → Browser STT → Text only → Backend → Google Translate
                                                              ↓
User hears ← Browser TTS ← Text only ← Backend ← Ollama
```

**No audio files are ever:**
- Stored on server
- Sent to backend
- Shared with third parties

Only **text** is transmitted after browser's speech recognition.

---

## 🚀 Performance

### **Latency Breakdown**
| Step | Time |
|------|------|
| Speech recognition | 1-3s |
| Translation (HI→EN) | 0.5-1s |
| Ollama processing | 2-5s |
| Translation (EN→HI) | 0.5-1s |
| **Total** | **4-10s** |

### **Optimization Tips**
1. Pre-load speech recognition on page load
2. Cache common translations
3. Use streaming translation (future)
4. Show progress indicators

---

## 🎯 Future Enhancements

1. **Offline Support**
   - Offline speech recognition
   - Local translation models
   - Cached AI responses

2. **Voice Commands**
   - "Show me history"
   - "Save this prediction"
   - "Export results"

3. **Multi-language Voices**
   - Better Hindi voice quality
   - Better Kannada voice quality
   - Regional dialect support

4. **Voice Training**
   - Learn user's voice patterns
   - Improve recognition accuracy
   - Personalized vocabulary

5. **Conversation Mode**
   - Hold button for push-to-talk
   - Auto-listen after AI response
   - Natural conversation flow

---

## 📊 Usage Analytics

### **Track Metrics:**
- Voice input usage rate
- Language distribution
- Recognition accuracy
- Translation quality ratings
- TTS usage rate

### **Example Analytics:**
```javascript
// Track voice input usage
analytics.track('voice_input_used', {
    language: userLanguage,
    success: true,
    duration: listeningTime
});

// Track TTS usage
analytics.track('tts_played', {
    language: userLanguage,
    message_id: messageId
});
```

---

## 🔗 Related Documentation

- [Multi-Language Support](MULTI_LANGUAGE_SUPPORT.md)
- [Translation Fixes](TRANSLATION_FIXES_SUMMARY.md)
- [Chatbot Integration](CHATBOT_INTEGRATION.md)
- [Ollama Setup](OLLAMA_SETUP_PHI3.md)

---

## 📞 Support

For voice input issues:
1. Check browser compatibility
2. Verify microphone permissions
3. Test with English first
4. Check browser console for errors
5. Review backend logs

---

**Status:** ✅ Complete  
**Date:** April 2026  
**Languages:** English, Hindi, Kannada  
**Browsers:** Chrome (recommended), Edge, Firefox

---

**Built with ❤️ for accessible farming**

*AgroDoc-AI - Now with voice!*
