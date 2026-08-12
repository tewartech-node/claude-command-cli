#!/bin/bash
# The Brain: Interactive Welcome Menu

show_status() {
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

    if pgrep -f "agent.core.agent" > /dev/null; then
        echo "✅ Brain: RUNNING (thinking every 5 minutes)"
        DECISIONS=$(sqlite3 ~/claude-command-cli/agent/storage/memory.db "SELECT COUNT(*) FROM decisions" 2>/dev/null || echo "0")
        echo "💡 Decisions made: $DECISIONS"
    else
        echo "⏸️  Brain: STOPPED"
    fi
}

show_menu() {
    cat << 'EOF'

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚀 QUICK COMMANDS (select one)

  (1) View Brain Thoughts (live)
  (2) Check Recent Decisions
  (3) Start Brain
  (4) Stop Brain
  (5) View Full Log
  (6) Brain Status
  (7) Help / Documentation
  (0) Exit

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Your AI is thinking. Welcome to your future. 🚀

EOF
}

execute_command() {
    case $1 in
        1)
            echo ""
            echo "📖 Viewing Brain Thoughts (Ctrl+C to exit)..."
            sleep 1
            tail -f agent/storage/brain.log
            ;;
        2)
            echo ""
            echo "📋 Recent Decisions:"
            sqlite3 agent/storage/memory.db "SELECT * FROM decisions ORDER BY timestamp DESC LIMIT 5" 2>/dev/null || echo "No decisions yet"
            read -p "Press Enter to continue..."
            ;;
        3)
            echo ""
            echo "🚀 Starting Brain..."
            ./agent/start_brain.sh 0.0
            ;;
        4)
            echo ""
            echo "⏹️  Stopping Brain..."
            pkill -f agent.core.agent
            echo "Brain stopped."
            read -p "Press Enter to continue..."
            ;;
        5)
            echo ""
            echo "📄 Full Log (Ctrl+C to exit)..."
            sleep 1
            less agent/storage/brain.log
            ;;
        6)
            show_status
            read -p "Press Enter to continue..."
            ;;
        7)
            clear
            echo "📚 DOCUMENTATION"
            echo ""
            echo "Quick Start:  cat QUICK_START.txt"
            echo "Full Guide:   cat TERMUX_SETUP.md"
            echo "Architecture: cat CLAUDE.md"
            echo ""
            read -p "Press Enter to continue..."
            ;;
        0)
            echo "Goodbye! 🚀"
            exit 0
            ;;
        *)
            echo "Invalid option. Try again."
            read -p "Press Enter to continue..."
            ;;
    esac
}

# Main loop
while true; do
    show_status
    show_menu
    read -p "Select [0-7]: " choice
    execute_command "$choice"
done
