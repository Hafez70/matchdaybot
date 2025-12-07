"""
Fix data integrity issue: Add missing users to users table
"""
import sqlite3
from datetime import datetime

conn = sqlite3.connect('fifa_bot.db')
cursor = conn.cursor()

print("🔍 Checking for orphaned league members...")

# Find user IDs in league_members but not in users
cursor.execute('''
    SELECT DISTINCT lm.telegram_id, lm.joined_at
    FROM league_members lm
    LEFT JOIN users u ON lm.telegram_id = u.telegram_id
    WHERE u.telegram_id IS NULL
''')

orphaned_members = cursor.fetchall()

if not orphaned_members:
    print("✅ No orphaned members found! Data integrity is OK.")
    conn.close()
    exit(0)

print(f"⚠️ Found {len(orphaned_members)} orphaned member(s):")
for member in orphaned_members:
    print(f"   - User ID: {member[0]}, Joined: {member[1]}")

print("\n🔧 Fixing by adding them to users table...")

for telegram_id, joined_at in orphaned_members:
    # Use a placeholder name (they can change it later)
    name = f"User_{telegram_id}"
    created_at = joined_at or datetime.now().isoformat()
    
    cursor.execute('''
        INSERT INTO users (telegram_id, name, created_at)
        VALUES (?, ?, ?)
    ''', (telegram_id, name, created_at))
    
    print(f"   ✓ Added user {telegram_id} with name '{name}'")

conn.commit()

# Verify fix
cursor.execute('''
    SELECT DISTINCT lm.telegram_id
    FROM league_members lm
    LEFT JOIN users u ON lm.telegram_id = u.telegram_id
    WHERE u.telegram_id IS NULL
''')

remaining_orphans = cursor.fetchall()

if remaining_orphans:
    print(f"\n❌ Still have {len(remaining_orphans)} orphaned members!")
else:
    print("\n✅ All fixed! Data integrity restored.")

conn.close()

