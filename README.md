# 🎮 FIFA Match Tracking Bot ⚽

> A professional Telegram bot for tracking FIFA matches with league support, comprehensive statistics, and user management.

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Telegram Bot](https://img.shields.io/badge/Telegram-Bot-blue.svg)](https://core.telegram.org/bots)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## ✨ Features

### 🎯 Core Features
- 👤 **User Registration** - Automatic registration on first use
- 🏆 **League System** - Create and join multiple independent leagues
- ⚽ **Multiple Match Types** - 1v1, 2v2, 1v2, and 2v1 matches
- 📊 **Comprehensive Statistics** - Detailed stats per league
- 🏅 **Leaderboards** - Rankings based on wins and goal difference
- 🔒 **Privacy** - League-scoped data isolation
- 📅 **Persian Calendar** - Full Jalali date support

### 🎨 User Experience
- Intuitive inline keyboard interface
- Persian (Farsi) language support
- Clean, modern UI
- Easy navigation
- Simple score input

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- A Telegram Bot Token ([Get one from @BotFather](https://t.me/botfather))

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/fifa-match-tracker.git
cd fifa-match-tracker

# Install dependencies
pip install -r requirements.txt

# Configure bot token
cp env_example.txt config.env
# Edit config.env and add your TELEGRAM_BOT_TOKEN

# Run the bot
python main.py
```

## 📱 Usage

### Commands
- `/start` - Register or show main menu
- `/help` - Show help information

### User Flow

1. **Register**: Send `/start` and enter your name
2. **Create/Join League**: Choose to create a new league or join with an invite code
3. **Record Matches**: Select league → Choose match type → Select players → Enter score
4. **View Statistics**: Check your stats, leaderboard, and match history

## 🏗️ Architecture

```
src/
├── models/          # Data models (User, League, Match)
├── services/        # Business logic
├── handlers/        # Bot interaction handlers
├── utils/           # Helper functions
└── config/          # Configuration
```

### Design Patterns
- Service Layer Pattern
- Repository Pattern
- Builder Pattern
- Modular Architecture

## 📊 Match Types

- **1v1** - One player vs one player
- **2v2** - Two players vs two players
- **1v2** - One player vs two players (NEW!)
- **2v1** - Two players vs one player (NEW!)

## 🔄 Migration from Old Version

If you have data from an older version:

```bash
# Run migration script
python migrate_data.py

# Start the bot
python main.py
```

## 📚 Documentation

- **[INDEX.md](INDEX.md)** - Documentation navigation
- **[QUICK_START.md](QUICK_START.md)** - Quick setup guide
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Technical details
- **[MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)** - Migration instructions

## 🛠️ Configuration

Create a `config.env` file:

```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
```

## 📊 Statistics Features

Each league tracks:
- Total matches played
- Wins / Losses / Draws
- Goals scored / Goals conceded
- Goal difference
- Win percentage
- Player rankings

## 🔐 Security & Privacy

- Users identified by Telegram ID (unique)
- League-scoped data isolation
- Users can only edit their own names
- Invite codes control league access

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🌟 Features Roadmap

- [ ] ELO rating system
- [ ] Tournament mode
- [ ] Match rematch requests
- [ ] Export to Excel/CSV
- [ ] Web dashboard
- [ ] Advanced statistics
- [ ] Multi-language support

## 🙏 Acknowledgments

- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) - Telegram Bot API wrapper
- [jdatetime](https://github.com/pylover/jdatetime) - Persian calendar support

## 📞 Support

If you have any questions or issues, please open an issue on GitHub.

## ⚽ Screenshots

### Main Menu
![Main Menu](docs/screenshots/main_menu.png)

### Match Recording
![Match Recording](docs/screenshots/match_recording.png)

### Statistics
![Statistics](docs/screenshots/statistics.png)

---

**Made with ❤️ for FIFA gaming communities**

⭐ Star this repo if you find it useful!
