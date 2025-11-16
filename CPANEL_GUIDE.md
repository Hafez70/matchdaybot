# 🚀 cPanel Deployment - Complete Guide

## Your bot is now in ~/fifa-bot directory

### 📋 Quick Commands

```bash
# Check bot status
./status.sh

# Start bot
./start.sh

# Stop bot
./stop.sh

# Restart bot
./restart.sh

# View logs (live)
tail -f bot.log

# View keep-alive logs
tail -f keep_alive.log

# Check if running
ps aux | grep main.py
```

---

## ⚙️ Initial Setup (Do Once)

### 1. Create Virtual Environment

```bash
cd ~/fifa-bot

# Try this first
python3 -m venv --without-pip venv
source venv/bin/activate
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python get-pip.py

# If above fails, try:
python3 -m venv --system-site-packages venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Create config.env

```bash
# Copy example
cp env_example.txt config.env

# Edit and add your bot token
nano config.env
```

Add this line:
```
TELEGRAM_BOT_TOKEN=your_actual_bot_token_here
```

Save: `Ctrl+X`, then `Y`, then `Enter`

### 3. Make Scripts Executable

```bash
chmod +x *.sh
```

### 4. Start Bot

```bash
./start.sh
```

---

## 🔄 Setup Auto-Restart (Recommended)

### Add to cPanel Cron Jobs:

1. Go to cPanel → **Cron Jobs**
2. Add new cron job:

**Every 5 minutes:**
```
*/5 * * * * cd ~/fifa-bot && ./keep_alive.sh
```

This will:
- Check if bot is running every 5 minutes
- Restart automatically if crashed
- Log activities to `keep_alive.log`

---

## 📊 Monitoring

### Check Status
```bash
./status.sh
```

Shows:
- Running status
- Process ID
- Memory usage
- Last log entries

### View Logs

```bash
# Real-time logs
tail -f bot.log

# Last 50 lines
tail -50 bot.log

# Search for errors
grep -i error bot.log
```

---

## 🔄 Updating Bot

When you update code on GitHub:

```bash
cd ~/fifa-bot

# Stop bot
./stop.sh

# Pull updates
git pull

# Reinstall dependencies (if requirements.txt changed)
source venv/bin/activate
pip install -r requirements.txt

# Start bot
./start.sh
```

---

## 🐛 Troubleshooting

### Bot Won't Start

```bash
# Check logs
tail -50 bot.log

# Check Python version
python3 --version

# Check if config.env exists
cat config.env

# Test bot directly
source venv/bin/activate
python3 main.py
# Press Ctrl+C to stop
```

### Bot Keeps Stopping

```bash
# Check memory usage
./status.sh

# Check for errors
tail -100 bot.log

# Check keep_alive log
tail -50 keep_alive.log
```

### Can't Install Dependencies

```bash
# Remove venv and recreate
rm -rf venv

# Install to user space instead
pip3 install --user -r requirements.txt

# Update start.sh to use python3 directly (no venv)
```

---

## 🔒 Security

### Protect Sensitive Files

```bash
chmod 600 config.env
chmod 600 fifa_data.json
```

### If in public_html, add .htaccess

```bash
cat > .htaccess << 'EOF'
# Deny access to all files
<Files "*">
    Deny from all
</Files>

# Allow specific files if needed
<Files "index.html">
    Allow from all
</Files>
EOF
```

---

## 📱 Test Your Bot

1. Open Telegram
2. Send `/start` to your bot
3. Should respond with registration
4. Create a test league
5. Record a test match

---

## 🎯 File Structure

```
~/fifa-bot/
├── main.py              # Bot entry point
├── src/                 # Source code
├── config.env           # Your bot token (DO NOT SHARE)
├── fifa_data.json       # Bot database
├── bot.log              # Bot logs
├── bot.pid              # Process ID
├── keep_alive.log       # Monitor logs
├── venv/                # Virtual environment
├── start.sh             # Start bot
├── stop.sh              # Stop bot
├── restart.sh           # Restart bot
├── status.sh            # Check status
└── keep_alive.sh        # Monitor script
```

---

## 🆘 Common Issues

### "Permission denied"
```bash
chmod +x *.sh
```

### "config.env not found"
```bash
cp env_example.txt config.env
nano config.env
```

### "Module not found"
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### "Address already in use"
```bash
./stop.sh
./start.sh
```

---

## 📞 Need Help?

Check logs first:
```bash
tail -100 bot.log
```

Most issues are in the logs!

---

**Your bot should now be running! 🎉**

Test it by sending `/start` to your bot in Telegram.

