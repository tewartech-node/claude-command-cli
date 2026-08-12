# Multi-Device Network: The Brain Network

Connect multiple devices running The Brain into a unified intelligence network.

**Supported Devices:**
- Termux (ARM32, ARM64) - arrdee, git
- Windows (7, 8, 10, 11) - native or WSL
- Linux (any distro)
- macOS

---

## Architecture

```
┌─────────────────┐
│   Windows 10    │ (device: windows-laptop)
│   The Brain     │
└────────┬────────┘
         │ Memory Sync
         │ (shared decisions)
         │
    ┌────┴────┐
    │          │
┌───▼──┐  ┌───▼──┐
│arrdee│  │ git  │
│64-bit│  │32-bit│
└──────┘  └──────┘
 (Termux)  (Termux)

All Brains share:
- Decision history
- Learned patterns
- Success ratings
- Confidence scores
```

---

## Setup Instructions

### On Each Device

#### 1. Clone The Brain
```bash
git clone https://github.com/tewartech-node/claude-command-cli.git
cd claude-command-cli
```

#### 2. Windows Setup (7-11)
```powershell
# Install Python 3.8+
# https://www.python.org/downloads/

# Create virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install dependencies
pip install -e .
python -m agent.core.agent
```

#### 3. Linux Setup
```bash
# Install Python and pip
sudo apt-get install python3 python3-pip

# Install dependencies
pip3 install -e .
python3 -m agent.core.agent &
```

#### 4. Termux Setup (already done)
```bash
cd ~/claude-command-cli
./agent/start_brain.sh 0.0 &
bash agent/startup/welcome.sh
```

### 2. Register Devices in Network

On each device, edit `agent/config/devices.json`:

```json
{
  "this_device": {
    "device_id": "windows-laptop",
    "device_name": "My Windows 10 PC",
    "platform": "windows",
    "arch": "x86_64",
    "memory_path": "C:\\Users\\YourName\\claude-command-cli\\agent\\storage\\memory.db"
  },
  "network_peers": [
    {
      "device_id": "arrdee",
      "device_name": "Galaxy Tab (64-bit)",
      "platform": "termux",
      "arch": "arm64"
    },
    {
      "device_id": "git",
      "device_name": "Old Phone (32-bit)",
      "platform": "termux",
      "arch": "arm32"
    }
  ]
}
```

### 3. Enable Sync

Each device automatically syncs to others in the network every:
- 1 hour (automatic)
- On demand via menu option 9

---

## Free AI Providers (Pick One or More)

### Option 1: Ollama (Recommended - Unlimited Free)

**Cost:** $0  
**Limit:** Unlimited (runs local)  
**Setup:** 2 minutes

```bash
# Download from https://ollama.ai
# Linux:
curl https://ollama.ai/install.sh | sh
ollama serve

# Windows: Download installer from https://ollama.ai/download/windows

# Test:
ollama pull mistral
ollama run mistral "Hello"
```

**The Brain will auto-use Ollama if running:**
```bash
# Terminal 1: Start Ollama
ollama serve

# Terminal 2: Start The Brain
python -m agent.core.agent
```

---

### Option 2: Groq (Free Tier)

**Cost:** $0 (30 requests/minute free)  
**Limit:** 30 req/min (plenty for 5-min thinking loops)  
**Setup:** 5 minutes

1. Go to https://console.groq.com
2. Sign up (free)
3. Create API key
4. Set environment variable:

**Windows:**
```powershell
[System.Environment]::SetEnvironmentVariable("GROQ_API_KEY", "your-key-here", "User")
# Restart terminal
```

**Linux/Termux:**
```bash
echo 'export GROQ_API_KEY="your-key-here"' >> ~/.bashrc
source ~/.bashrc
```

---

### Option 3: Together AI (Free Tier)

**Cost:** $0  
**Limit:** Free tier available  
**Setup:** 5 minutes

1. Visit https://www.together.ai
2. Sign up (free)
3. Get API key
4. Set environment:

```bash
export TOGETHER_API_KEY="your-key-here"
```

---

### Option 4: HuggingFace (Free Tier)

**Cost:** $0 (limited rate)  
**Limit:** Free but rate-limited  
**Setup:** 5 minutes

1. Visit https://huggingface.co
2. Create account
3. Generate API token
4. Set environment:

```bash
export HF_API_KEY="your-token-here"
```

---

## Recommended Setup (Zero Cost, Maximum Power)

### Best Free Option: Ollama
- **Cost:** $0
- **Limit:** Unlimited (runs on your hardware)
- **Speed:** Fast (no network latency)
- **Privacy:** Everything stays local

```bash
# Install Ollama
# (one-time, works on Windows/Mac/Linux)

# Download smallest model
ollama pull mistral

# Start it
ollama serve

# The Brain will auto-detect and use it
```

### Backup: Groq (if Ollama unavailable)
- **Cost:** $0
- **Limit:** 30 req/min
- **Speed:** Very fast
- **Privacy:** Sent to Groq servers

---

## Checking Free Provider Status

On any device:
```bash
python -c "
from agent.executor.free_connectors import FreeAIConnectors
fc = FreeAIConnectors()
import json
print(json.dumps(fc.get_status(), indent=2))
"
```

Example output:
```json
{
  "ollama_available": true,
  "groq_available": false,
  "together_available": false,
  "huggingface_available": false,
  "providers_enabled": 1,
  "recommendation": "Ollama (local, unlimited free)"
}
```

---

## Network Sync

### Automatic Sync (Every Hour)
The Brain automatically syncs decisions across your network.

### Manual Sync
```bash
# On any device, from welcome menu
bash agent/startup/welcome.sh
# Select option 9: Sync Status
# Shows what's ready to share
```

### What Gets Synced
- ✅ All decisions
- ✅ User ratings (1-5 feedback)
- ✅ Learned patterns
- ✅ Confidence scores
- ✅ Device metadata

---

## Multi-Device Benefits

As your network grows:
1. **Faster Learning** - Decisions from one device inform all others
2. **Better Patterns** - More data = better pattern recognition
3. **Higher Confidence** - Collective history improves accuracy
4. **Redundancy** - If one device fails, others continue
5. **Distributed Intelligence** - Multiple devices thinking = exponential improvement

---

## Example Network Setup

**Your Network:**
- Windows 10 laptop (main): Ollama running locally
- arrdee (64-bit): Groq free tier as backup
- git (32-bit): Falls back to Groq if Ollama unavailable
- Windows 7 desktop (future): Shares memory with entire network

**Result:**
All devices learn from each collective decision, confidence improves continuously.

---

## Cost Breakdown

| Provider | Cost | Limit | Setup |
|----------|------|-------|-------|
| Ollama | $0 | Unlimited | 2 min |
| Groq | $0 | 30 req/min | 5 min |
| Together | $0 | Free tier | 5 min |
| HuggingFace | $0 | Rate limit | 5 min |
| **Total** | **$0** | **Sufficient** | **~10 min** |

---

## Troubleshooting

### "No AI provider available"
```bash
# Install Ollama or set API key
export GROQ_API_KEY="your-key"
# Then restart The Brain
```

### Network not syncing
```bash
# Check device registration
sqlite3 agent/storage/memory.db "SELECT * FROM devices;"

# Check sync status
bash agent/startup/welcome.sh
# Select option 9
```

### Device not appearing in network
```bash
# Re-register device
python -c "
from agent.core.device_registry import DeviceRegistry
dr = DeviceRegistry('agent/storage/memory.db')
dr.initialize()
dr.register_device('device-id', 'Device Name', 'windows', 'x86_64', 'path/to/memory.db')
"
```

---

## Next Steps

1. **Set up Ollama** (recommended)
2. **Register all your devices**
3. **Start all Brains**
4. **Wait 1 hour** for first sync
5. **Check analytics** (menu option 8) to see network growth

Welcome to multi-device AI! 🧠🧠🧠
