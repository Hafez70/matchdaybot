# Quick Start Guide

## 🚀 Getting Started with the Modular FIFA Bot

### Option 1: Fresh Installation (Recommended for new users)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp env_example.txt config.env
# Edit config.env and add your TELEGRAM_BOT_TOKEN

# 3. Run the bot
python main.py
```

### Option 2: Migrating from Old Version

If you have existing data from the old `bot.py`:

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Migrate your data
python migrate_data.py

# 3. Run the new bot
python main.py
```

### Option 3: Using Start Script

```bash
# Make script executable
chmod +x start.sh

# Start new version
./start.sh

# Migrate and start
./start.sh --migrate

# Start old version (for comparison)
./start.sh --old
```

## 📱 First Time User Flow

### 1. Start the Bot
Send `/start` to your bot

### 2. Register
- Bot will ask for your name
- Enter your name (this will be shown in matches)

### 3. Create or Join a League

**Create a League:**
- Select "ایجاد لیگ جدید" (Create New League)
- Enter league name
- You'll receive a unique invite code (e.g., ABC123)
- Share this code with friends

**Join a League:**
- Select "پیوستن به لیگ" (Join League)
- Enter the invite code you received
- You're now a member!

### 4. Record a Match

- Select "لیگ‌های من" (My Leagues)
- Choose your league
- Select "ثبت مسابقه" (Record Match)
- Choose match type:
  - 1v1 (one vs one)
  - 2v2 (two vs two)
  - 1v2 (one vs two)
  - 2v1 (two vs one)
- Select players from league members
- Enter result (e.g., 3-2)

### 5. View Statistics

From league menu:
- **آمار من** (My Stats) - Your performance
- **جدول لیگ** (Leaderboard) - Top players
- **مسابقات اخیر** (Recent Matches) - Match history
- **اعضای لیگ** (League Members) - Member list

## ⚙️ Account Settings

Select "تنظیمات حساب" (Account Settings) to:
- Edit your name
- View your profile
- See all your leagues

## 🔍 Important Notes

### League Scope
- Each league is independent
- You can join multiple leagues
- Statistics are separate for each league
- You can only see players from your own leagues

### Name Editing
- You can edit your own name anytime
- Your name must be unique
- Name changes apply to all your leagues

### Match Types
- **1v1**: Standard one-on-one
- **2v2**: Two players per team
- **1v2**: One player vs two players (uneven teams)
- **2v1**: Two players vs one player (uneven teams)

### League Codes
- Each league has a unique 6-character code
- Codes are case-insensitive
- Share codes carefully (anyone with code can join)

## 🐛 Troubleshooting

### Bot doesn't respond
- Check if bot is running: `ps aux | grep main.py`
- Check bot logs: `tail -f bot.log`
- Verify TELEGRAM_BOT_TOKEN in config.env

### Can't see other players
- Make sure you're in the same league
- Check league membership: "اعضای لیگ"

### Migration issues
- Check backup file was created
- Verify old data format
- Run: `python migrate_data.py` again

### Name already taken
- Each name must be unique across all users
- Try a different name or add a suffix

## 📊 File Locations

- **Config**: `config.env`
- **Data**: `fifa_data.json`
- **Logs**: `bot.log` (when using start.sh)
- **Backups**: `fifa_data_backup_*.json`

## 🔄 Switching Between Versions

### Use New Version (Recommended)
```bash
python main.py
```

### Use Old Version
```bash
python bot.py
```

**Note**: Don't run both at the same time with the same data file!

## 💡 Tips

1. **Create a test league** first to familiarize yourself
2. **Share league codes** via private messages
3. **Regular backups**: Copy fifa_data.json regularly
4. **Use descriptive league names** for better organization
5. **Check leaderboard** regularly to track progress

## 📞 Getting Help

- Use `/help` command in bot for in-app help
- Check `README_MODULAR.md` for detailed documentation
- Read `MIGRATION_GUIDE.md` if migrating from old version

## 🎮 Example Workflow

```
1. /start → Register as "John"
2. Create League "Office League" → Get code "ABC123"
3. Share "ABC123" with colleagues
4. They join using the code
5. Record match: John vs Jane, 3-2
6. Check leaderboard to see standings
7. Continue playing and tracking!
```

Enjoy your FIFA matches! ⚽🎮

