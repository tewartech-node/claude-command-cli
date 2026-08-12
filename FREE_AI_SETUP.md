# Free AI Providers for The Brain

Run your entire AI network **completely free** with multiple provider options.

---

## Quick Start (Pick One - Takes 5 Minutes)

### ⭐ BEST: Ollama (Unlimited Free, Local)

**Install once, use everywhere**

```bash
# Download from https://ollama.ai
# (Supports Windows, Mac, Linux)

# Start Ollama
ollama serve

# In another terminal, pull a model (first time only)
ollama pull mistral  # ~4GB download

# The Brain auto-detects and uses it
python -m agent.core.agent
```

**Why it's best:**
- ✅ Unlimited free usage
- ✅ Works offline
- ✅ No API key needed
- ✅ Fast (runs local)
- ✅ Private (no data sent anywhere)

---

### 🚀 FAST: Groq (Free Tier - 30 req/min)

Perfect for The Brain's 5-minute thinking cycle.

```bash
# 1. Visit https://console.groq.com
# 2. Sign up (free account, takes 2 min)
# 3. Create API key
# 4. Set environment variable:

# Windows (PowerShell):
[System.Environment]::SetEnvironmentVariable("GROQ_API_KEY", "gsk_your_key_here", "User")
# Then restart terminal and Python

# Linux/Mac/Termux:
echo 'export GROQ_API_KEY="gsk_your_key_here"' >> ~/.bashrc
source ~/.bashrc

# Test it
python -m agent.core.agent
```

**Why Groq:**
- ✅ Completely free
- ✅ Very fast (optimized inference)
- ✅ 30 req/min = enough for 288 thinking loops/day
- ✅ No payment info needed
- ✅ Instant setup

---

### 💡 Alternative: Together AI (Free Tier)

```bash
# 1. Visit https://www.together.ai
# 2. Sign up (free)
# 3. Get API key
# 4. Set environment:

export TOGETHER_API_KEY="your_key_here"

python -m agent.core.agent
```

---

### 📚 Alternative: HuggingFace (Free Tier)

```bash
# 1. Visit https://huggingface.co
# 2. Create account
# 3. Generate API token
# 4. Set environment:

export HF_API_KEY="hf_your_token"

python -m agent.core.agent
```

---

## Multi-Device Network (All Free)

### Setup for Windows + Termux

**On Windows:**
```bash
# Install Ollama from https://ollama.ai
ollama serve
```

**On arrdee (64-bit Termux):**
```bash
# Set Groq as fallback (if Ollama unavailable)
export GROQ_API_KEY="your_key"
cd ~/claude-command-cli
./agent/start_brain.sh 0.0 &
```

**On git (32-bit Termux):**
```bash
export GROQ_API_KEY="your_key"
cd ~/claude-command-cli
./agent/start_brain.sh 0.0 &
```

**Result:** Your network has local AI (Windows) + fallback (both phones)

---

## Fallback Chain (Auto-Tries in Order)

The Brain automatically tries providers in this order:
1. **Ollama** (if running locally) ← Best
2. **Groq** (if API key set) ← Fast
3. **Together** (if API key set)
4. **HuggingFace** (if API key set)
5. **Error** (if none available)

So you can have multiple set up, and it uses what's available.

---

## Cost Comparison

| Provider | Cost | Limit | Setup Time |
|----------|------|-------|-----------|
| Ollama | $0 | Unlimited | 5 min |
| Groq | $0 | 30 req/min | 2 min |
| Together | $0 | Free tier | 3 min |
| HF | $0 | Rate limited | 3 min |
| Claude API | Paid | Depends | 2 min |
| GPT-4 API | Paid | Depends | 2 min |

**Recommendation:** Use **Ollama + Groq** for free, reliable network.

---

## Example Network (Zero Cost)

```
┌──────────────────┐
│   Windows 10     │
│ Ollama (local)   │ ← Unlimited free
│ The Brain #1     │
└─────────┬────────┘
          │ Memory Sync
          │
    ┌─────┴────┐
    │          │
┌───▼─────┐  ┌─▼────────┐
│  arrdee  │  │   git    │
│Groq Free │  │Groq Free │
│The Brain │  │The Brain │
│   #2     │  │   #3     │
└──────────┘  └──────────┘

Cost: $0/month
AI Capability: Excellent
Speed: Fast (local + cloud)
Privacy: Good (Ollama local, Groq encrypted)
```

---

## Checking Your Setup

```bash
# See which providers are available
python -c "
from agent.executor.free_connectors import FreeAIConnectors
import json
fc = FreeAIConnectors()
print(json.dumps(fc.get_status(), indent=2))
"
```

Example output:
```json
{
  "ollama_available": true,
  "groq_available": true,
  "together_available": false,
  "huggingface_available": false,
  "providers_enabled": 2,
  "recommendation": "Ollama (local, unlimited free)"
}
```

---

## Troubleshooting

### "No AI provider available"
**Solution:** Install Ollama OR set a free API key

```bash
# Option 1: Install Ollama (recommended)
# https://ollama.ai

# Option 2: Set Groq free key
export GROQ_API_KEY="gsk_..."
```

### "GROQ_API_KEY not found"
**Solution:** Set environment variable properly

```bash
# Linux/Mac/Termux
echo 'export GROQ_API_KEY="gsk_..."' >> ~/.bashrc
source ~/.bashrc
echo $GROQ_API_KEY  # Should print your key

# Windows (PowerShell)
[System.Environment]::SetEnvironmentVariable("GROQ_API_KEY", "gsk_...", "User")
# Restart terminal
echo $env:GROQ_API_KEY
```

### "Ollama connection refused"
**Solution:** Start Ollama server first

```bash
# Terminal 1
ollama serve

# Terminal 2 (in another terminal)
python -m agent.core.agent
```

---

## Getting API Keys (All Free, Takes 5 Minutes)

### Groq Free Key
1. Go to https://console.groq.com
2. Click "Sign In" (or "Sign Up")
3. Create account (free)
4. Click "API Keys" in left menu
5. Click "Create API Key"
6. Copy it

### Together Free Key
1. Go to https://www.together.ai
2. Sign up (free)
3. Go to API page
4. Copy API key

### HuggingFace Free Key
1. Go to https://huggingface.co
2. Click "Sign up"
3. Verify email
4. Go to Settings → Access Tokens
5. Create new token (read)
6. Copy it

---

## Best Practices

### For Maximum Uptime
Use **Ollama + Groq**:
- Ollama is primary (local, always available)
- Groq is fallback (if Ollama down)
- Zero cost, never fails

### For Maximum Speed
Use **Groq**:
- Specialized hardware (very fast inference)
- Perfect for 5-minute thinking loops
- Free tier sufficient

### For Maximum Privacy
Use **Ollama**:
- Everything stays on your device
- No data leaves your network
- Perfect for sensitive decisions

---

## Starting Fresh Network (Windows + 2 Termux)

### Step 1: Install Ollama
```powershell
# Download from https://ollama.ai/download/windows
# Run installer
# Done!
```

### Step 2: Get Groq Key (5 min)
- Visit https://console.groq.com
- Sign up
- Create API key
- Copy it

### Step 3: On Each Device
```bash
# Linux/Termux:
export GROQ_API_KEY="your_key"
export OLLAMA_HOST="http://192.168.1.100:11434"  # Windows IP
python -m agent.core.agent &

# Or on Windows:
ollama serve
python -m agent.core.agent &
```

### Step 4: Run
All your Brains now think for free! 🧠

---

**Total setup time: 15 minutes**  
**Total cost: $0**  
**Total capability: Unlimited**

Welcome to free AI networks! 🚀
