"""Create mock data for testing the Mini App locally"""
import sqlite3
import os
from datetime import datetime, timedelta
import random

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), 'fifa_bot.db')

def create_mock_data():
    """Create 4 users, 3 leagues, and matches with realistic stats"""
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create tables if they don't exist
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            telegram_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS leagues (
            code TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            owner_telegram_id INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS league_members (
            league_code TEXT,
            telegram_id INTEGER,
            joined_at TEXT DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (league_code, telegram_id)
        );
        
        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            league_code TEXT NOT NULL,
            match_type TEXT NOT NULL DEFAULT '2v2',
            team1_score INTEGER NOT NULL,
            team2_score INTEGER NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS match_players (
            match_id INTEGER,
            telegram_id INTEGER,
            team_number INTEGER,
            PRIMARY KEY (match_id, telegram_id)
        );
    """)
    
    # Mock users - one is the test user (93205092)
    users = [
        (93205092, 'Ali (Test)', '2025-01-01 10:00:00'),
        (100001, 'Mohammad', '2025-01-02 11:00:00'),
        (100002, 'Reza', '2025-01-03 12:00:00'),
        (100003, 'Amir', '2025-01-04 13:00:00'),
    ]
    
    # Mock leagues (code, name, owner_telegram_id, created_at)
    leagues = [
        ('LEAGUE1', 'Premier League', 93205092, '2025-01-01 10:00:00'),  # Test user is owner
        ('LEAGUE2', 'Friendly League', 100001, '2025-01-05 10:00:00'),  # Test user is member
        ('LEAGUE3', 'Cup Tournament', 93205092, '2025-01-10 10:00:00'),  # Test user is owner
    ]
    
    print("[*] Clearing existing mock data...")
    # Clear existing data for mock IDs
    for user_id, _, _ in users:
        cursor.execute("DELETE FROM users WHERE telegram_id = ?", (user_id,))
        cursor.execute("DELETE FROM league_members WHERE telegram_id = ?", (user_id,))
        cursor.execute("DELETE FROM match_players WHERE telegram_id = ?", (user_id,))
    
    for code, _, _, _ in leagues:
        cursor.execute("DELETE FROM leagues WHERE code = ?", (code,))
        cursor.execute("DELETE FROM matches WHERE league_code = ?", (code,))
    
    print("[*] Creating users...")
    for telegram_id, name, created_at in users:
        cursor.execute(
            "INSERT OR REPLACE INTO users (telegram_id, name, created_at) VALUES (?, ?, ?)",
            (telegram_id, name, created_at)
        )
        print(f"  + {name} (ID: {telegram_id})")
    
    print("\n[*] Creating leagues...")
    for code, name, owner_id, created_at in leagues:
        cursor.execute(
            "INSERT OR REPLACE INTO leagues (code, name, owner_telegram_id, created_at) VALUES (?, ?, ?, ?)",
            (code, name, owner_id, created_at)
        )
        print(f"  + {name} (Code: {code})")
    
    print("\n[*] Adding members to leagues...")
    # All users join all leagues
    for code, name, _, _ in leagues:
        for telegram_id, user_name, _ in users:
            cursor.execute(
                "INSERT OR REPLACE INTO league_members (league_code, telegram_id) VALUES (?, ?)",
                (code, telegram_id)
            )
        print(f"  + Added 4 members to {name}")
    
    print("\n[*] Creating matches...")
    match_id = 1000  # Start from high ID to avoid conflicts
    
    for code, league_name, _, _ in leagues:
        # Create 10-20 matches per league
        num_matches = random.randint(10, 20)
        
        for i in range(num_matches):
            # Random scores
            team1_score = random.randint(0, 5)
            team2_score = random.randint(0, 5)
            
            # Random date in last 30 days
            match_date = datetime.now() - timedelta(days=random.randint(1, 30))
            
            cursor.execute(
                "INSERT INTO matches (id, league_code, match_type, team1_score, team2_score, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (match_id, code, '2v2', team1_score, team2_score, match_date.strftime('%Y-%m-%d %H:%M:%S'))
            )
            
            # Assign 2 players per team (4 total per match)
            shuffled_users = [u[0] for u in users]
            random.shuffle(shuffled_users)
            
            # Team 1: first 2 users, Team 2: last 2 users
            for j, telegram_id in enumerate(shuffled_users):
                team_number = 1 if j < 2 else 2
                cursor.execute(
                    "INSERT INTO match_players (match_id, telegram_id, team_number) VALUES (?, ?, ?)",
                    (match_id, telegram_id, team_number)
                )
            
            match_id += 1
        
        print(f"  + Created {num_matches} matches for {league_name}")
    
    conn.commit()
    conn.close()
    
    print("\n[OK] Mock data created successfully!")
    print(f"   Database: {DB_PATH}")
    print(f"   Test user ID: 93205092")
    print(f"   Leagues: LEAGUE1, LEAGUE2, LEAGUE3")


if __name__ == "__main__":
    create_mock_data()

