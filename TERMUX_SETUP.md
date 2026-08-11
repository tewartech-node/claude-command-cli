# The Brain: Termux Setup Guide
## Cross-Platform (32-bit & 64-bit Android)

### Device Requirements
- **Recommended**: Android 6.0+ with 2GB+ RAM
- **32-bit ARM**: Works on older phones (2013-2018)
- **64-bit ARM**: Works on modern phones (2018+)
- **Storage**: ~500MB free (CLI + Brain + Python)

---

## QUICK START (Copy & Paste All Commands)

### Step 1: Install Termux
```
Download from F-Droid (NOT Google Play):
https://f-droid.org/en/packages/com.termux/
```

### Step 2: Open Termux & Update System
```bash
pkg update && pkg upgrade -y
```

### Step 3: Install Dependencies
```bash
pkg install -y python git golang
```

**Verify installations:**
```bash
python3 --version
git --version
go version
```

### Step 4: Clone Repository
```bash
cd ~
git clone https://github.com/tewartech-node/claude-command-cli.git
cd claude-command-cli
git checkout claude/repo-push-bug-fixes-hxo19w
```

### Step 5: Build CLI for Your Architecture
#### For 64-bit ARM (most modern phones)
```bash
cd cli/go
go build -o bin/claude ./cmd/claude
cd ../..
ls -la cli/go/bin/claude
```

#### For 32-bit ARM (older phones)
```bash
cd cli/go
GOOS=linux GOARCH=arm go build -o bin/claude ./cmd/claude
cd ../..
ls -la cli/go/bin/claude
```

**Both should show a file ~16MB**

### Step 6: Install Python Termux Package (Not pip)
```bash
pkg install -y python-psutil
```

### Step 7: Install Python HTTP Library
```bash
pip install httpx
```

**Verify:**
```bash
python3 -c "import psutil; import httpx; print('✅ Ready')"
```

### Step 8: Start The Brain
```bash
./agent/start_brain.sh '?qwerty4claude2026?' 0.0
```

**Expected output:**
```
🧠 Starting The Brain
✅ Configuration:
   Gmail: warnet.dev01@gmail.com
   Password: ****** (hidden)
   Monthly Budget: $0.0
   CLI Path: ./cli/go/bin/claude

✅ All checks passed
🚀 Launching Brain...
```

Brain is now thinking every 5 minutes. First email comes in ~5 min.

---

## KEEP BRAIN RUNNING (Auto-Start on Reboot)

### Option A: Run in Background (Now)
```bash
nohup ./agent/start_brain.sh '?qwerty4claude2026?' 0.0 > ~/brain.log 2>&1 &
```

**Check if running:**
```bash
ps aux | grep agent
```

**View log:**
```bash
tail -f ~/brain.log
```

### Option B: Auto-Start on Phone Reboot
```bash
pkg install termux-boot
mkdir -p ~/.termux/boot
```

**Create auto-start script:**
```bash
cat > ~/.termux/boot/start_brain.sh << 'EOF'
#!/data/data/com.termux/files/usr/bin/bash
cd ~/claude-command-cli
nohup ./agent/start_brain.sh '?qwerty4claude2026?' 0.0 > ~/brain.log 2>&1 &
EOF

chmod +x ~/.termux/boot/start_brain.sh
```

**Enable Termux:Boot app** (install from F-Droid) → toggle notifications ON

Now Brain starts automatically when you reboot.

---

## MONITOR THE BRAIN

### From Termux Directly
```bash
# View live log
tail -f ~/brain.log

# Check process
ps aux | grep agent

# Stop Brain
pkill -f "agent.py"

# Restart
./agent/start_brain.sh '?qwerty4claude2026?' 0.0
```

### From Computer (SSH into Phone)
**On Termux phone:**
```bash
pkg install openssh
sshd
```

**On your computer:**
```bash
ssh -p 8022 user@localhost
# Inside SSH session:
cd ~/claude-command-cli
tail -f ~/brain.log
```

---

## COMMAND THE BRAIN VIA EMAIL

The Brain checks your email every 5 minutes for commands.

**Reply to any Brain email with:**
```
> yes, implement caching
> focus on optimization this week
> pause everything
> check disk usage
```

Brain reads the `>` lines and acts on them.

---

## TROUBLESHOOTING

### "CLI not found"
```bash
cd cli/go
go build -o bin/claude ./cmd/claude
cd ../..
./agent/start_brain.sh '?qwerty4claude2026?' 0.0
```

### "No module named psutil"
```bash
pkg install -y python-psutil
python3 -c "import psutil; print('✅ OK')"
```

### "No module named httpx"
```bash
pip install httpx
python3 -c "import httpx; print('✅ OK')"
```

### "Permission denied" on start_brain.sh
```bash
chmod +x agent/start_brain.sh
./agent/start_brain.sh '?qwerty4claude2026?' 0.0
```

### Brain won't send emails
1. Verify password in start_brain.sh matches your Gmail app password
2. Check internet connection: `ping google.com`
3. Check /root/.ccr/README.md for proxy issues

### Brain uses too much battery
- Run only when charging
- Reduce thinking interval (edit agent/core/agent.py line 116: change 300 to 600)
- Disable email checking (edit agent/core/agent.py line 113: comment out)

---

## PLATFORM-SPECIFIC NOTES

### 32-bit ARM (ARMv7/ARMv8 32-bit mode)
- Use: `GOOS=linux GOARCH=arm go build`
- psutil from Termux package works fine
- ~15% slower than 64-bit but fully functional
- Recommended for phones: Samsung Galaxy S5, LG G3, HTC One M8, etc.

### 64-bit ARM (ARMv8)
- Use: Default `go build` (detects 64-bit)
- psutil from Termux package works fine
- Full performance
- Recommended for phones: Pixel 2+, Galaxy S8+, OnePlus 5+, etc.

### Windows (if using WSL/Termux emulator)
```bash
GOOS=windows GOARCH=amd64 go build -o bin/claude.exe ./cmd/claude
```

---

## STORAGE LOCATION

All Brain data stored locally:
```
~/claude-command-cli/agent/storage/memory.db
```

3-month retention, 10% sample rate for efficiency.

---

## ADVANCED: Update Brain Code

When new features are released:
```bash
cd ~/claude-command-cli
git fetch origin
git pull origin claude/repo-push-bug-fixes-hxo19w

# Rebuild CLI if Go code changed
cd cli/go && go build -o bin/claude ./cmd/claude && cd ../..

# Restart Brain
pkill -f "agent.py"
./agent/start_brain.sh '?qwerty4claude2026?' 0.0
```

---

## NEXT: Link GitHub to Termux

After Brain is running successfully:

```bash
# Generate SSH key
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519 -N ""

# Copy public key
cat ~/.ssh/id_ed25519.pub
```

1. Go to GitHub.com → Settings → SSH Keys
2. Click "New SSH Key"
3. Paste the output from above
4. Name it "Termux Phone"

Now you can:
```bash
cd ~/claude-command-cli
git push -u origin claude/repo-push-bug-fixes-hxo19w
```

---

## SUPPORT

Issues? Check:
1. Internet: `ping 8.8.8.8`
2. Python: `python3 --version` (3.7+)
3. Go: `go version` (1.18+)
4. Logs: `tail -f ~/brain.log`
5. Process: `ps aux | grep agent`

For errors, attach output of:
```bash
./agent/start_brain.sh '?qwerty4claude2026?' 0.0 2>&1 | head -50
```

---

## Your Brain is Alive 🧠

You now have an autonomous AI system running on your Android phone that:
- ✅ Thinks every 5 minutes
- ✅ Learns from decisions
- ✅ Respects 3 safety rules
- ✅ Reports daily via email
- ✅ Takes commands via email reply
- ✅ Tracks costs and efficiency
- ✅ Works 32-bit and 64-bit

Welcome to your AI-powered future. 🚀
