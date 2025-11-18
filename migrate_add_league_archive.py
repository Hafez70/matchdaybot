#!/usr/bin/env python3
"""
Migration script to add archive functionality to leagues table
Run this on cPanel after pulling the latest code
"""
import sqlite3
import sys

def migrate_database(db_path='fifa_bot.db'):
    """Add is_archived column to leagues table"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔄 Starting database migration for archive feature...")
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(leagues)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'is_archived' in columns:
            print("✅ is_archived column already exists. No migration needed.")
            conn.close()
            return
        
        # Add is_archived column
        print("Adding is_archived column...")
        cursor.execute("""
            ALTER TABLE leagues 
            ADD COLUMN is_archived INTEGER DEFAULT 0
        """)
        
        conn.commit()
        print("✅ is_archived column added")
        
        print("\n🎉 Migration completed successfully!")
        print("\n📊 Updated schema:")
        cursor.execute("PRAGMA table_info(leagues)")
        for col in cursor.fetchall():
            print(f"  - {col[1]} ({col[2]})")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    db_path = sys.argv[1] if len(sys.argv) > 1 else 'fifa_bot.db'
    migrate_database(db_path)

