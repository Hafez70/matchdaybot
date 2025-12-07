import sqlite3

conn = sqlite3.connect('fifa_bot.db')
cursor = conn.cursor()

print('=' * 50)
print('=== USERS TABLE ===')
print('=' * 50)
cursor.execute('SELECT * FROM users')
users = cursor.fetchall()
columns = [desc[0] for desc in cursor.description]
print(f"Columns: {columns}")
print(f"Total users: {len(users)}\n")
for u in users:
    print(f"ID: {u[0]}, Name: {u[1]}, Created: {u[2]}")

print('\n' + '=' * 50)
print('=== LEAGUE_MEMBERS TABLE ===')
print('=' * 50)
cursor.execute('SELECT * FROM league_members')
members = cursor.fetchall()
columns = [desc[0] for desc in cursor.description]
print(f"Columns: {columns}")
print(f"Total members: {len(members)}\n")
for m in members:
    print(f"League: {m[0]}, User ID: {m[1]}, Joined: {m[2]}")

print('\n' + '=' * 50)
print('=== LEAGUES TABLE ===')
print('=' * 50)
cursor.execute('SELECT code, name, owner_telegram_id, created_at FROM leagues')
leagues = cursor.fetchall()
print(f"Total leagues: {len(leagues)}\n")
for league in leagues:
    print(f"Code: {league[0]}, Name: {league[1]}, Owner ID: {league[2]}, Created: {league[3]}")

print('\n' + '=' * 50)
print('=== ANALYSIS: Users vs League Members ===')
print('=' * 50)

# Get unique user IDs from users table
user_ids = set(u[0] for u in users)
# Get unique user IDs from league_members table
member_ids = set(m[1] for m in members)

print(f"\nUser IDs in users table: {sorted(user_ids)}")
print(f"User IDs in league_members table: {sorted(member_ids)}")

# Check for inconsistencies
missing_in_members = user_ids - member_ids
missing_in_users = member_ids - user_ids

if missing_in_members:
    print(f"\n⚠️ WARNING: Users in 'users' table but NOT in 'league_members': {missing_in_members}")
    for uid in missing_in_members:
        cursor.execute('SELECT name FROM users WHERE telegram_id = ?', (uid,))
        name = cursor.fetchone()[0]
        print(f"   - {name} (ID: {uid})")

if missing_in_users:
    print(f"\n❌ ERROR: User IDs in 'league_members' but NOT in 'users' table: {missing_in_users}")
    print("   This is a data integrity issue!")

if not missing_in_members and not missing_in_users:
    print("\n✅ All good! All league members exist in users table.")

conn.close()

