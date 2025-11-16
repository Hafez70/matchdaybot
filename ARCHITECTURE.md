# Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         TELEGRAM BOT API                            │
└─────────────────────────────────────┬───────────────────────────────┘
                                      │
┌─────────────────────────────────────▼───────────────────────────────┐
│                            main.py                                   │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                    FifaBot (Main App)                         │  │
│  │  • Setup conversation handlers                                │  │
│  │  • Route callbacks to appropriate handlers                    │  │
│  │  • Error handling                                             │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────┬───────────────────────────────┘
                                      │
         ┌────────────────────────────┼────────────────────────────┐
         │                            │                            │
┌────────▼─────────┐        ┌─────────▼─────────┐      ┌─────────▼─────────┐
│  HANDLERS        │        │    SERVICES        │      │    MODELS         │
│  (Bot Logic)     │◄───────┤  (Business Logic)  │◄─────┤   (Data Layer)    │
│                  │        │                    │      │                   │
│ • Registration   │        │ • UserService      │      │ • User            │
│ • Account        │        │ • LeagueService    │      │ • League          │
│ • League         │        │ • MatchService     │      │ • Match           │
│ • Match          │        │ • DatabaseService  │      │                   │
│ • Base           │        │                    │      │                   │
└──────────────────┘        └──────────┬─────────┘      └───────────────────┘
         │                             │
         │                             │
         │                   ┌─────────▼─────────┐
         │                   │  fifa_data.json   │
         │                   │                   │
         │                   │  • users          │
         └───────────────────┤  • leagues        │
              (Uses)         │  • matches        │
                             └───────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                          UTILITIES                                   │
│  ┌─────────────────────┐        ┌──────────────────────┐           │
│  │  KeyboardBuilder    │        │    DateUtils         │           │
│  │  • Build menus      │        │  • Persian dates     │           │
│  │  • Player selection │        │  • Format datetime   │           │
│  └─────────────────────┘        └──────────────────────┘           │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                       CONFIGURATION                                  │
│  • States (conversation states)                                      │
│  • Messages (bot messages in Persian)                                │
│  • Constants                                                         │
└─────────────────────────────────────────────────────────────────────┘
```

## Data Flow

### User Registration Flow
```
User: /start
    │
    ▼
RegistrationHandler.start()
    │
    ├─► UserService.is_user_registered() ──► DatabaseService
    │
    ├─► If registered: Show main menu
    │
    └─► If not: Request name
            │
            ▼
        User enters name
            │
            ▼
        UserService.register_user()
            │
            ▼
        DatabaseService.add_user()
            │
            ▼
        Show main menu
```

### Match Recording Flow
```
User: Record Match
    │
    ▼
Select League ──► LeagueService.get_user_leagues()
    │
    ▼
Select Match Type (1v1, 2v2, 1v2, 2v1)
    │
    ▼
Select Team 1 Players ◄── UserService.get_users_in_league()
    │                          (League scoped!)
    ▼
Select Team 2 Players ◄── (Filtered: exclude Team 1)
    │
    ▼
Enter Result (e.g., 3-2)
    │
    ▼
MatchService.create_match()
    │
    ├─► Build Match object
    ├─► Set league_code
    └─► DatabaseService.add_match()
            │
            ▼
        Match saved!
```

### Statistics Flow
```
User: View Stats
    │
    ▼
Select League
    │
    ▼
LeagueHandler.show_my_stats()
    │
    ▼
MatchService.get_player_stats(user_id, league_code)
    │
    ├─► Get all matches in league
    ├─► Filter by player
    ├─► Calculate: wins, losses, draws, goals
    └─► Return statistics
            │
            ▼
        Display to user
```

## Conversation Handler States

```
Registration:
  REGISTRATION_NAME → User enters name → END

Create League:
  CREATE_LEAGUE_NAME → User enters league name → END

Join League:
  JOIN_LEAGUE_CODE → User enters code → END

Edit Name:
  EDIT_NAME → User enters new name → END

Record Match:
  MATCH_SELECT_TYPE → Select match type
        ↓
  MATCH_TEAM1_P1 → Select player 1 of team 1
        ↓
  MATCH_TEAM1_P2 → (if 2v2 or 2v1)
        ↓
  MATCH_TEAM2_P1 → Select player 1 of team 2
        ↓
  MATCH_TEAM2_P2 → (if 2v2 or 1v2)
        ↓
  MATCH_RESULT → Enter score → END
```

## Key Design Patterns

### 1. Service Layer Pattern
- Business logic separated from handlers
- Reusable across different handlers
- Easy to test independently

### 2. Repository Pattern
- DatabaseService abstracts data access
- Easy to switch to different storage (SQL, etc.)

### 3. Builder Pattern
- KeyboardBuilder constructs complex keyboards
- Consistent UI across the app

### 4. Strategy Pattern
- Different match types handled dynamically
- Match flow adapts based on type (1v1, 2v2, 1v2, 2v1)

## League Scope Implementation

```
┌─────────────────────────────────────────┐
│           User A                        │
│  Leagues: [ABC123, XYZ789]              │
└─────────────────┬───────────────────────┘
                  │
      ┌───────────┴──────────┐
      │                      │
      ▼                      ▼
┌─────────────┐        ┌─────────────┐
│ League      │        │ League      │
│ ABC123      │        │ XYZ789      │
│             │        │             │
│ Members:    │        │ Members:    │
│ • User A    │        │ • User A    │
│ • User B    │        │ • User C    │
│ • User C    │        │ • User D    │
│             │        │             │
│ Matches:    │        │ Matches:    │
│ • Match 1   │        │ • Match 3   │
│ • Match 2   │        │ • Match 4   │
└─────────────┘        └─────────────┘

When User A records a match in ABC123:
  → Only sees: User A, User B, User C
  → Match saved with league_code: ABC123

When User A views stats in XYZ789:
  → Only matches from XYZ789 are counted
```

## Security & Privacy

1. **User Identification**: Telegram ID (immutable, unique)
2. **Name Editing**: Only own name (checked by telegram_id)
3. **League Privacy**: Users only see their league data
4. **Invite Codes**: Control league membership

## Error Handling

```python
try:
    # Operation
    service.some_operation()
except ValueError as e:
    # User-friendly error message
    await update.message.reply_text(f"⚠️ {str(e)}")
except Exception as e:
    # Log error, show generic message
    logger.error(f"Error: {e}")
    await update.message.reply_text("❌ خطایی رخ داد")
```

## Testing Strategy (Future)

```
Unit Tests:
  • Models: User, League, Match
  • Services: UserService, LeagueService, MatchService
  • Utils: KeyboardBuilder, DateUtils

Integration Tests:
  • Database operations
  • Service interactions

End-to-End Tests:
  • Complete user flows
  • Bot conversations
```

This architecture ensures:
- ✅ Separation of concerns
- ✅ Testability
- ✅ Maintainability
- ✅ Scalability
- ✅ Data integrity
- ✅ User privacy

