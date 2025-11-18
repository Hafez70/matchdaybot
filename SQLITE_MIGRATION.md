# 🔄 SQLite Database Migration Guide

## Overview

The bot now uses **SQLite** instead of JSON for data storage. SQLite provides better performance, data integrity, and query capabilities.

---

## 📊 Database Schema

### **Tables:**

1. **`users`** - User information
2. **`leagues`** - League details
3. **`league_members`** - Many-to-many relationship between users and leagues
4. **`matches`** - Match records
5. **`match_players`** - Many-to-many relationship between matches and players

### **Benefits:**
- ✅ **Faster queries** with indexes
- ✅ **Data integrity** with foreign keys
- ✅ **ACID transactions** (no data corruption)
- ✅ **Scalability** for thousands of matches
- ✅ **Easy backup** (single `.db` file)

---

## 🚀 Migration Process

### **1. Automatic Migration (Recommended)**

Run the migration script:

```bash
python migrate_to_sqlite.py
```

This will:
- ✅ Create backup: `fifa_data.json.backup`
- ✅ Create SQLite database: `fifa_bot.db`
- ✅ Migrate all users, leagues, and matches
- ✅ Show detailed migration summary

**Example Output:**
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

### **2. Fresh Installation**

If you don't have existing data:

```bash
# Just start the bot - database will be created automatically
python main.py
```

---

## 🔍 Database Inspection

### **Using SQLite CLI:**

```bash
# Open database
sqlite3 fifa_bot.db

# View schema
.schema

# View users
SELECT * FROM users;

# View leagues
SELECT * FROM leagues;

# View leaderboard
SELECT 
    u.name,
    COUNT(m.id) as matches,
    SUM(CASE 
        WHEN (mp.team_number = 1 AND m.team1_score > m.team2_score) OR
             (mp.team_number = 2 AND m.team2_score > m.team1_score)
        THEN 1 ELSE -1 
    END) as points
FROM users u
JOIN match_players mp ON u.telegram_id = mp.telegram_id
JOIN matches m ON mp.match_id = m.id
WHERE m.league_code = 'ABC123'
GROUP BY u.telegram_id
ORDER BY points DESC;

# Exit
.quit
```

---

## 📦 Backup & Restore

### **Backup Database:**

```bash
# Simple copy
cp fifa_bot.db fifa_bot_backup_$(date +%Y%m%d).db

# Or use SQLite backup
sqlite3 fifa_bot.db ".backup fifa_bot_backup.db"
```

### **Restore Database:**

```bash
cp fifa_bot_backup.db fifa_bot.db
```

---

## 🔧 Troubleshooting

### **Migration Failed:**

1. Check if `fifa_data.json` exists
2. Check file permissions
3. Check disk space
4. Review error messages

### **Database Locked:**

```bash
# Stop the bot
./stop.sh

# Run migration
python migrate_to_sqlite.py

# Start the bot
./start.sh
```

### **Corrupt Database:**

```bash
# Check integrity
sqlite3 fifa_bot.db "PRAGMA integrity_check;"

# If corrupt, restore from backup
cp fifa_bot_backup.db fifa_bot.db
```

---

## 📝 Database Maintenance

### **Optimize Database:**

```bash
sqlite3 fifa_bot.db "VACUUM;"
```

### **Check Database Size:**

```bash
ls -lh fifa_bot.db
```

### **View Statistics:**

```bash
sqlite3 fifa_bot.db <<EOF
SELECT 'Users', COUNT(*) FROM users
UNION ALL
SELECT 'Leagues', COUNT(*) FROM leagues
UNION ALL
SELECT 'Matches', COUNT(*) FROM matches;
EOF
```

---

## 🔄 Reverting to JSON (Not Recommended)

If you need to revert:

1. Stop the bot
2. Restore `fifa_data.json.backup` to `fifa_data.json`
3. Update `main.py` to use `DatabaseService` instead of `SQLiteDatabaseService`
4. Restart the bot

---

## 📚 Further Reading

- [SQLite Documentation](https://www.sqlite.org/docs.html)
- [Python sqlite3 Module](https://docs.python.org/3/library/sqlite3.html)
- [SQL Tutorial](https://www.w3schools.com/sql/)

---

## ✅ Checklist

- [ ] Run migration: `python migrate_to_sqlite.py`
- [ ] Verify migration success
- [ ] Check backup file created
- [ ] Test bot functionality
- [ ] Setup automatic backups (cron job)
- [ ] Delete old JSON file (after confirming everything works)

---

**Questions or issues?** Check the logs or open an issue on GitHub!

