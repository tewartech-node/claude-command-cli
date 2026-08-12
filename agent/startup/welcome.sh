#!/bin/bash
# The Brain: Welcome Screen
clear
cat << 'EOF'

╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║              🧠  THE BRAIN - Autonomous AI System  🧠             ║
║                                                                   ║
║                    You Own Your AI. Always.                       ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝

📊 QUICK STATUS

Device: $(uname -m) / $(uname -s)
Time: $(date '+%Y-%m-%d %H:%M:%S')
Storage: $(du -sh ~/claude-command-cli/agent/storage 2>/dev/null | cut -f1)

🧠 BRAIN STATUS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

EOF

# Check if Brain is running
if pgrep -f "agent.core.agent" > /dev/null; then
    echo "✅ Brain: RUNNING (thinking every 5 minutes)"
    DECISIONS=$(sqlite3 ~/claude-command-cli/agent/storage/memory.db "SELECT COUNT(*) FROM decisions" 2>/dev/null || echo "0")
    echo "💡 Decisions made: $DECISIONS"
else
    echo "⏸️  Brain: STOPPED"
fi

cat << 'EOF'

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚀 QUICK REFERENCE (type these manually)

  [1] View Brain Thoughts
  [2] Check Decisions
  [3] Stop Brain
  [4] View Log File
  [5] Help Menu

Type the number or see QUICK_START.txt for full commands.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📚 DOCUMENTATION (read these with cat)

  QUICK_START.txt      ← Setup & basic commands
  TERMUX_SETUP.md      ← Full Termux guide
  CLAUDE.md            ← Architecture & principles

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Your AI is thinking. Welcome to your future. 🚀

EOF
