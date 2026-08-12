# Containerized Brain Network with Email & Traffic Learning

Run The Brain as a full containerized network that learns from your email and web activity.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Docker Network                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐    │
│  │ Brain Core   │   │ Email        │   │ Traffic      │    │
│  │ (Thinking)   │←→→│ Monitor      │   │ Monitor      │    │
│  └──────────────┘   └──────────────┘   └──────────────┘    │
│         ↑                                                    │
│         │  Shared Data                                      │
│         ↓                                                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  SQLite Database (Memory + Learning)                 │   │
│  │  • Decisions  • Ratings  • Patterns                   │   │
│  │  • Email Activity  • Traffic Patterns  • Interests   │   │
│  └──────────────────────────────────────────────────────┘   │
│         ↑                                                    │
│         │                                                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Dashboard (Port 3000)                                │   │
│  │  Central visualization & control panel               │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  Supporting Services:                                        │
│  • Redis (network coordination)                              │
│  • PostgreSQL (metrics & analytics)                          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

### 1. Docker & Docker Compose

**Windows/Mac:**
- Download Docker Desktop: https://www.docker.com/products/docker-desktop

**Linux:**
```bash
sudo apt-get install docker.io docker-compose
sudo usermod -aG docker $USER
```

### 2. Gmail App Password

The Brain learns from your emails using a special app password (more secure than your main password).

**Get your Gmail App Password:**
1. Go to https://myaccount.google.com/security
2. Enable 2-Step Verification (if not already)
3. Go to App Passwords (at the bottom)
4. Select: Mail → Windows Computer (or your device)
5. Copy the 16-character password

---

## Setup (5 Minutes)

### Step 1: Clone and Configure

```bash
cd claude-command-cli

# Copy environment template
cp .env.example .env

# Edit with your details
nano .env
# OR on Windows
notepad .env
```

### Step 2: Set Your Email and API Keys

Edit `.env`:

```env
# Your Gmail
GMAIL_USER=jasoensyd26@gmail.com
GMAIL_APP_PASSWORD=your-16-char-app-password

# Groq (free tier, recommended)
GROQ_API_KEY=gsk_...

# Optional: Other providers
TOGETHER_API_KEY=...
HF_API_KEY=hf_...
```

### Step 3: Start the Network

```bash
# Build and start all containers
docker-compose up -d

# View logs
docker-compose logs -f

# Check status
docker-compose ps
```

**Done!** Your Brain network is running.

---

## Access the Dashboard

Open your browser to:

```
http://localhost:3000
```

You'll see:
- Brain thinking status
- Email activity analysis
- Web interests detected
- Decision quality metrics
- Network device status
- Learning progress

---

## What's Running

### 🧠 Brain Coordinator (Port 8000)
- Main thinking loop (5-min cycles)
- Memory management
- Decision making
- Confidence scoring

### 📧 Email Monitor
- Checks Gmail every 5 minutes
- Learns your communication patterns
- Identifies important contacts
- Categorizes messages

### 🌐 Traffic Monitor
- Analyzes browsing patterns
- Detects interests
- Categories websites
- Learns your habits

### 📊 Dashboard (Port 3000)
- Real-time visualization
- Network status
- Performance metrics
- Learning progress

### 🗄️ Supporting Services
- **Redis**: Network coordination
- **PostgreSQL**: Metrics storage

---

## Email Learning Details

The Brain learns:

1. **Communication Patterns**
   - Who you email most
   - Response times
   - Time of day patterns

2. **Interests**
   - Keywords in emails
   - Categories (work, personal, etc.)
   - Urgency levels

3. **Contacts**
   - Important senders
   - Frequency
   - Relationship strength

**Privacy Note:** All email data is stored locally in your Docker containers. Nothing is sent to external services.

---

## Traffic Analysis Details

The Brain learns:

1. **Browsing Habits**
   - Most visited sites
   - Time spent per domain
   - Peak activity times

2. **Interests**
   - Technology
   - Learning & Development
   - Business & Productivity
   - Entertainment & News

3. **Patterns**
   - What you do daily
   - Weekly habits
   - Interest trends

**Privacy Note:** Traffic data is also stored locally.

---

## Commands

### Start the Network
```bash
docker-compose up -d
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f brain-coordinator
docker-compose logs -f email-monitor
docker-compose logs -f traffic-monitor
docker-compose logs -f dashboard
```

### Stop the Network
```bash
docker-compose down
```

### Stop and Remove Everything
```bash
docker-compose down -v  # -v removes volumes too
```

### Rebuild Containers
```bash
docker-compose build
docker-compose up -d
```

### Check Database
```bash
# Enter SQLite shell
docker exec -it brain-coordinator sqlite3 /app/agent/storage/memory.db

# Query decisions
> SELECT COUNT(*) FROM decisions;

# Query email activity
> SELECT COUNT(*) FROM email_activity;
```

---

## Viewing Data

### Dashboard (Best Way)
```
http://localhost:3000
```

### Command Line

```bash
# Enter container
docker exec -it brain-coordinator bash

# Check decisions
python -c "
from agent.models import ModelManager
mm = ModelManager()
mm.print_status()
"

# View stats
python -c "
import sqlite3
conn = sqlite3.connect('agent/storage/memory.db')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM decisions')
print('Total decisions:', cursor.fetchone()[0])
cursor.execute('SELECT COUNT(*) FROM email_activity')
print('Emails analyzed:', cursor.fetchone()[0])
conn.close()
"
```

---

## Extending the Network

### Add More Containers

Want to run additional Brains on different devices?

**On another Linux/Windows/Mac machine:**

```bash
git clone https://github.com/tewartech-node/claude-command-cli.git
cd claude-command-cli

# Copy environment
cp .env.example .env

# Set unique device name
nano .env
# Change: DEVICE_ID=coordinator-main
# To: DEVICE_ID=brain-device-2

# Start
docker-compose up -d
```

**Network Sync:**
Devices on the same network automatically sync decisions via Redis.

---

## Troubleshooting

### "Gmail connection failed"

**Solution:** Verify your app password

```bash
# Check credentials in container
docker exec brain-coordinator cat /app/.env | grep GMAIL

# Should show your app password (16 characters)
```

### "Email Monitor not finding emails"

**Solution:** Check Gmail authentication

1. Verify GMAIL_APP_PASSWORD is 16 characters
2. Check Gmail security settings
3. View logs: `docker-compose logs -f email-monitor`

### "Dashboard not loading"

**Solution:** Check dashboard service

```bash
docker-compose logs -f dashboard

# Restart
docker-compose restart dashboard
```

### "Out of disk space"

**Solution:** Clean old data

```bash
# See what's using space
docker system df

# Remove unused containers/images
docker system prune

# If needed, remove volumes (clears all data)
docker-compose down -v
```

---

## Monitoring in Production

### Health Check

```bash
# Is everything running?
docker-compose ps

# Should show all containers as "Up"
```

### Resource Usage

```bash
# Check CPU and memory
docker stats

# Monitor specific container
docker stats brain-coordinator
```

### Logs

```bash
# Follow logs in real-time
docker-compose logs -f

# See last 100 lines
docker-compose logs --tail=100

# Save logs to file
docker-compose logs > brain-network.log
```

---

## Data Persistence

All data is stored in Docker volumes:

```
brain-coordinator-storage   ← Main Brain database
redis-storage               ← Cache
postgres-storage            ← Metrics
```

These persist even if containers stop. To keep data:
- **Never** use `docker-compose down -v`
- Use `docker-compose down` (without -v)

---

## Security Notes

### ✅ Good Practices

- App passwords are safer than main Gmail password
- All data stays in Docker (local)
- No external connections for personal data
- Containers run as non-root

### ⚠️ Important

- Keep `.env` file secure (add to `.gitignore`)
- Don't commit `.env` to GitHub
- Use strong DB_PASSWORD in production
- Regular backups of volume data

---

## Next Steps

1. **Start the network:** `docker-compose up -d`
2. **Check dashboard:** http://localhost:3000
3. **Wait 5 minutes** for first email check
4. **Watch** as The Brain learns your patterns
5. **Rate decisions** (in The Brain menu) to improve learning

---

## What The Brain Learns Over Time

**Week 1:**
- Your email frequency
- Most active times
- Main contacts

**Week 2:**
- Communication preferences
- Interest categories
- Browsing patterns

**Week 3:**
- Predictable decisions
- Confidence in patterns
- Behavioral trends

**Week 4+:**
- Optimization opportunities
- Productivity patterns
- Interest evolution

---

## Connect More Devices

The real power comes from multiple devices learning together.

**On your phone (Termux):**
```bash
# Set network to communicate with Docker Brain
export BRAIN_COORDINATOR_URL=http://your-laptop-ip:8000
./agent/start_brain.sh 0.0 &
```

**Result:** arrdee + git + Docker network = superpower 🧠🧠🧠

---

## Questions?

Check the logs for details:
```bash
docker-compose logs -f [service-name]
```

Supported services:
- `brain-coordinator`
- `email-monitor`
- `traffic-monitor`
- `dashboard`
- `redis`
- `postgres`

Happy learning! 🚀
