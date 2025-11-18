# League Management & GIF Features - Update Guide

## 🎉 New Features

### For League Owners:

1. **⚙️ League Settings Menu**
   - Access via league menu (only visible to owners)
   - Edit league name
   - Set custom winner GIF
   - Set custom loser GIF
   - Delete league (with confirmation)

2. **🏆 Custom GIFs for Match Results**
   - Winners receive custom GIF (if set by owner)
   - Losers receive custom GIF (if set by owner)
   - GIFs can be uploaded or provided as URLs
   - Falls back gracefully if GIFs not set

3. **✅ Fixed Match Result Emojis**
   - Emojis now show from each player's perspective
   - Winners see 🏆, losers see ❌, draws see 🤝
   - Previously only showed from team1's perspective

4. **🔔 Improved Notifications**
   - Participants get personalized stats + GIF
   - Non-participants get league update with action buttons
   - All league members notified after match recording

## 📦 Deployment to cPanel

### Step 1: Backup Current Database

```bash
ssh xqaebsls@nitro
cd ~/fifa-bot
cp fifa_bot.db fifa_bot.db.backup_$(date +%Y%m%d_%H%M%S)
```

### Step 2: Stop the Bot

```bash
./stop.sh
```

### Step 3: Pull Latest Code

```bash
git pull origin main
```

### Step 4: Run Database Migration

```bash
python3 migrate_add_league_gifs.py
```

Expected output:
```
🔄 Starting database migration...
Adding winner_gif column...
✅ winner_gif column added
Adding loser_gif column...
✅ loser_gif column added

🎉 Migration completed successfully!

📊 Updated schema:
  - code (TEXT)
  - name (TEXT)
  - owner_telegram_id (INTEGER)
  - winner_gif (TEXT)
  - loser_gif (TEXT)
  - created_at (TIMESTAMP)
```

### Step 5: Restart the Bot

```bash
./start.sh
```

### Step 6: Verify Bot is Running

```bash
tail -f bot.log
```

## 🎮 How to Use New Features

### Setting Up League GIFs (As Owner)

1. Go to your league
2. Click **⚙️ تنظیمات لیگ** (League Settings)
3. Click **🏆 تنظیم GIF برد** (Set Winner GIF)
4. Send a GIF/animation OR paste a GIF URL (e.g., from Giphy, Tenor)
5. Repeat for **❌ تنظیم GIF باخت** (Set Loser GIF)

### Finding GIF URLs

**Option 1: Giphy**
```
1. Go to https://giphy.com
2. Search for a GIF
3. Click "Share" → "Copy GIF Link"
4. Paste in bot
```

**Option 2: Tenor**
```
1. Go to https://tenor.com
2. Search for a GIF
3. Right-click GIF → "Copy image address"
4. Paste in bot
```

**Option 3: Telegram**
```
1. Find a GIF in Telegram
2. Forward it to your bot
3. Bot will use the file_id
```

### Example GIF URLs

**Winner GIFs:**
- `https://media.giphy.com/media/g9582DNuQppxC/giphy.gif` (celebration)
- `https://media.giphy.com/media/kyLYXonQYYfwYDIeZl/giphy.gif` (trophy)
- `https://media.giphy.com/media/111ebonMs90YLu/giphy.gif` (victory dance)

**Loser GIFs:**
- `https://media.giphy.com/media/d2lcHJTG5Tscg/giphy.gif` (sad)
- `https://media.giphy.com/media/ISOckXUybVfQ4/giphy.gif` (crying)
- `https://media.giphy.com/media/8Iv5lqKwKsZ2g/giphy.gif` (disappointed)

## 🔧 Troubleshooting

### Migration Fails

```bash
# Check if columns already exist
sqlite3 fifa_bot.db "PRAGMA table_info(leagues);"

# If migration script fails, add manually:
sqlite3 fifa_bot.db
ALTER TABLE leagues ADD COLUMN winner_gif TEXT;
ALTER TABLE leagues ADD COLUMN loser_gif TEXT;
.exit
```

### GIF Not Sending

- **File too large**: Telegram has a 50MB limit for animations
- **Invalid URL**: Make sure URL is direct link to GIF file
- **Bot continues**: GIF sending is optional, messages will still be sent

### League Settings Not Showing

- Make sure you're the league owner
- Only owners see the "⚙️ تنظیمات لیگ" button
- Try restarting the bot: `./stop.sh && ./start.sh`

## 📝 Database Schema Changes

### Before:
```sql
CREATE TABLE leagues (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    owner_telegram_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### After:
```sql
CREATE TABLE leagues (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    owner_telegram_id INTEGER NOT NULL,
    winner_gif TEXT,              -- NEW
    loser_gif TEXT,               -- NEW
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## ✨ Technical Details

### Why GIFs Instead of Stickers?

1. **Stickers require specific file_ids** that may expire or be invalid
2. **GIFs are more flexible** - can use URLs from Giphy, Tenor, etc.
3. **Easier for users** - just paste a link or send any GIF
4. **More customizable** - each league can have unique GIFs

### How Emoji Logic Works

**Before:** All emojis showed from Team 1's perspective
```
Team 1 wins: 🏆 (correct for team1, wrong for team2)
Team 2 wins: ❌ (wrong for team2, should be 🏆)
```

**After:** Emojis show from each player's perspective
```
Player in Team 1, Team 1 wins: 🏆
Player in Team 2, Team 1 wins: ❌
Player in Team 1, Team 2 wins: ❌
Player in Team 2, Team 2 wins: 🏆
```

## 🎯 Testing Checklist

After deployment, test these features:

- [ ] League owner can access settings menu
- [ ] League owner can edit league name
- [ ] League owner can set winner GIF (URL)
- [ ] League owner can set loser GIF (file upload)
- [ ] League owner can delete league (with confirmation)
- [ ] Non-owners don't see settings button
- [ ] Match recording sends GIFs to participants
- [ ] Emojis show correctly for each player
- [ ] Non-participants receive update notifications
- [ ] All existing features still work

## 🆘 Rollback Instructions

If something goes wrong:

```bash
cd ~/fifa-bot
./stop.sh

# Restore backup
mv fifa_bot.db fifa_bot.db.broken
cp fifa_bot.db.backup_YYYYMMDD_HHMMSS fifa_bot.db

# Revert code
git reset --hard HEAD~1

./start.sh
```

## 📞 Support

If you encounter any issues:
1. Check `bot.log` for errors
2. Verify database schema with `sqlite3 fifa_bot.db ".schema leagues"`
3. Test GIF URLs in browser first
4. Make sure bot has necessary permissions

---

**All features are backward compatible!** Existing leagues will work normally, and owners can optionally add GIFs.

