"""Data migration script from old to new structure"""
import json
import os
import shutil
from datetime import datetime


def migrate_data():
    """Migrate from old to new data structure"""
    
    print("🔄 Starting migration from old to new data structure...")
    
    # Load old data
    if not os.path.exists('fifa_data.json'):
        print("ℹ️  No existing data found. Creating fresh database...")
        new_data = {
            'users': [],
            'leagues': [],
            'matches': []
        }
        with open('fifa_data.json', 'w', encoding='utf-8') as f:
            json.dump(new_data, f, ensure_ascii=False, indent=2)
        print("✅ Fresh database created!")
        return
    
    with open('fifa_data.json', 'r', encoding='utf-8') as f:
        old_data = json.load(f)
    
    # Check if already migrated
    if 'users' in old_data and 'leagues' in old_data:
        print("ℹ️  Data is already in new format!")
        return
    
    # Backup old data
    backup_file = f'fifa_data_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    shutil.copy('fifa_data.json', backup_file)
    print(f"📦 Backup created: {backup_file}")
    
    # Create new structure
    new_data = {
        'users': [],
        'leagues': [],
        'matches': []
    }
    
    # Migrate persons to users
    person_to_telegram_id = {}
    print("\n👥 Migrating users...")
    for person in old_data.get('persons', []):
        telegram_id = person.get('telegram_id')
        if telegram_id:
            new_data['users'].append({
                'telegram_id': telegram_id,
                'name': person['name'],
                'leagues': [],
                'created_at': person.get('created_at', datetime.now().isoformat())
            })
            person_to_telegram_id[person['name']] = telegram_id
            print(f"  ✓ Migrated: {person['name']} (ID: {telegram_id})")
    
    # Create a default league for old matches
    if old_data.get('matches') and new_data['users']:
        print("\n🏆 Creating legacy league...")
        default_league = {
            'code': 'LEGACY',
            'name': 'Legacy Matches (Imported)',
            'owner_telegram_id': new_data['users'][0]['telegram_id'],
            'members': list(person_to_telegram_id.values()),
            'created_at': old_data['matches'][0].get('datetime', datetime.now().isoformat())
        }
        new_data['leagues'].append(default_league)
        print("  ✓ Created LEGACY league for existing matches")
        
        # Add legacy league to all users
        for user in new_data['users']:
            user['leagues'].append('LEGACY')
    
    # Migrate matches
    print("\n⚽ Migrating matches...")
    migrated_count = 0
    skipped_count = 0
    
    for match in old_data.get('matches', []):
        # Convert player names to telegram IDs
        team1_ids = []
        for name in match['team1']:
            if name in person_to_telegram_id:
                team1_ids.append(person_to_telegram_id[name])
            else:
                print(f"  ⚠️  Warning: Player '{name}' not found in team1")
        
        team2_ids = []
        for name in match['team2']:
            if name in person_to_telegram_id:
                team2_ids.append(person_to_telegram_id[name])
            else:
                print(f"  ⚠️  Warning: Player '{name}' not found in team2")
        
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
            migrated_count += 1
        else:
            skipped_count += 1
    
    print(f"  ✓ Migrated: {migrated_count} matches")
    if skipped_count > 0:
        print(f"  ⚠️  Skipped: {skipped_count} matches (incomplete data)")
    
    # Save new data
    with open('fifa_data.json', 'w', encoding='utf-8') as f:
        json.dump(new_data, f, ensure_ascii=False, indent=2)
    
    print("\n" + "="*50)
    print("✅ Migration complete!")
    print("="*50)
    print(f"📊 Summary:")
    print(f"  • Users: {len(new_data['users'])}")
    print(f"  • Leagues: {len(new_data['leagues'])}")
    print(f"  • Matches: {len(new_data['matches'])}")
    print(f"\n💾 Backup saved to: {backup_file}")
    print("\n🚀 You can now run: python main.py")
    print("="*50)


if __name__ == '__main__':
    try:
        migrate_data()
    except Exception as e:
        print(f"\n❌ Migration failed: {str(e)}")
        print("Please check your data file and try again.")

