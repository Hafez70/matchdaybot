# FIFA Match Tracking Bot - Modular Edition

A comprehensive Telegram bot for tracking FIFA matches with league support, user registration, and advanced match recording capabilities.

## 🎯 Features

### ✨ New Features (Modular Version)

- **User Registration System**: Automatic registration when user starts the bot
- **League System**: Create and join multiple leagues with unique invite codes
- **League Scope**: All data is filtered by league for better organization
- **Enhanced Match Types**: Support for 1v1, 2v2, 1v2, and 2v1 matches
- **Account Management**: Users can edit their own names
- **Modular Architecture**: Clean separation of concerns with models, services, and handlers

### 📊 Core Features

- Record match results with various team configurations
- View player statistics within each league
- League leaderboards with wins and goal difference
- Recent match history per league
- Persian (Jalali) date support
- Inline keyboard interface for easy navigation

## 🏗️ Project Structure

```
test-analyzer/
├── main.py                      # New modular entry point
├── bot.py                       # Original bot (kept for reference)
├── src/
│   ├── __init__.py
│   ├── models/                  # Data models
│   │   ├── __init__.py
│   │   ├── user.py             # User model
│   │   ├── league.py           # League model
│   │   └── match.py            # Match model
│   ├── services/               # Business logic
│   │   ├── __init__.py
│   │   ├── database_service.py  # Data persistence
│   │   ├── user_service.py      # User management
│   │   ├── league_service.py    # League management
│   │   └── match_service.py     # Match management
│   ├── handlers/               # Bot handlers
│   │   ├── __init__.py
│   │   ├── base_handler.py      # Base handler class
│   │   ├── registration_handler.py  # Registration & onboarding
│   │   ├── account_handler.py   # Account management
│   │   ├── league_handler.py    # League operations
│   │   └── match_handler.py     # Match recording
│   ├── utils/                  # Utilities
│   │   ├── __init__.py
│   │   ├── date_utils.py       # Date conversions
│   │   └── keyboard_builder.py  # Keyboard builders
│   └── config/                 # Configuration
│       ├── __init__.py
│       └── constants.py        # Constants and messages
├── requirements.txt
└── README.md
```

## 🚀 Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd test-analyzer
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   
   Create a `config.env` file:
   ```env
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   ```

4. **Run the bot**
   ```bash
   # Run new modular version
   python main.py
   
   # Or run original version
   python bot.py
   ```

## 📱 User Flow

1. **Registration** (`/start`)
   - User sends /start
   - Bot asks for name
   - User is registered automatically

2. **League Management**
   - Create a new league (receive unique invite code)
   - Join existing league with invite code
   - View all your leagues

3. **Match Recording**
   - Select a league
   - Choose "ثبت مسابقه" (Record Match)
   - Select match type (1v1, 2v2, 1v2, 2v1)
   - Choose players from league members
   - Enter result (e.g., 3-2)

4. **Statistics & Leaderboard**
   - View your stats in each league
   - Check league leaderboard
   - See recent matches

## 🔧 Technical Details

### Data Models

- **User**: Telegram ID, name, leagues, registration date
- **League**: Code, name, owner, members, creation date
- **Match**: League code, type, teams, result, datetime

### Service Layer

- **DatabaseService**: JSON file-based persistence
- **UserService**: User registration, name updates, league membership
- **LeagueService**: League creation, joining, member management
- **MatchService**: Match recording, statistics, leaderboards

### Handlers

- **RegistrationHandler**: Onboarding and help
- **AccountHandler**: Profile management
- **LeagueHandler**: League operations and views
- **MatchHandler**: Match recording flow

## 🎮 Commands

- `/start` - Register or show main menu
- `/help` - Show help message

## 📊 Match Types

- **1v1**: One player vs one player
- **2v2**: Two players vs two players
- **1v2**: One player vs two players
- **2v1**: Two players vs one player

## 🔐 Security Features

- Users can only edit their own names
- League owners have special privileges
- League-scoped data isolation
- Telegram ID-based authentication

## 🌍 Localization

- Full Persian (Farsi) interface
- Jalali (Persian) date format
- RTL-friendly messages

## 📈 Future Enhancements

- Player ratings (ELO system)
- Tournament mode
- Match rematch requests
- Export statistics to Excel
- Web dashboard
- Advanced filtering and search
- Notifications for league activities

## 🤝 Contributing

Feel free to submit issues and enhancement requests!

## 📝 License

This project is for personal/educational use.

## 👨‍💻 Author

Created with ❤️ for FIFA gaming communities

