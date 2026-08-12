# Termux Auto-Start & Welcome Screen Setup

## What This Does

- Shows custom welcome screen when you open Termux
- Displays Brain status automatically
- Quick command reference
- Auto-starts Brain on device reboot

---

## Setup (On Each Device)

### Step 1: Install Termux:Boot

```bash
pkg install termux-boot
```

### Step 2: Create Boot Script

```bash
mkdir -p ~/.termux/boot
cat > ~/.termux/boot/start_brain.sh << 'EOF'
#!/data/data/com.termux/files/usr/bin/bash
cd ~/claude-command-cli
sleep 5
nohup ./agent/start_brain.sh 0.0 > ~/brain.log 2>&1 &
EOF

chmod +x ~/.termux/boot/start_brain.sh
```

### Step 3: Install Termux:Boot App

1. Download **Termux:Boot** from F-Droid (not Google Play)
2. Open the app
3. Enable "Termux:Boot"
4. Turn on notifications

### Step 4: Set Up Welcome Screen

Add this to your `~/.bashrc`:

```bash
# Add to end of ~/.bashrc
if [ -d ~/claude-command-cli ]; then
    cd ~/claude-command-cli
    bash agent/startup/welcome.sh
fi
```

Or in one command:

```bash
echo "" >> ~/.bashrc
echo "# Brain Welcome Screen" >> ~/.bashrc
echo "if [ -d ~/claude-command-cli ]; then" >> ~/.bashrc
echo "    cd ~/claude-command-cli" >> ~/.bashrc
echo "    bash agent/startup/welcome.sh" >> ~/.bashrc
echo "fi" >> ~/.bashrc
```

### Step 5: Test

Reopen Termux. You should see:
- Welcome banner
- Brain status
- Quick commands

---

## What Happens Now

**On Device Reboot:**
1. Termux:Boot app wakes up
2. Runs `~/.termux/boot/start_brain.sh`
3. Waits 5 seconds (for system to stabilize)
4. Starts The Brain

**On Shell Open:**
1. Shows welcome screen
2. Displays current Brain status
3. Shows quick commands
4. You can immediately view logs or restart

---

## Quick Commands

```bash
# View welcome screen anytime
bash agent/startup/welcome.sh

# View Brain thoughts
tail -f agent/storage/brain.log

# Check if Brain is running
ps aux | grep agent

# Restart Brain
pkill -f agent.core.agent
./agent/start_brain.sh 0.0
```

---

## Troubleshooting

**Welcome screen not showing?**
```bash
# Manually add to bashrc
nano ~/.bashrc
# Add lines from Step 4
```

**Brain not auto-starting?**
```bash
# Check boot script
cat ~/.termux/boot/start_brain.sh

# Check if Termux:Boot app is enabled
# (Open Termux:Boot app → toggle should be ON)

# Check log
cat ~/brain.log
```

**Brain starts but crashes?**
```bash
tail ~/brain.log
# Look for error messages
# Common issues: missing files, permissions
```

---

Done! Your Brain now:
- ✅ Auto-starts on reboot
- ✅ Shows status on shell open
- ✅ Runs autonomously in background
- ✅ You can monitor anytime

Welcome to always-on AI. 🧠
