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
  (7) Rate a Decision
  (8) View Analytics
  (9) Sync Status
  (10) Help / Documentation
  (0) Exit

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Your AI is thinking. Welcome to your future. 🚀

EOF
}

show_analytics() {
    echo ""
    echo "📊 BRAIN ANALYTICS"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # Overall stats
    echo ""
    echo "Overall Performance:"
    sqlite3 agent/storage/memory.db "
        SELECT
            COUNT(*) as total_decisions,
            SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful,
            ROUND(SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as success_rate
        FROM decisions
    " 2>/dev/null | awk -F'|' '{print "  Total Decisions: " $1; print "  Successful: " $2; print "  Success Rate: " $3 "%"}'

    # Top performing decisions
    echo ""
    echo "Top Performing Decision Types:"
    sqlite3 agent/storage/memory.db "
        SELECT
            d.decision_name,
            COUNT(*) as uses,
            ROUND(AVG(CASE WHEN r.rating IS NOT NULL THEN r.rating ELSE 0 END), 1) as avg_rating
        FROM decisions d
        LEFT JOIN ratings r ON d.id = r.decision_id
        GROUP BY d.decision_name
        ORDER BY avg_rating DESC
        LIMIT 5
    " 2>/dev/null | while IFS='|' read name uses rating; do
        echo "  • $name (used $uses times, avg rating: $rating/5)"
    done

    # Feedback coverage
    echo ""
    echo "Feedback Coverage:"
    sqlite3 agent/storage/memory.db "
        SELECT
            COUNT(*) as total,
            COUNT(DISTINCT decision_id) as rated
        FROM decisions d
        LEFT JOIN ratings r ON d.id = r.decision_id
    " 2>/dev/null | awk -F'|' '{rated=$2; total=$1; pct=(rated*100/total); print "  Rated Decisions: " rated "/" total " (" int(pct) "%)"}'

    read -p "Press Enter to continue..."
}

show_sync_status() {
    echo ""
    echo "🔄 SYNC STATUS"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    echo ""
    echo "Local Database:"
    sqlite3 agent/storage/memory.db "
        SELECT
            COUNT(*) as decisions,
            (SELECT COUNT(*) FROM ratings) as ratings,
            (SELECT COUNT(*) FROM patterns) as patterns
        FROM decisions
    " 2>/dev/null | awk -F'|' '{print "  Decisions: " $1; print "  Ratings: " $2; print "  Patterns: " $3}'

    echo ""
    echo "Export available for sync:"
    echo "  Run: python -c \"from agent.core.sync import MemorySync; s = MemorySync('agent/storage/memory.db', '$(uname -n)'); print('Decisions:', len(s.export_decisions())); print('Ratings:', len(s.export_ratings())); print('Patterns:', len(s.export_patterns()))\""

    read -p "Press Enter to continue..."
}

rate_decision() {
    echo ""
    echo "⭐ RATE A DECISION"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # Get unrated decisions
    UNRATED=$(sqlite3 agent/storage/memory.db "
        SELECT d.id, d.decision_name, d.timestamp
        FROM decisions d
        LEFT JOIN ratings r ON d.id = r.decision_id
        WHERE r.id IS NULL
        ORDER BY d.timestamp DESC
        LIMIT 1
    " 2>/dev/null)

    if [ -z "$UNRATED" ]; then
        echo "✅ All decisions have been rated!"
        read -p "Press Enter to continue..."
        return
    fi

    # Parse the unrated decision
    ID=$(echo "$UNRATED" | cut -d'|' -f1)
    NAME=$(echo "$UNRATED" | cut -d'|' -f2)
    TIMESTAMP=$(echo "$UNRATED" | cut -d'|' -f3)

    echo "Decision: $NAME"
    echo "Made at: $TIMESTAMP"
    echo ""
    echo "Rate this decision (1-5):"
    echo "  1 = Poor (bad outcome)"
    echo "  2 = Below Average"
    echo "  3 = Average"
    echo "  4 = Good (positive)"
    echo "  5 = Excellent (very positive)"
    echo ""
    read -p "Your rating (1-5): " rating

    # Validate rating
    if ! [[ "$rating" =~ ^[1-5]$ ]]; then
        echo "❌ Invalid rating. Must be 1-5."
        read -p "Press Enter to continue..."
        return
    fi

    # Optional feedback
    read -p "Brief feedback (optional, press Enter to skip): " feedback

    # Store rating in database
    if [ -z "$feedback" ]; then
        sqlite3 agent/storage/memory.db "
            INSERT INTO ratings (decision_id, rating, feedback, rated_at)
            VALUES ($ID, $rating, '', datetime('now'))
        " 2>/dev/null
    else
        sqlite3 agent/storage/memory.db "
            INSERT INTO ratings (decision_id, rating, feedback, rated_at)
            VALUES ($ID, $rating, '$feedback', datetime('now'))
        " 2>/dev/null
    fi

    echo "✅ Rating saved!"
    read -p "Press Enter to continue..."
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
            rate_decision
            ;;
        8)
            show_analytics
            ;;
        9)
            show_sync_status
            ;;
        10)
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
    read -p "Select [0-10]: " choice
    execute_command "$choice"
done
