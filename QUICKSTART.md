# 🚀 VillageCrop - Quick Start Guide

## ✅ MongoDB Status

Your MongoDB database is **initialized and ready**:

```
Database: villagecrop
Collections:
  - users (1 document - test user)
  - predictions (0 documents)
```

## 📝 Test Credentials

A test user has been created for you:
- **Username**: `testuser`
- **Password**: `test123`

## 🎯 Starting the Application

### Option 1: Using the Batch File (Easiest)

Double-click `start_servers.bat` in the project root.

This will:
- Start Flask app on `http://localhost:5000`
- Start Ollama server on `http://localhost:3000`
- Open browser automatically

### Option 2: Manual Start

**Terminal 1 - Flask App:**
```bash
cd "C:\All projects\VILLAGECROP\web_app"
C:\Users\tamar\anaconda3\python.exe app.py
```

**Terminal 2 - Ollama Server:**
```bash
cd "C:\All projects\VILLAGECROP\Ollama-integration"
npm start
```

**Terminal 3 - Ollama (if not running):**
```bash
ollama serve
```

## 🧪 Testing the Complete Flow

1. **Open browser** to `http://localhost:5000`

2. **Login** with test credentials:
   - Username: `testuser`
   - Password: `test123`

3. **Upload an image**:
   - Click "Disease Detection" in navigation
   - Upload a plant leaf image
   - Click "Analyze Image"
   - View prediction results

4. **View AI answers**:
   - Click "AI Answers" in navigation
   - Click "Generate AI Answers"
   - Wait for Ollama to process (may take 1-2 minutes)
   - View expert insights

5. **View history**:
   - Click "My Predictions" in navigation
   - See all your past predictions

## 📊 MongoDB Verification

To verify data is being stored:

```bash
cd "C:\All projects\VILLAGECROP"
C:\Users\tamar\anaconda3\python.exe init_mongodb.py
```

This shows:
- Number of users
- Number of predictions
- Database collections

## 🔧 Troubleshooting

### MongoDB Not Found
```bash
net start MongoDB
```

### Port 5000 Already in Use
```bash
# Change port in web_app/app.py last line:
app.run(debug=True, host='0.0.0.0', port=5001)
```

### Ollama Not Responding
```bash
# Check Ollama is running
ollama list

# Install llama3.2 if not present
ollama pull llama3.2
```

### Module Not Found Errors
```bash
cd "C:\All projects\VILLAGECROP\web_app"
C:\Users\tamar\anaconda3\python.exe -m pip install -r requirements.txt
```

## 📁 Project Structure

```
VILLAGECROP/
├── web_app/                    # Flask application
│   ├── app.py                 # Main Flask app
│   ├── image_processor.py     # CNN & blur detection
│   ├── templates/             # HTML templates
│   ├── static/                # CSS/JS files
│   ├── .env                   # Environment variables
│   └── requirements.txt       # Python dependencies
├── Ollama-integration/         # Ollama server
│   ├── server.js              # Node.js server
│   └── public/index.html      # Ollama web interface
├── best_model.pth             # Trained CNN model
├── init_mongodb.py            # Database initialization
├── start_servers.bat          # Windows startup script
└── MONGODB_SETUP.md           # Detailed documentation
```

## 🎉 You're Ready!

Your MongoDB database is configured and the application is ready to use.

**Next Steps:**
1. Start the servers using `start_servers.bat`
2. Login at `http://localhost:5000`
3. Upload a plant image
4. Get AI-powered disease analysis!

---

**Need more help?** See `MONGODB_SETUP.md` and `INTEGRATION_SUMMARY.md` for detailed documentation.
