# 🚀 SQLite Deployment to cPanel - Step by Step

## 📋 Prerequisites

- [x] Code pushed to GitHub
- [x] SSH access to cPanel
- [x] Bot currently stopped (or will be stopped)

---

## 🔧 Deployment Steps

### **Step 1: Connect to cPanel**

```bash
ssh xqaebsls@nitro
```

---

### **Step 2: Navigate to Bot Directory**

```bash
cd ~/fifa-bot
```

---

### **Step 3: Stop the Bot**

```bash
./stop.sh
```

Expected output:
```
🛑 Stopping FIFA Match Tracker Bot...
Bot stopped successfully!
```

---

### **Step 4: Pull Latest Changes**

```bash
git pull origin main
```

Expected output:
```
Updating 44a8708..b427038
Fast-forward
 .gitignore                                |  10 +-
 SQLITE_IMPLEMENTATION.md                  | 235 +++++++
 SQLITE_MIGRATION.md                       | 243 +++++++
 main.py                                   |   4 +-
 migrate_to_sqlite.py                      | 117 ++++
 src/services/__init__.py                  |   3 +-
 src/services/sqlite_database_service.py   | 310 +++++++++
 7 files changed, 917 insertions(+), 5 deletions(-)
```

---

### **Step 5: Run Migration**

```bash
python3 migrate_to_sqlite.py
```

**Expected Output:**

```
🔄 Starting migration from JSON to SQLite...
==================================================
📦 Backup created: fifa_data.json.backup
📊 JSON data loaded:
   - Users: 15
   - Leagues: 3
   - Matches: 47

👥 Migrating users...
  ✓ Ali (ID: 123456)
  ✓ Sara (ID: 234567)
  ... (more users)
✅ Migrated 15 users

🏆 Migrating leagues...
  ✓ Office League (ABC123) - 8 members
  ✓ Friends League (XYZ789) - 7 members
✅ Migrated 3 leagues

⚽ Migrating matches...
  ... 10 matches migrated
  ... 20 matches migrated
  ... 30 matches migrated
  ... 40 matches migrated
✅ Migrated 47 matches

==================================================
📊 Migration Summary:
  ✅ Users: 15
  ✅ Leagues: 3
  ✅ Matches: 47

💾 SQLite database: fifa_bot.db
📦 JSON backup: fifa_data.json.backup

🎉 Migration completed successfully!
==================================================
```

---

### **Step 6: Verify Database Created**

```bash
ls -lh fifa_bot.db
```

Expected output:
```
-rw-r--r-- 1 xqaebsls xqaebsls 20K Nov 18 10:30 fifa_bot.db
```

---

### **Step 7: Start the Bot**

```bash
./start.sh
```

Expected output:
```
🚀 Starting FIFA Match Tracker Bot...
Activating virtual environment...
Starting bot in background...
✅ Bot started successfully!
Process ID: 12345
```

---

### **Step 8: Check Bot Status**

```bash
./status.sh
```

Expected output:
```
📊 FIFA Bot Status
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🟢 Bot is RUNNING
Process ID: 12345
Uptime: 0:01
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### **Step 9: Check Logs (Optional)**

```bash
tail -f bot.log
```

Expected output:
```
2025-11-18 10:30:15,123 - __main__ - INFO - Database initialized successfully
2025-11-18 10:30:15,234 - __main__ - INFO - Bot started successfully
2025-11-18 10:30:15,345 - __main__ - INFO - Listening for messages...
```

Press `Ctrl+C` to exit log view.

---

## ✅ Verification Checklist

Test the bot functionality:

### **1. Test Registration**
- [ ] Send `/start` to bot
- [ ] Verify welcome message appears
- [ ] Check if points are displayed correctly

### **2. Test League Operations**
- [ ] Create a new league
- [ ] Join existing league with code
- [ ] View league leaderboard
- [ ] Verify points and ranking

### **3. Test Match Recording**
- [ ] Select league
- [ ] Choose team 1 players (1 or 2)
- [ ] Choose team 2 players (1 or 2)
- [ ] Enter match results
- [ ] Add multiple results for same competition
- [ ] Finish competition
- [ ] Verify notifications sent to participants

### **4. Test Statistics**
- [ ] View personal stats
- [ ] Check leaderboard updates
- [ ] Verify points calculation (+1 win, -1 loss, 0 draw)

---

## 🔍 Troubleshooting

### **Issue: Migration fails with "JSON file not found"**

**Solution:** This is normal for fresh installations. The script will create an empty database.

```bash
python3 migrate_to_sqlite.py
# Output: "✅ Creating fresh SQLite database..."
```

---

### **Issue: "Database is locked"**

**Solution:** Bot is still running. Stop it first.

```bash
./stop.sh
pkill -f main.py  # Forcefully kill if needed
python3 migrate_to_sqlite.py
./start.sh
```

---

### **Issue: "Permission denied" on fifa_bot.db**

**Solution:** Fix file permissions.

```bash
chmod 644 fifa_bot.db
chmod 755 .
```

---

### **Issue: Bot starts but no messages received**

**Solution:** Check token and network.

```bash
# Verify token is loaded
python3 -c "from dotenv import load_dotenv; import os; load_dotenv('config.env'); print('Token:', os.getenv('TELEGRAM_BOT_TOKEN')[:20] + '...')"

# Check bot process
ps aux | grep main.py

# Check logs
tail -50 bot.log
```

---

## 📊 Database Inspection

### **View Database Contents:**

```bash
sqlite3 fifa_bot.db
```

Inside SQLite shell:

```sql
-- View all users
SELECT * FROM users;

-- View all leagues
SELECT * FROM leagues;

-- Count matches
SELECT COUNT(*) as total_matches FROM matches;

-- View leaderboard for league ABC123
SELECT 
    u.name,
    COUNT(m.id) as matches,
    SUM(CASE 
        WHEN (mp.team_number = 1 AND m.team1_score > m.team2_score) OR
             (mp.team_number = 2 AND m.team2_score > m.team1_score)
        THEN 1 
        WHEN m.team1_score = m.team2_score
        THEN 0
        ELSE -1 
    END) as points
FROM users u
JOIN match_players mp ON u.telegram_id = mp.telegram_id
JOIN matches m ON mp.match_id = m.id
WHERE m.league_code = 'ABC123'
GROUP BY u.telegram_id
ORDER BY points DESC;

-- Exit
.quit
```

---

## 📦 Backup Strategy

### **Manual Backup:**

```bash
# Create dated backup
cp fifa_bot.db ~/backups/fifa_bot_$(date +%Y%m%d_%H%M%S).db

# Or use SQLite backup command
sqlite3 fifa_bot.db ".backup ~/backups/fifa_bot_$(date +%Y%m%d_%H%M%S).db"
```

### **Automatic Backup (Recommended):**

Add to crontab:

```bash
crontab -e
```

Add this line:

```cron
# Backup database daily at 3 AM
0 3 * * * cd ~/fifa-bot && sqlite3 fifa_bot.db ".backup ~/backups/fifa_bot_$(date +\%Y\%m\%d).db"
```

---

## 🔄 Rollback (If Needed)

### **Restore from JSON backup:**

```bash
# Stop bot
./stop.sh

# Restore JSON file
cp fifa_data.json.backup fifa_data.json

# Update main.py to use JSON
nano main.py
# Change: SQLiteDatabaseService → DatabaseService
# Change: 'fifa_bot.db' → 'fifa_data.json'

# Start bot
./start.sh
```

### **Restore from SQLite backup:**

```bash
# Stop bot
./stop.sh

# Restore database
cp ~/backups/fifa_bot_20251118.db fifa_bot.db

# Start bot
./start.sh
```

---

## 📈 Performance Monitoring

### **Check Database Size:**

```bash
ls -lh fifa_bot.db
```

### **Optimize Database:**

```bash
sqlite3 fifa_bot.db "VACUUM;"
```

Run this monthly to reclaim space and optimize performance.

---

## 🎉 Deployment Complete!

Your bot is now running with SQLite! 

**Key Benefits:**
- ⚡ Faster queries (especially leaderboards)
- 🔒 Data integrity with foreign keys
- 📦 Single file backup
- 🚀 Scalable to thousands of matches

**Next Steps:**
- Set up automatic backups
- Monitor bot performance
- Enjoy the speed improvements!

---

## 📞 Support

If you encounter any issues:

1. Check logs: `tail -f bot.log`
2. Check status: `./status.sh`
3. Review migration guide: `SQLITE_MIGRATION.md`
4. Review implementation guide: `SQLITE_IMPLEMENTATION.md`

**Remember:** Your JSON data is safely backed up in `fifa_data.json.backup`!

