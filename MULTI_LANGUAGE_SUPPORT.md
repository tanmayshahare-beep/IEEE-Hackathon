# 🌐 Multi-Language Support Feature

## Overview

AgroDoc-AI now supports **three languages** for a more inclusive user experience:
- **English (EN)** - Default
- **Hindi (HI)** - हिंदी
- **Kannada (KN)** - ಕನ್ನಡ

Users can switch languages at any time from the login or registration pages.

---

## 🎯 Features

### 1. **Language Selector Modal**
- Beautiful popup modal with language options
- Accessible from login and registration pages
- Smooth animations and transitions
- Premium dark theme with gold accents

### 2. **Real-Time Translation**
- Instant language switching without page reload
- All UI elements translated dynamically
- Form labels, buttons, and placeholders
- Error and success messages

### 3. **Persistent Preference**
- Language choice saved in browser localStorage
- Session-based storage for logged-in users
- Automatically applied on return visits

---

## 🖼️ User Interface

### Language Selector Button
- Located in navigation bar (when not logged in)
- Shows current language code (EN/HI/KN)
- Globe icon (🌐) for easy identification

### Language Modal
```
┌─────────────────────────────────┐
│  🌐 Select Language        ✕    │
│  Choose your preferred language │
│                                 │
│  ┌──────────────────────────┐  │
│  │ 🇬🇧 English               │  │
│  └──────────────────────────┘  │
│  ┌──────────────────────────┐  │
│  │ 🇮🇳 हिंदी (Hindi)         │  │
│  └──────────────────────────┘  │
│  ┌──────────────────────────┐  │
│  │ 🇮🇳 ಕನ್ನಡ (Kannada)       │  │
│  └──────────────────────────┘  │
│                                 │
│          [ Close ]              │
└─────────────────────────────────┘
```

---

## 🛠️ Technical Implementation

### Files Created/Modified

| File | Purpose |
|------|---------|
| `app/static/js/translations.json` | Translation strings for all languages |
| `app/static/js/translations.js` | Language switching logic |
| `app/templates/base.html` | Language modal + selector button |
| `app/templates/auth/login.html` | Translated login form |
| `app/templates/auth/register.html` | Translated registration form |
| `app/templates/auth/verify_otp.html` | Translated OTP verification |
| `app/templates/auth/verify_otp_login.html` | Translated OTP login |
| `app/routes/auth.py` | Backend language preference route |
| `app/static/css/agri-ai-replica.css` | Modal styling |

### Translation Keys

```javascript
{
  "welcome_back": "🌾 Welcome Back",
  "login_desc": "Login to access your dashboard",
  "password_login": "🔑 Password",
  "otp_login": "📧 OTP Code",
  "username_label": "Username",
  // ... 60+ more keys
}
```

### Data Attributes

HTML elements use `data-translate` attributes:
```html
<h2 data-translate="welcome_back">🌾 Welcome Back</h2>
<input data-translate-placeholder="username_placeholder" placeholder="Enter your username">
```

---

## 🚀 Usage

### For Users

1. **Open Login/Register Page**
   - Navigate to `/auth/login` or `/auth/register`

2. **Click Language Button**
   - Click the 🌐 **EN** button in navigation

3. **Select Language**
   - Choose English, Hindi, or Kannada
   - UI updates instantly

4. **Continue Using App**
   - Language preference persists across sessions

### For Developers

#### Add New Translations

1. **Add to translations.json:**
```json
{
  "en": {
    "new_key": "English text"
  },
  "hi": {
    "new_key": "हिंदी टेक्स्ट"
  },
  "kn": {
    "new_key": "ಕನ್ನಡ ಪಠ್ಯ"
  }
}
```

2. **Update HTML elements:**
```html
<span data-translate="new_key">English text</span>
```

3. **For input placeholders:**
```html
<input data-translate-placeholder="placeholder_key" placeholder="...">
```

#### Add New Language

1. Add language code to `languageNames` object in `translations.js`
2. Add all translation keys to `translations.json`
3. Add language option to modal in `base.html`

---

## 📱 Responsive Design

### Desktop (>768px)
- Modal width: 450px max
- Full language names visible
- Hover effects enabled

### Mobile (<768px)
- Modal width: 95%
- Compact padding
- Optimized touch targets

---

## 🔧 Configuration

### Supported Languages

```javascript
const languageNames = {
    'en': 'EN',
    'hi': 'HI',
    'kn': 'KN'
};
```

### Default Language
- Falls back to English if no preference set
- Browser language detection (future enhancement)

---

## 🎨 Styling

### Modal Theme
- **Background:** Dark gradient (#292524 → #1c1917)
- **Border:** Gold (#eab308)
- **Shadow:** Gold glow effect
- **Animation:** Scale + fade in/out

### Language Options
- **Background:** Semi-transparent white
- **Border:** Gold with hover effect
- **Hover:** Transform + color change
- **Active:** Scale down effect

---

## 🧪 Testing

### Manual Testing

1. **Language Switching:**
   - [ ] Click language button
   - [ ] Select Hindi
   - [ ] Verify all text translated
   - [ ] Select Kannada
   - [ ] Verify all text translated
   - [ ] Select English
   - [ ] Verify all text translated

2. **Persistence:**
   - [ ] Select language
   - [ ] Refresh page
   - [ ] Verify language persists
   - [ ] Close browser
   - [ ] Reopen and verify persistence

3. **Forms:**
   - [ ] Login form labels translate
   - [ ] Register form labels translate
   - [ ] Placeholders translate
   - [ ] Buttons translate

### Browser Testing
- Chrome ✓
- Firefox ✓
- Edge ✓
- Safari (to test)

---

## 🐛 Troubleshooting

### Issue: Language not changing

**Solution:**
1. Check browser console for errors
2. Verify `translations.json` loads correctly
3. Clear browser cache

### Issue: Some text not translating

**Solution:**
1. Check `data-translate` attribute spelling
2. Verify translation key exists in JSON
3. Check for nested HTML elements

### Issue: Modal not appearing

**Solution:**
1. Check CSS for `.language-modal` class
2. Verify JavaScript loaded correctly
3. Check for conflicting z-index values

---

## 📊 Translation Coverage

| Page | Coverage |
|------|----------|
| Login | 100% |
| Register | 100% |
| OTP Verify (Register) | 100% |
| OTP Verify (Login) | 100% |
| Navigation | 80% |
| Dashboard | Coming soon |
| Predictions | Coming soon |

---

## 🚀 Future Enhancements

### Planned Features

1. **More Languages**
   - Tamil
   - Telugu
   - Marathi
   - Gujarati

2. **Auto-Detection**
   - Browser language detection
   - Geo-location based suggestion

3. **Full App Translation**
   - Dashboard
   - Prediction results
   - AI chatbot responses
   - Farm map interface

4. **Accessibility**
   - RTL language support (Arabic)
   - Screen reader optimization
   - Font size adjustments

5. **User Preferences**
   - Profile language setting
   - Per-page language override
   - Translation quality feedback

---

## 📝 Translation Best Practices

### Do's
- ✅ Keep translations concise
- ✅ Preserve emoji icons
- ✅ Maintain tone (friendly, professional)
- ✅ Test with native speakers
- ✅ Use consistent terminology

### Don'ts
- ❌ Don't translate technical terms (GPS, OTP)
- ❌ Don't change HTML structure
- ❌ Don't remove data attributes
- ❌ Don't mix languages in same element

---

## 🔗 Related Documentation

- [Gmail OTP Setup](GMAIL_OTP_SETUP.md)
- [Authentication Flow](ARCHITECTURE_DIAGRAMS.md)
- [Frontend Styling](app/static/css/README.md)

---

## 📞 Support

For translation issues or suggestions:
1. Check `translations.json` for correct keys
2. Verify language code is supported
3. Test in browser console with `setLanguage('hi')`

---

**Last Updated:** April 2026  
**Version:** 1.0  
**Languages Supported:** 3 (EN, HI, KN)

---

**Built with ❤️ for inclusive farming**

*AgroDoc-AI - Now speaking your language!*
