# 📧 Gmail Setup for OTP Email Verification

## Overview

The AgroDoc-AI app now uses **Flask-Mail with Gmail SMTP** to send OTP verification emails during user registration.

---

## 🔧 Gmail Configuration Steps

### Step 1: Enable 2-Factor Authentication (Required)

Gmail requires 2FA to be enabled before you can create an App Password.

1. Go to your Google Account: https://myaccount.google.com/
2. Click on **Security** in the left sidebar
3. Under "Signing in to Google", click **2-Step Verification**
4. Click **Get Started** and follow the setup process
5. Enable 2FA using your phone number or authenticator app

---

### Step 2: Generate Gmail App Password

**Important:** You need an **App Password**, NOT your regular Gmail password!

1. Go to: https://myaccount.google.com/apppasswords
   - Or: Google Account → Security → 2-Step Verification → App passwords

2. Select app and device:
   - **Select app:** Choose "Mail" (or "Other (Custom name)" → enter "AgroDoc-AI")
   - **Select device:** Choose "Windows Computer" (or your device)

3. Click **Generate**

4. Copy the **16-character App Password**:
   ```
   abcd efgh ijkl mnop
   ```
   - This is a **one-time display** - save it securely!
   - No spaces needed when using: `abcdefghijklmnop`

---

### Step 3: Update .env File

Open your `.env` file and update the Gmail settings:

```env
# Flask-Mail Configuration (Gmail SMTP for OTP)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USE_SSL=false

# Replace with YOUR Gmail address
MAIL_USERNAME=your-email@gmail.com

# Replace with YOUR 16-character App Password (no spaces)
MAIL_PASSWORD=abcdefghijklmnop

# Usually same as MAIL_USERNAME
MAIL_DEFAULT_SENDER=your-email@gmail.com

# Set to true for debugging email issues
MAIL_DEBUG=false
```

**Example:**
```env
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USE_SSL=false
MAIL_USERNAME=john.farmer@gmail.com
MAIL_PASSWORD=abcdxyz123456789
MAIL_DEFAULT_SENDER=john.farmer@gmail.com
MAIL_DEBUG=false
```

---

## 📦 Required Python Package

Install Flask-Mail:

```bash
pip install flask-mail
```

Or add to requirements.txt:
```
flask-mail==0.9.1
```

---

## 🧪 Testing the Setup

### Test 1: Start Flask App

```bash
python run.py
```

Check for any mail configuration errors in the console.

### Test 2: Register a New User

1. Go to: http://localhost:5000/auth/register
2. Fill in registration form:
   - Username: testuser
   - Email: your-gmail@gmail.com
   - Password: test123
3. Click "Create Account"

### Test 3: Check Email

You should receive an email with:
- Subject: 🌾 AgroDoc-AI - Email Verification OTP
- A 6-digit verification code
- Beautiful HTML formatting

### Test 4: Verify OTP

1. Enter the 6-digit code on the verification page
2. Click "Verify Email"
3. Account created successfully! ✓

---

## 📧 Email Template Preview

Your OTP emails will look like this:

```
┌─────────────────────────────────────────────┐
│  🌾 AgroDoc-AI                             │
│  AI-Powered Plant Disease Detection         │
├─────────────────────────────────────────────┤
│                                             │
│  Email Verification                         │
│                                             │
│  Hello [Username],                          │
│                                             │
│  Your verification code:                    │
│  ┌─────────────────────────────────┐       │
│  │       1 2 3 4 5 6               │       │
│  └─────────────────────────────────┘       │
│                                             │
│  This OTP is valid for 10 minutes.          │
│                                             │
│  ⚠️ Security Tips:                          │
│  • Do not share this code                   │
│  • AgroDoc-AI never asks for password      │
│  • Ignore if you didn't request             │
│                                             │
└─────────────────────────────────────────────┘
```

---

## ⚙️ SMTP Settings Reference

| Setting | Value | Description |
|---------|-------|-------------|
| MAIL_SERVER | smtp.gmail.com | Gmail SMTP server |
| MAIL_PORT | 587 | TLS port (use 465 for SSL) |
| MAIL_USE_TLS | true | Enable TLS encryption |
| MAIL_USE_SSL | false | Disable SSL (use TLS instead) |
| MAIL_USERNAME | your-email@gmail.com | Your Gmail address |
| MAIL_PASSWORD | app-password | 16-char App Password |
| MAIL_DEFAULT_SENDER | your-email@gmail.com | Sender email |

---

## 🐛 Troubleshooting

### Issue: "Authentication failed" or "Invalid credentials"

**Solutions:**
1. Ensure you're using **App Password**, not regular password
2. Verify 2FA is enabled on your Google account
3. Check for typos in the App Password (no spaces)
4. Make sure App Password was generated for "Mail" app

### Issue: "Connection timed out" or "Cannot connect to server"

**Solutions:**
1. Check your internet connection
2. Verify firewall isn't blocking port 587
3. Try port 465 with SSL instead:
   ```env
   MAIL_PORT=465
   MAIL_USE_TLS=false
   MAIL_USE_SSL=true
   ```

### Issue: Email goes to spam

**Solutions:**
1. Mark the email as "Not Spam" in Gmail
2. Add your sender email to contacts
3. Use a custom domain email in production

### Issue: "Less secure app access" error

**Solution:**
- This setting is deprecated by Google
- You MUST use 2FA + App Password instead
- Follow Step 1 and Step 2 above

### Issue: OTP email not sending

**Debug Mode:**
Enable mail debugging in `.env`:
```env
MAIL_DEBUG=true
```

Check Flask console for error messages.

---

## 🔒 Security Best Practices

### 1. Protect Your App Password

- ✅ Store in `.env` file (not in code)
- ✅ Add `.env` to `.gitignore`
- ❌ Never commit App Password to GitHub
- ❌ Never share your App Password

### 2. Rate Limiting

The OTP system includes:
- ✅ 10-minute expiry
- ✅ Maximum 5 verification attempts
- ✅ 60-second resend cooldown

### 3. Production Recommendations

For production deployment:

1. **Use environment variables:**
   ```bash
   export MAIL_PASSWORD=your-app-password
   ```

2. **Use a dedicated email service:**
   - SendGrid (free tier: 100 emails/day)
   - Mailgun (free tier: 5,000 emails/month)
   - Amazon SES (pay-as-you-go)

3. **Store OTP in database:**
   - Currently stored in memory (resets on restart)
   - Use MongoDB or Redis for production

---

## 📊 How It Works

### Registration Flow

```
User fills registration form
        ↓
Validate input (username, email, password)
        ↓
Store user data in session (temporary)
        ↓
Generate 6-digit OTP
        ↓
Hash OTP with SHA256
        ↓
Send email via Gmail SMTP
        ↓
Redirect to OTP verification page
        ↓
User enters OTP
        ↓
Verify OTP (hash comparison + expiry check)
        ↓
If valid: Create user account in MongoDB
If invalid: Show error, allow retry (max 5 attempts)
```

### OTP Storage

```python
{
    'user@gmail.com': {
        'otp_hash': 'abc123...',      # SHA256 hash of OTP
        'created_at': datetime,        # When created
        'expires_at': datetime,        # 10 minutes from creation
        'attempts': 0                  # Failed attempts counter
    }
}
```

---

## 📝 Files Created/Modified

| File | Status | Purpose |
|------|--------|---------|
| `app/services/otp_service.py` | ✅ Created | OTP generation & verification |
| `app/templates/auth/verify_otp.html` | ✅ Created | OTP verification UI |
| `app/routes/auth.py` | ✅ Modified | Added OTP routes |
| `app/config.py` | ✅ Modified | Added Mail config |
| `app/__init__.py` | ✅ Modified | Initialize Flask-Mail |
| `.env` | ✅ Modified | Added Gmail settings |

---

## ✅ Quick Checklist

Before testing, ensure:

- [ ] Flask-Mail installed: `pip install flask-mail`
- [ ] 2FA enabled on Gmail account
- [ ] App Password generated (16 characters)
- [ ] `.env` file updated with Gmail credentials
- [ ] No spaces in App Password
- [ ] Flask app restarted after config changes

---

## 🎯 Next Steps

1. **Test the registration flow:**
   ```bash
   python run.py
   # Visit: http://localhost:5000/auth/register
   ```

2. **Check email delivery:**
   - Check inbox and spam folder
   - Verify OTP code works
   - Test resend functionality

3. **Customize email template:**
   - Edit `app/services/otp_service.py`
   - Modify HTML in `send_otp_email()` method

4. **Monitor email usage:**
   - Check Gmail dashboard for sent emails
   - Monitor for any delivery issues

---

## 📞 Support

If you encounter issues:

1. Check Flask console for error messages
2. Enable `MAIL_DEBUG=true` in `.env`
3. Verify Gmail App Password is correct
4. Ensure 2FA is enabled on Google account
5. Check Gmail API quotas and limits

---

**Your OTP email verification is now ready!** 📧✨
