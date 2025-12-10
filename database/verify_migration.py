"""Verify SQLite migration"""
import sqlite3
import json
import sys

# Fix Windows console encoding
sys.stdout.reconfigure(encoding='utf-8')

def verify_migration():
    """Verify that data was correctly migrated from JSON to SQLite"""
    
    print("=" * 60)
    print("📊 MIGRATION VERIFICATION REPORT")
    print("=" * 60)
    print()
    
    # Load JSON data
    with open('fifa_data.json', 'r', encoding='utf-8') as f:
        json_data = json.load(f)
    
    # Connect to SQLite
    conn = sqlite3.connect('fifa_bot.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Count records
    json_users = len(json_data.get('users', []))
    json_leagues = len(json_data.get('leagues', []))
    json_matches = len(json_data.get('matches', []))
    
    cursor.execute("SELECT COUNT(*) FROM users")
    db_users = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM leagues")
    db_leagues = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM matches")
    db_matches = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM league_members")
    db_league_members = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM match_players")
    db_match_players = cursor.fetchone()[0]
    
    # Print summary
    print("📋 RECORD COUNTS:")
    print("-" * 60)
    print(f"Users:           JSON: {json_users:3d}  →  SQLite: {db_users:3d}  {'✅' if json_users == db_users else '❌'}")
    print(f"Leagues:         JSON: {json_leagues:3d}  →  SQLite: {db_leagues:3d}  {'✅' if json_leagues == db_leagues else '❌'}")
    print(f"Matches:         JSON: {json_matches:3d}  →  SQLite: {db_matches:3d}  {'✅' if json_matches == db_matches else '❌'}")
    print(f"League Members:         →  SQLite: {db_league_members:3d}")
    print(f"Match Players:          →  SQLite: {db_match_players:3d}")
    print()
    
    # Verify users
    print("👥 USERS VERIFICATION:")
    print("-" * 60)
    all_users_ok = True
    for json_user in json_data.get('users', []):
        cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (json_user['telegram_id'],))
        db_user = cursor.fetchone()
        
        if db_user:
            name_match = db_user['name'] == json_user['name']
            status = "✅" if name_match else "❌"
            print(f"{status} {json_user['name']} (ID: {json_user['telegram_id']})")
            if not name_match:
                all_users_ok = False
                print(f"   JSON: {json_user['name']} vs DB: {db_user['name']}")
        else:
            all_users_ok = False
            print(f"❌ {json_user['name']} (ID: {json_user['telegram_id']}) - NOT FOUND IN DB")
    
    print()
    
    # Verify leagues
    print("🏆 LEAGUES VERIFICATION:")
    print("-" * 60)
    all_leagues_ok = True
    for json_league in json_data.get('leagues', []):
        cursor.execute("SELECT * FROM leagues WHERE code = ?", (json_league['code'],))
        db_league = cursor.fetchone()
        
        if db_league:
            name_match = db_league['name'] == json_league['name']
            owner_match = db_league['owner_telegram_id'] == json_league['owner_telegram_id']
            
            # Get members from DB
            cursor.execute("SELECT telegram_id FROM league_members WHERE league_code = ?", (json_league['code'],))
            db_members = [row['telegram_id'] for row in cursor.fetchall()]
            members_match = set(db_members) == set(json_league['members'])
            
            all_ok = name_match and owner_match and members_match
            status = "✅" if all_ok else "❌"
            
            print(f"{status} {json_league['name']} ({json_league['code']})")
            print(f"   Name:    {'✅' if name_match else '❌'}")
            print(f"   Owner:   {'✅' if owner_match else '❌'}")
            print(f"   Members: {'✅' if members_match else '❌'} (JSON: {len(json_league['members'])} vs DB: {len(db_members)})")
            
            if not members_match:
                all_leagues_ok = False
                json_set = set(json_league['members'])
                db_set = set(db_members)
                missing_in_db = json_set - db_set
                extra_in_db = db_set - json_set
                if missing_in_db:
                    print(f"   Missing in DB: {missing_in_db}")
                if extra_in_db:
                    print(f"   Extra in DB: {extra_in_db}")
        else:
            all_leagues_ok = False
            print(f"❌ {json_league['name']} ({json_league['code']}) - NOT FOUND IN DB")
    
    print()
    
    # Verify matches
    print("⚽ MATCHES VERIFICATION:")
    print("-" * 60)
    all_matches_ok = True
    for json_match in json_data.get('matches', []):
        cursor.execute("SELECT * FROM matches WHERE id = ?", (json_match['id'],))
        db_match = cursor.fetchone()
        
        if db_match:
            # Get match players
            cursor.execute("SELECT telegram_id, team_number FROM match_players WHERE match_id = ?", (json_match['id'],))
            players = cursor.fetchall()
            
            db_team1 = sorted([p['telegram_id'] for p in players if p['team_number'] == 1])
            db_team2 = sorted([p['telegram_id'] for p in players if p['team_number'] == 2])
            json_team1 = sorted(json_match['team1'])
            json_team2 = sorted(json_match['team2'])
            
            league_match = db_match['league_code'] == json_match['league_code']
            type_match = db_match['match_type'] == json_match['type']
            team1_match = db_team1 == json_team1
            team2_match = db_team2 == json_team2
            score1_match = db_match['team1_score'] == json_match['result']['team1']
            score2_match = db_match['team2_score'] == json_match['result']['team2']
            
            all_ok = league_match and type_match and team1_match and team2_match and score1_match and score2_match
            status = "✅" if all_ok else "❌"
            
            print(f"{status} Match #{json_match['id']}: {json_match['result']['team1']}-{json_match['result']['team2']}")
            
            if not all_ok:
                all_matches_ok = False
                if not league_match:
                    print(f"   League: JSON: {json_match['league_code']} vs DB: {db_match['league_code']}")
                if not type_match:
                    print(f"   Type: JSON: {json_match['type']} vs DB: {db_match['match_type']}")
                if not team1_match:
                    print(f"   Team1: JSON: {json_team1} vs DB: {db_team1}")
                if not team2_match:
                    print(f"   Team2: JSON: {json_team2} vs DB: {db_team2}")
                if not score1_match:
                    print(f"   Score1: JSON: {json_match['result']['team1']} vs DB: {db_match['team1_score']}")
                if not score2_match:
                    print(f"   Score2: JSON: {json_match['result']['team2']} vs DB: {db_match['team2_score']}")
        else:
            all_matches_ok = False
            print(f"❌ Match #{json_match['id']} - NOT FOUND IN DB")
    
    print()
    print("=" * 60)
    print("📊 FINAL RESULT:")
    print("=" * 60)
    
    if (json_users == db_users and json_leagues == db_leagues and 
        json_matches == db_matches and all_users_ok and all_leagues_ok and all_matches_ok):
        print("✅ ✅ ✅ MIGRATION SUCCESSFUL! ALL DATA VERIFIED! ✅ ✅ ✅")
    else:
        print("❌ MIGRATION HAS ISSUES - PLEASE REVIEW ABOVE")
        if json_users != db_users:
            print(f"   - User count mismatch")
        if json_leagues != db_leagues:
            print(f"   - League count mismatch")
        if json_matches != db_matches:
            print(f"   - Match count mismatch")
        if not all_users_ok:
            print(f"   - Some users have data issues")
        if not all_leagues_ok:
            print(f"   - Some leagues have data issues")
        if not all_matches_ok:
            print(f"   - Some matches have data issues")
    
    print("=" * 60)
    
    conn.close()

if __name__ == '__main__':
    verify_migration()

