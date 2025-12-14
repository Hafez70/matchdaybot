"""Debug script to test the API endpoint"""
import os
import sys
import traceback

# Fix encoding for Windows
sys.stdout.reconfigure(encoding='utf-8')

# Add the api directory to path
sys.path.insert(0, os.path.dirname(__file__))

from main import get_db, logger, UserLeague

telegram_id = 93205092

print(f"\n{'='*50}")
print(f"Testing get_user_leagues for telegram_id={telegram_id}")
print(f"{'='*50}\n")

try:
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Step 1: Check user exists
        print("Step 1: Check user exists...")
        cursor.execute("SELECT name FROM users WHERE telegram_id = ?", (telegram_id,))
        user = cursor.fetchone()
        if user:
            print(f"  ✅ User found: {user['name']}")
        else:
            print(f"  ❌ User not found!")
            sys.exit(1)
        
        # Step 2: Get user's leagues
        print("\nStep 2: Get user's leagues...")
        cursor.execute("""
            SELECT l.code, l.name, l.owner_telegram_id,
                   (SELECT COUNT(*) FROM league_members WHERE league_code = l.code) as member_count
            FROM leagues l
            JOIN league_members lm ON l.code = lm.league_code
            WHERE lm.telegram_id = ?
            ORDER BY l.name
        """, (telegram_id,))
        
        leagues_raw = cursor.fetchall()
        print(f"  ✅ Found {len(leagues_raw)} leagues")
        
        # Step 3: Process each league
        print("\nStep 3: Process each league...")
        leagues = []
        for i, row in enumerate(leagues_raw):
            print(f"\n  League {i+1}: {row['code']} - {row['name']}")
            
            # Calculate points
            print("    Calculating points...")
            cursor.execute("""
                SELECT 
                    COALESCE(SUM(CASE 
                        WHEN (mp.team_number = 1 AND m.team1_score > m.team2_score) OR
                             (mp.team_number = 2 AND m.team2_score > m.team1_score)
                        THEN 1 ELSE 0 END), 0) as wins,
                    COALESCE(SUM(CASE 
                        WHEN (mp.team_number = 1 AND m.team1_score < m.team2_score) OR
                             (mp.team_number = 2 AND m.team2_score < m.team1_score)
                        THEN 1 ELSE 0 END), 0) as losses
                FROM match_players mp
                JOIN matches m ON mp.match_id = m.id AND m.league_code = ?
                WHERE mp.telegram_id = ?
            """, (row['code'], telegram_id))
            stats = cursor.fetchone()
            my_points = (stats['wins'] or 0) - (stats['losses'] or 0)
            print(f"    ✅ Points: {my_points} (W:{stats['wins']} L:{stats['losses']})")
            
            # Get rank
            print("    Calculating rank...")
            cursor.execute("""
                SELECT COUNT(*) + 1 as rank
                FROM (
                    SELECT mp.telegram_id,
                        SUM(CASE 
                            WHEN (mp.team_number = 1 AND m.team1_score > m.team2_score) OR
                                 (mp.team_number = 2 AND m.team2_score > m.team1_score)
                            THEN 1 ELSE 0 END) -
                        SUM(CASE 
                            WHEN (mp.team_number = 1 AND m.team1_score < m.team2_score) OR
                                 (mp.team_number = 2 AND m.team2_score < m.team1_score)
                            THEN 1 ELSE 0 END) as points
                    FROM match_players mp
                    JOIN matches m ON mp.match_id = m.id AND m.league_code = ?
                    GROUP BY mp.telegram_id
                    HAVING points > ?
                )
            """, (row['code'], my_points))
            rank_result = cursor.fetchone()
            my_rank = rank_result['rank'] if rank_result else 1
            print(f"    ✅ Rank: #{my_rank}")
            
            # Create UserLeague object
            print("    Creating UserLeague object...")
            league_obj = UserLeague(
                code=row['code'],
                name=row['name'],
                member_count=row['member_count'],
                is_owner=row['owner_telegram_id'] == telegram_id,
                my_points=my_points,
                my_rank=my_rank
            )
            leagues.append(league_obj)
            print(f"    ✅ Created: {league_obj}")
        
        print(f"\n{'='*50}")
        print(f"✅ SUCCESS! Processed {len(leagues)} leagues")
        print(f"{'='*50}\n")
        
except Exception as e:
    print(f"\n{'='*50}")
    print(f"❌ ERROR: {type(e).__name__}: {e}")
    print(f"{'='*50}")
    traceback.print_exc()

