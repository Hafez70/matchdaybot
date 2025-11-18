"""Migration script from JSON to SQLite"""
import json
import os
from src.services.sqlite_database_service import SQLiteDatabaseService


def migrate_json_to_sqlite(json_file: str = 'fifa_data.json', db_file: str = 'fifa_bot.db'):
    """Migrate data from JSON file to SQLite database"""
    
    print("🔄 Starting migration from JSON to SQLite...")
    print("=" * 50)
    
    # Check if JSON file exists
    if not os.path.exists(json_file):
        print(f"❌ JSON file '{json_file}' not found!")
        print("✅ Creating fresh SQLite database...")
        db = SQLiteDatabaseService(db_file)
        print("✅ Fresh database created!")
        return
    
    # Backup JSON file
    backup_file = f"{json_file}.backup"
    if os.path.exists(json_file):
        import shutil
        shutil.copy(json_file, backup_file)
        print(f"📦 Backup created: {backup_file}")
    
    # Load JSON data
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ Error loading JSON: {e}")
        return
    
    print(f"📊 JSON data loaded:")
    print(f"   - Users: {len(data.get('users', []))}")
    print(f"   - Leagues: {len(data.get('leagues', []))}")
    print(f"   - Matches: {len(data.get('matches', []))}")
    print()
    
    # Initialize SQLite database
    db = SQLiteDatabaseService(db_file)
    print("✅ SQLite database initialized")
    print()
    
    # Migrate users
    print("👥 Migrating users...")
    users_migrated = 0
    for user in data.get('users', []):
        try:
            db.add_user(
                telegram_id=user['telegram_id'],
                name=user['name']
            )
            users_migrated += 1
            print(f"  ✓ {user['name']} (ID: {user['telegram_id']})")
        except Exception as e:
            print(f"  ✗ Error migrating user {user.get('name')}: {e}")
    
    print(f"✅ Migrated {users_migrated} users")
    print()
    
    # Migrate leagues
    print("🏆 Migrating leagues...")
    leagues_migrated = 0
    for league in data.get('leagues', []):
        try:
            db.add_league(
                code=league['code'],
                name=league['name'],
                owner_telegram_id=league['owner_telegram_id']
            )
            
            # Add members (owner already added in add_league)
            for member_id in league.get('members', []):
                if member_id != league['owner_telegram_id']:  # Skip owner (already added)
                    try:
                        db.add_league_member(league['code'], member_id)
                    except Exception as e:
                        print(f"  ⚠ Could not add member {member_id} to league {league['code']}: {e}")
            
            leagues_migrated += 1
            print(f"  ✓ {league['name']} ({league['code']}) - {len(league.get('members', []))} members")
        except Exception as e:
            print(f"  ✗ Error migrating league {league.get('name')}: {e}")
    
    print(f"✅ Migrated {leagues_migrated} leagues")
    print()
    
    # Migrate matches
    print("⚽ Migrating matches...")
    matches_migrated = 0
    for match in data.get('matches', []):
        try:
            # Determine match type
            team1_size = len(match['team1'])
            team2_size = len(match['team2'])
            match_type = f"{team1_size}v{team2_size}"
            
            match_id = db.add_match(
                league_code=match['league_code'],
                match_type=match_type,
                team1=match['team1'],
                team2=match['team2'],
                team1_score=match['result']['team1'],
                team2_score=match['result']['team2']
            )
            matches_migrated += 1
            
            if matches_migrated % 10 == 0:
                print(f"  ... {matches_migrated} matches migrated")
                
        except Exception as e:
            print(f"  ✗ Error migrating match {match.get('id')}: {e}")
    
    print(f"✅ Migrated {matches_migrated} matches")
    print()
    
    # Summary
    print("=" * 50)
    print("📊 Migration Summary:")
    print(f"  ✅ Users: {users_migrated}")
    print(f"  ✅ Leagues: {leagues_migrated}")
    print(f"  ✅ Matches: {matches_migrated}")
    print()
    print(f"💾 SQLite database: {db_file}")
    print(f"📦 JSON backup: {backup_file}")
    print()
    print("🎉 Migration completed successfully!")
    print("=" * 50)


if __name__ == '__main__':
    migrate_json_to_sqlite()

