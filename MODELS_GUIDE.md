# Models Guide: LLM Management for The Brain

Easily manage and download AI models from multiple providers without leaving the repo.

---

## Quick Start (Choose One)

### 🚀 Fast Setup (2 minutes)

```bash
# Run the interactive setup wizard
python setup_models.py

# Follow the prompts to choose a provider
# Done!
```

### 📚 View Available Models

```bash
# See all models in the catalog
python models_cli.py catalog

# Check provider status
python models_cli.py status
```

---

## Provider Options

### ⭐ Ollama (Recommended)

**Best for:** Unlimited free, local, private, fast

```bash
# 1. Download from https://ollama.ai
# 2. Start it
ollama serve

# 3. Download a model (first time only)
python models_cli.py download ollama mistral

# 4. The Brain auto-detects and uses it
python -m agent.core.agent
```

**Models:**
- `mistral` (4.1GB) - ⭐ Recommended
- `llama2` (3.8GB) - Good alternative
- `neural-chat` (4.1GB) - Very fast
- `zephyr` (4.1GB) - Best reasoning
- `orca-mini` (1.9GB) - For old devices

---

### 🚀 Groq (Free Tier)

**Best for:** Fast inference, 30 req/min free

```bash
# 1. Get free API key
# Visit: https://console.groq.com
# Sign up → Create API key → Copy

# 2. Set environment variable
export GROQ_API_KEY="gsk_..."

# 3. The Brain auto-detects and uses it
python -m agent.core.agent
```

**Models:**
- `mixtral-8x7b-32768` - ⭐ Recommended
- `llama2-70b-4096` - Larger, more capable
- `llama2-13b-chat` - Fast and capable

---

### 💡 Together AI (Free Tier)

```bash
# 1. Get API key
# Visit: https://www.together.ai → Sign up → Get key

# 2. Set environment variable
export TOGETHER_API_KEY="..."

# 3. Run The Brain
python -m agent.core.agent
```

---

### 📚 HuggingFace (Free Tier)

```bash
# 1. Get API token
# Visit: https://huggingface.co/settings/tokens

# 2. Set environment variable
export HF_API_KEY="hf_..."

# 3. Run The Brain
python -m agent.core.agent
```

---

## Commands

### View Status

```bash
python models_cli.py status
```

Shows which providers are installed/configured:
```
✅ Ollama: Download from https://ollama.ai
   Installed models: mistral, llama2
✅ GROQ: Set GROQ_API_KEY environment variable
⏳ TOGETHER: Set TOGETHER_API_KEY environment variable
⏳ HUGGINGFACE: Set HF_API_KEY environment variable
```

---

### View All Models

```bash
python models_cli.py catalog
```

Shows every available model across all providers with details.

---

### Get Model Info

```bash
python models_cli.py info ollama mistral
```

Shows detailed information about a specific model:
```
📦 Mistral 7B
============================================================
Description: Best balance of speed and quality for The Brain
Speed: Fast
Quality: High
Size: 4.1GB
```

---

### Download Models

```bash
# Download Ollama model
python models_cli.py download ollama mistral

# For cloud providers, see setup instructions
python models_cli.py info groq mixtral-8x7b-32768
```

---

### List Installed Models

```bash
python models_cli.py list
```

Shows what's currently installed on your system:
```
📚 Installed Ollama Models:
  • mistral
  • llama2
```

---

## Recommended Setups

### Setup 1: Local Only (Best Privacy)

```bash
# Install Ollama once
# From https://ollama.ai

# Download model
ollama pull mistral

# Start server
ollama serve

# In another terminal
python -m agent.core.agent
```

**Cost:** $0  
**Privacy:** Excellent (everything local)  
**Speed:** Very fast  
**Limit:** None (unlimited)

---

### Setup 2: Local + Cloud Fallback (Best Reliability)

```bash
# 1. Install Ollama
ollama serve  # Terminal 1

# 2. Set Groq key (for fallback)
export GROQ_API_KEY="gsk_..."

# 3. Download Ollama model
ollama pull mistral

# 4. Start The Brain
python -m agent.core.agent  # Terminal 2
```

**Cost:** $0  
**Privacy:** Good (Ollama local, Groq is fallback)  
**Speed:** Very fast  
**Limit:** Unlimited (Ollama) + 30 req/min (Groq)

---

### Setup 3: Cloud Only (No Installation)

```bash
# Set one API key (or multiple for fallback)
export GROQ_API_KEY="gsk_..."

# Start The Brain
python -m agent.core.agent
```

**Cost:** $0 (all free tiers)  
**Privacy:** Cloud-based  
**Speed:** Fast  
**Limit:** Depends on provider (30 req/min for Groq)

---

## Models by Device

### Windows (7-11)

**Recommended:** Ollama (local) + Groq fallback

```bash
# Download Ollama from https://ollama.ai
# Run installer
# Done!

python setup_models.py
```

---

### Linux

**Recommended:** Ollama

```bash
curl https://ollama.ai/install.sh | sh
ollama pull mistral
ollama serve
```

---

### macOS

**Recommended:** Ollama

```bash
# Download from https://ollama.ai
# Or install via Homebrew
brew install ollama
ollama pull mistral
```

---

### Termux (arrdee 64-bit & git 32-bit)

**Recommended:** Groq (Ollama not available on ARM)

```bash
export GROQ_API_KEY="gsk_..."
cd ~/claude-command-cli
python -m agent.core.agent
```

---

## Model Comparison

| Model | Speed | Quality | Size | Best For |
|-------|-------|---------|------|----------|
| Mistral 7B | ⚡ Fast | ⭐⭐⭐⭐ High | 4.1GB | ✅ General use |
| Llama 2 7B | ⚡ Fast | ⭐⭐⭐⭐ High | 3.8GB | Alternatives |
| Neural Chat 7B | ⚡⚡ Very Fast | ⭐⭐⭐ Good | 4.1GB | Quick responses |
| Zephyr 7B | ⚡ Fast | ⭐⭐⭐⭐⭐ Excellent | 4.1GB | Complex reasoning |
| Orca Mini 3B | ⚡⚡⚡ Lightning | ⭐⭐⭐ Good | 1.9GB | Old devices |
| Mixtral 8x7B | ⚡ Fast | ⭐⭐⭐⭐⭐ Excellent | Cloud | Best quality |

---

## Environment Variables

Set these to enable cloud providers:

```bash
# Groq (recommended)
export GROQ_API_KEY="gsk_..."

# Together AI
export TOGETHER_API_KEY="..."

# HuggingFace
export HF_API_KEY="hf_..."

# Linux/Mac: Add to ~/.bashrc or ~/.zshrc
# Windows: System Properties → Environment Variables

# Verify it's set
echo $GROQ_API_KEY  # Should print your key
```

---

## Troubleshooting

### "No AI provider available"

**Solution:** Install Ollama or set an API key

```bash
# Option 1: Install Ollama
python setup_models.py

# Option 2: Set API key
export GROQ_API_KEY="gsk_..."
```

---

### "Ollama connection refused"

**Solution:** Start Ollama first

```bash
# Terminal 1
ollama serve

# Terminal 2
python -m agent.core.agent
```

---

### "Model not found"

**Solution:** Download it first

```bash
python models_cli.py download ollama mistral
```

---

### "API key not working"

**Solution:** Verify environment variable

```bash
echo $GROQ_API_KEY

# If empty, set it
export GROQ_API_KEY="gsk_..."

# Restart Python/terminal and try again
```

---

## Multi-Device Network

**All devices use models from the repo:**

```
arrdee (64-bit)     → Groq (free tier)
git (32-bit)        → Groq (free tier)
Windows 10          → Ollama (local)

All share decisions → collective learning
```

**Setup:**
1. Install Ollama on Windows
2. Set GROQ_API_KEY on both Termux devices
3. Start The Brain on each
4. Watch them learn together! 🧠🧠🧠

---

## Next Steps

1. **Run setup wizard:** `python setup_models.py`
2. **Choose a provider** (Ollama recommended)
3. **Download a model** (`python models_cli.py download ollama mistral`)
4. **Start The Brain:** `python -m agent.core.agent`
5. **Watch it think!** 🚀

---

## Questions?

- **Provider comparison:** `python models_cli.py catalog`
- **Model details:** `python models_cli.py info <provider> <model>`
- **Installation help:** `python setup_models.py`

Happy thinking! 🧠
