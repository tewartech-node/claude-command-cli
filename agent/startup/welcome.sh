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
🚀 QUICK COMMANDS

  Start Brain:
    ./agent/start_brain.sh 0.0

  View Brain Thoughts:
    tail -f agent/storage/brain.log

  Check Decisions:
    sqlite3 agent/storage/memory.db "SELECT * FROM decisions LIMIT 5"

  Stop Brain:
    pkill -f agent.core.agent

  Push to GitHub:
    git add . && git commit -m "message" && git push

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📚 DOCUMENTATION

  Setup Guide:         cat QUICK_START.txt
  Full Guide:          cat TERMUX_SETUP.md
  Architecture:        cat CLAUDE.md

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Your AI is thinking. Welcome to your future. 🚀

EOF
