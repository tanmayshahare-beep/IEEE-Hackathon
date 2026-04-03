# 🦙 Ollama Setup for VillageCrop

## RTX 4060 Configuration

Your system is configured to use **Phi-3-mini**, the optimal model for RTX 4060 (8GB VRAM).

---

## ✅ Quick Start

### 1. Start Ollama Server
```bash
ollama serve
```

### 2. Verify Model is Installed
```bash
ollama list
```

You should see:
```
NAME       ID              SIZE      MODIFIED
phi3       <hash>          2.3 GB    <date>
```

### 3. Start VillageCrop
```bash
python run.py
```

---

## 🔧 Configuration Files

### `.env`
```env
OLLAMA_API_URL=http://localhost:11434/api/generate
OLLAMA_MODEL=phi3
```

### `app/config.py`
```python
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'phi3')  # RTX 4060 optimized
```

---

## 📊 Expected Performance

| Metric | Value |
|--------|-------|
| **Model Size** | 2.3 GB |
| **VRAM Usage** | ~2.5 GB |
| **Token Speed** | 50-80 tokens/sec |
| **4 Prompts Time** | ~15-25 seconds |

---

## 🧪 Test Ollama Connection

### Method 1: Command Line
```bash
ollama run phi3 "What is plant disease detection?"
```

### Method 2: Web UI
1. Start Flask app: `python run.py`
2. Login to VillageCrop
3. Upload a plant image
4. Go to "AI Answers" page
5. Click "Generate AI Answers"

### Method 3: API Status Check
```
GET http://localhost:11434/api/tags
```

---

## 🔄 Alternative Models

If you want to try other models:

```bash
# Very light (2B parameters, 1.5GB VRAM)
ollama pull gemma:2b
# Then update .env: OLLAMA_MODEL=gemma:2b

# Balanced (7B parameters, 4.5GB VRAM)
ollama pull mistral
# Then update .env: OLLAMA_MODEL=mistral

# Best quality (8B parameters, 5GB VRAM)
ollama pull llama3
# Then update .env: OLLAMA_MODEL=llama3
```

---

## ⚠️ Troubleshooting

### "model 'phi3' not found"
```bash
ollama pull phi3
```

### "Connection refused"
```bash
ollama serve
```

### Slow responses
- Close other GPU applications
- Reduce concurrent requests
- Try a smaller model: `ollama pull gemma:2b`

### Out of VRAM
- Check what's using VRAM: `nvidia-smi`
- Close GPU-intensive apps
- Use smaller model

---

## 🎯 AI Prompts Used

The system asks these 4 questions for each disease (optimized for concise, pointwise answers):

1. **"List key symptoms in bullet points"** - Specific, concise symptoms
2. **"Provide treatment as numbered steps"** - Actionable steps with product names
3. **"List prevention methods as bullet points"** - Practical measures
4. **"List environmental conditions as bullet points"** - Temperature, humidity, seasonal factors

**Output Format:**
- Bullet points (•) or numbered steps (1. 2. 3.)
- No paragraphs or introductions
- Short, actionable statements
- Specific details (product names, values, conditions)

Phi-3-mini excels at these agricultural Q&A tasks!

---

## 📝 Notes

- **First request** may be slow as the model loads into VRAM
- **Subsequent requests** will be much faster
- Model stays loaded for ~5 minutes after last use
- Ollama automatically unloads model when idle to free VRAM

---

**Enjoy AI-powered plant disease insights! 🌾🤖**
