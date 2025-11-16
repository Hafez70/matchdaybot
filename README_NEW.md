# 🎮 FIFA Match Tracking Bot - Complete Guide

> A professional Telegram bot for tracking FIFA matches with league support, user registration, and comprehensive statistics.

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Telegram Bot](https://img.shields.io/badge/Telegram-Bot-blue.svg)](https://core.telegram.org/bots)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## 📖 Table of Contents

- [Features](#-features)
- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Usage](#-usage)
- [Project Structure](#-project-structure)
- [Documentation](#-documentation)
- [Examples](#-examples)
- [Migration](#-migration)
- [Contributing](#-contributing)
- [FAQ](#-faq)

## ✨ Features

### Core Features
- 🎯 **User Registration**: Automatic user registration and management
- 🏆 **League System**: Create and join multiple independent leagues
- ⚽ **Multiple Match Types**: 1v1, 2v2, 1v2, and 2v1 matches
- 📊 **Statistics**: Comprehensive stats per league
- 🏅 **Leaderboards**: Rankings based on wins and goal difference
- 📅 **Persian Calendar**: Full Jalali date support
- 🔒 **Privacy**: League-scoped data isolation

### User Management
- Unique identification via Telegram ID
- Edit your own name anytime
- Join multiple leagues
- View personal profile and stats

### League Features
- Create unlimited leagues
- Unique 6-character invite codes
- Share codes with friends
- League ownership and management
- Member list and statistics

### Match Recording
- League-scoped player selection
- Flexible team configurations (1v2, 2v1)
- Simple score input (e.g., 3-2)
- Automatic statistics calculation
- Match history tracking

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Bot
```bash
# Copy example config
cp env_example.txt config.env

# Edit config.env and add your bot token
TELEGRAM_BOT_TOKEN=your_token_here
```

### 3. Run Bot
```bash
# New modular version (recommended)
python main.py

# Or use the start script
chmod +x start.sh
./start.sh
```

### 4. Use Bot
1. Send `/start` to your bot
2. Register with your name
3. Create or join a league
4. Start recording matches!

## 📦 Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager
- Telegram Bot Token ([Get one from @BotFather](https://t.me/botfather))

### Dependencies
```bash
python-telegram-bot>=20.0
jdatetime>=4.0.0
python-dotenv>=1.0.0
```

### Step-by-Step

1. **Clone or Download**
   ```bash
   git clone <your-repo-url>
   cd test-analyzer
   ```

2. **Install Requirements**
   ```bash
   pip install -r requirements.txt
   ```

3. **Setup Environment**
   ```bash
   # Create config.env
   echo "TELEGRAM_BOT_TOKEN=your_token_here" > config.env
   ```

4. **Run**
   ```bash
   python main.py
   ```

## 📱 Usage

### Commands
- `/start` - Register or show main menu
- `/help` - Show help information

### User Flow

#### First Time Setup
```
1. Send /start to bot
2. Enter your name when prompted
3. Choose "Create League" or "Join League"
```

#### Creating a League
```
1. Select "ایجاد لیگ جدید" (Create New League)
2. Enter league name (e.g., "Office FIFA League")
3. Receive unique invite code (e.g., ABC123)
4. Share code with friends
```

#### Joining a League
```
1. Select "پیوستن به لیگ" (Join League)
2. Enter invite code you received
3. You're now a member!
```

#### Recording a Match
```
1. Select "لیگ‌های من" (My Leagues)
2. Choose your league
3. Select "ثبت مسابقه" (Record Match)
4. Choose match type (1v1, 2v2, 1v2, or 2v1)
5. Select players (only league members shown)
6. Enter result (e.g., 3-2)
```

#### Viewing Statistics
```
From league menu:
• آمار من (My Stats) - Your performance
• جدول لیگ (Leaderboard) - Top players
• مسابقات اخیر (Recent Matches) - Match history
• اعضای لیگ (League Members) - Member list
```

## 🏗️ Project Structure

```
test-analyzer/
├── main.py                      # Application entry point
├── bot.py                       # Original version (reference)
├── migrate_data.py             # Data migration utility
├── src/
│   ├── __init__.py
│   ├── models/                 # Data models
│   │   ├── user.py            # User model
│   │   ├── league.py          # League model
│   │   └── match.py           # Match model
│   ├── services/              # Business logic
│   │   ├── database_service.py    # Data persistence
│   │   ├── user_service.py        # User operations
│   │   ├── league_service.py      # League operations
│   │   └── match_service.py       # Match operations
│   ├── handlers/              # Bot handlers
│   │   ├── base_handler.py        # Base handler
│   │   ├── registration_handler.py # Registration
│   │   ├── account_handler.py     # Account management
│   │   ├── league_handler.py      # League operations
│   │   └── match_handler.py       # Match recording
│   ├── utils/                 # Utilities
│   │   ├── date_utils.py         # Date conversions
│   │   └── keyboard_builder.py   # Keyboard builders
│   └── config/                # Configuration
│       └── constants.py          # Constants & messages
├── config.env                  # Environment variables
├── fifa_data.json             # Database (auto-created)
├── requirements.txt           # Python dependencies
└── docs/                      # Documentation
    ├── README_MODULAR.md      # Main documentation
    ├── QUICK_START.md         # Quick start guide
    ├── MIGRATION_GUIDE.md     # Migration instructions
    ├── PROJECT_SUMMARY.md     # Project overview
    ├── ARCHITECTURE.md        # Technical details
    └── TRANSFORMATION_COMPLETE.md # Summary
```

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [QUICK_START.md](QUICK_START.md) | Get started in 5 minutes |
| [README_MODULAR.md](README_MODULAR.md) | Complete feature documentation |
| [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) | Migrate from old version |
| [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) | Detailed project overview |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Technical architecture |
| [TRANSFORMATION_COMPLETE.md](TRANSFORMATION_COMPLETE.md) | What's new summary |

## 💡 Examples

### Example 1: Office League
```
1. Ahmed creates "Office League" → Gets code "OFF123"
2. Ahmed shares "OFF123" in office group
3. Sara, John, Mary join using "OFF123"
4. They record matches throughout the week
5. Check leaderboard on Friday to see who's winning!
```

### Example 2: Multiple Leagues
```
Player: John
Leagues:
  • "Office League" (OFF123) - Plays during lunch
  • "Friends League" (FRD456) - Plays on weekends
  • "Family League" (FAM789) - Plays at home

Each league has:
  • Separate members
  • Independent statistics
  • Own leaderboard
```

### Example 3: Uneven Teams
```
Scenario: 3 players want to play

Match Type: 1v2
  Team 1: John
  Team 2: Sara & Mary
  Result: 4-3 (John wins!)

Or

Match Type: 2v1
  Team 1: John & Sara
  Team 2: Mary
  Result: 3-5 (Mary wins!)
```

## 🔄 Migration

### From Old Version

If you have existing data from `bot.py`:

```bash
# 1. Backup (automatic)
python migrate_data.py

# 2. Check backup
ls fifa_data_backup_*.json

# 3. Run new bot
python main.py
```

The migration script:
- ✅ Creates automatic backup
- ✅ Converts players to users
- ✅ Creates "LEGACY" league for old matches
- ✅ Migrates all match data
- ✅ Preserves statistics

See [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) for details.

## 🤝 Contributing

Contributions are welcome! Here's how:

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open Pull Request

### Development Setup
```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests (if available)
pytest

# Check code style
flake8 src/
```

## ❓ FAQ

### General

**Q: Do I need a Telegram account?**  
A: Yes, you need a Telegram account to use the bot.

**Q: How do I get a bot token?**  
A: Message [@BotFather](https://t.me/botfather) on Telegram and follow the instructions.

**Q: Can I use this for other games?**  
A: Yes! The code is flexible and can be adapted for any competitive game.

### Features

**Q: How many leagues can I join?**  
A: Unlimited! Join as many as you want.

**Q: Can I see stats from all my leagues combined?**  
A: Currently, stats are per-league. Global stats can be added as a feature.

**Q: What happens if I change my name?**  
A: Your new name applies to all leagues you're in.

**Q: Can league owners remove members?**  
A: Not yet, but this can be added as a feature.

### Technical

**Q: Where is data stored?**  
A: In `fifa_data.json` (JSON file database).

**Q: Can I use a real database (MySQL, PostgreSQL)?**  
A: Yes! Modify `DatabaseService` to use your database.

**Q: How do I backup my data?**  
A: Simply copy `fifa_data.json` regularly.

**Q: Can I run multiple bots?**  
A: Yes, use different tokens and data files.

### Troubleshooting

**Q: Bot doesn't respond**  
A: Check token in config.env, ensure bot is running.

**Q: Can't see other players**  
A: Make sure you're in the same league.

**Q: Migration failed**  
A: Check backup file, ensure old data format is correct.

**Q: Name already taken**  
A: Each name must be unique. Try adding a suffix.

## 📊 Statistics

### Code Metrics
- **Old Version**: 1 file, 1657 lines
- **New Version**: Modular, ~2500 lines (organized)
- **Files**: 20+ well-organized modules
- **Documentation**: 6 comprehensive guides

### Features
- 4 match types (1v1, 2v2, 1v2, 2v1)
- Unlimited leagues
- Unlimited users per league
- Full statistics tracking
- Persian language support

## 🔧 Configuration

### Environment Variables
```env
# config.env
TELEGRAM_BOT_TOKEN=your_token_here
```

### Customization
Edit `src/config/constants.py` to customize:
- Bot messages
- Conversation states
- Default settings

## 🎯 Roadmap

### Planned Features
- [ ] ELO rating system
- [ ] Tournament mode
- [ ] Match rematch requests
- [ ] Export to Excel/CSV
- [ ] Web dashboard
- [ ] Advanced statistics
- [ ] Player profiles with avatars
- [ ] Match scheduling
- [ ] Notifications
- [ ] Multi-language support

## 📜 License

This project is available for personal and educational use.

## 👨‍💻 Author

Created with ❤️ for FIFA gaming communities

## 🌟 Acknowledgments

- Telegram Bot API
- python-telegram-bot library
- jdatetime for Persian calendar
- All FIFA enthusiasts!

## 📞 Support

- 📖 Check documentation first
- 💬 Use `/help` in bot
- 🐛 Report issues on GitHub
- 💡 Suggest features

---

**Ready to track your FIFA matches?** 🎮⚽

```bash
python main.py
```

Let the games begin! 🏆

