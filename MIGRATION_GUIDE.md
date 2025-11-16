# Migration Guide: From Monolithic to Modular

## Overview

This guide helps you migrate from the old `bot.py` to the new modular structure.

## Key Changes

### 1. File Structure

**Old:**
- Single `bot.py` file (1657 lines)
- `FifaDatabase` class
- `FifaBot` class
- All logic in one file

**New:**
- Modular structure with separate directories
- `src/models/` - Data models
- `src/services/` - Business logic
- `src/handlers/` - Bot handlers
- `src/utils/` - Utility functions
- `src/config/` - Configuration

### 2. Data Structure Changes

**Old `fifa_data.json`:**
```json
{
  "persons": [
    {
      "id": 1,
      "name": "John",
      "telegram_id": 123456,
      "created_at": "2024-01-01T10:00:00"
    }
  ],
  "matches": [
    {
      "id": 1,
      "type": "1v1",
      "team1": ["John"],
      "team2": ["Jane"],
      "result": {"team1": 3, "team2": 2},
      "datetime": "2024-01-01T10:00:00"
    }
  ]
}
```

**New `fifa_data.json`:**
```json
{
  "users": [
    {
      "telegram_id": 123456,
      "name": "John",
      "leagues": ["ABC123", "XYZ789"],
      "created_at": "2024-01-01T10:00:00"
    }
  ],
  "leagues": [
    {
      "code": "ABC123",
      "name": "Friends League",
      "owner_telegram_id": 123456,
      "members": [123456, 789012],
      "created_at": "2024-01-01T10:00:00"
    }
  ],
  "matches": [
    {
      "id": 1,
      "league_code": "ABC123",
      "type": "1v1",
      "team1": [123456],
      "team2": [789012],
      "result": {"team1": 3, "team2": 2},
      "datetime": "2024-01-01T10:00:00"
    }
  ]
}
```

### 3. Migration Script

If you have existing data, you need to migrate it. Here's a migration script:

```python
# migrate_data.py
import json
import os

def migrate_data():
    """Migrate from old to new data structure"""
    
    # Load old data
    if not os.path.exists('fifa_data.json'):
        print("No existing data to migrate")
        return
    
    with open('fifa_data.json', 'r', encoding='utf-8') as f:
        old_data = json.load(f)
    
    # Check if already migrated
    if 'users' in old_data and 'leagues' in old_data:
        print("Data already migrated!")
        return
    
    # Backup old data
    with open('fifa_data_backup.json', 'w', encoding='utf-8') as f:
        json.dump(old_data, f, ensure_ascii=False, indent=2)
    
    print("Backup created: fifa_data_backup.json")
    
    # Create new structure
    new_data = {
        'users': [],
        'leagues': [],
        'matches': []
    }
    
    # Migrate persons to users
    person_to_telegram_id = {}
    for person in old_data.get('persons', []):
        telegram_id = person.get('telegram_id')
        if telegram_id:
            new_data['users'].append({
                'telegram_id': telegram_id,
                'name': person['name'],
                'leagues': [],  # Will be populated from matches
                'created_at': person.get('created_at', '')
            })
            person_to_telegram_id[person['name']] = telegram_id
    
    # Create a default league for old matches
    if old_data.get('matches'):
        default_league = {
            'code': 'LEGACY',
            'name': 'Legacy Matches',
            'owner_telegram_id': new_data['users'][0]['telegram_id'] if new_data['users'] else 0,
            'members': list(person_to_telegram_id.values()),
            'created_at': old_data['matches'][0].get('datetime', '')
        }
        new_data['leagues'].append(default_league)
        
        # Add legacy league to all users
        for user in new_data['users']:
            user['leagues'].append('LEGACY')
    
    # Migrate matches
    for match in old_data.get('matches', []):
        # Convert player names to telegram IDs
        team1_ids = []
        for name in match['team1']:
            if name in person_to_telegram_id:
                team1_ids.append(person_to_telegram_id[name])
        
        team2_ids = []
        for name in match['team2']:
            if name in person_to_telegram_id:
                team2_ids.append(person_to_telegram_id[name])
        
        if team1_ids and team2_ids:
            new_data['matches'].append({
                'id': match['id'],
                'league_code': 'LEGACY',
                'type': match['type'],
                'team1': team1_ids,
                'team2': team2_ids,
                'result': match['result'],
                'datetime': match['datetime']
            })
    
    # Save new data
    with open('fifa_data.json', 'w', encoding='utf-8') as f:
        json.dump(new_data, f, ensure_ascii=False, indent=2)
    
    print("Migration complete!")
    print(f"Migrated {len(new_data['users'])} users")
    print(f"Created {len(new_data['leagues'])} league(s)")
    print(f"Migrated {len(new_data['matches'])} matches")

if __name__ == '__main__':
    migrate_data()
```

Run migration:
```bash
python migrate_data.py
```

### 4. Key Differences

#### User Registration
**Old**: Manual player addition
**New**: Automatic registration on /start

#### Player Identification
**Old**: By name (string matching)
**New**: By telegram_id (unique identifier)

#### Data Scope
**Old**: Global - all players see all data
**New**: League-scoped - players only see data from their leagues

#### Match Recording
**Old**: Select any registered player
**New**: Select only players from the same league

#### Name Editing
**Old**: Not supported
**New**: Users can edit their own names

#### Match Types
**Old**: 1v1 and 2v2 only
**New**: 1v1, 2v2, 1v2, and 2v1

### 5. Running Both Versions

You can run both versions side by side:

```bash
# Run new version (recommended)
python main.py

# Run old version
python bot.py
```

**Note**: Use different data files or run one at a time to avoid conflicts.

### 6. Benefits of Modular Version

1. **Better Organization**: Code is organized by responsibility
2. **Easier Maintenance**: Changes are isolated to specific modules
3. **Scalability**: Easy to add new features
4. **Testing**: Each module can be tested independently
5. **League System**: Better data organization and privacy
6. **Flexibility**: Support for asymmetric matches (1v2, 2v1)

### 7. Troubleshooting

#### Issue: Bot doesn't start
- Check `TELEGRAM_BOT_TOKEN` in config.env
- Verify all dependencies are installed
- Check Python version (3.8+)

#### Issue: Old data not visible
- Run migration script
- Check fifa_data.json format

#### Issue: Users can't see each other
- Make sure users are in the same league
- Verify league membership

## Support

For issues or questions, please refer to the main README.md or create an issue.

