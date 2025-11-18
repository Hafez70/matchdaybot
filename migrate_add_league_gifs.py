#!/usr/bin/env python3
"""
Migration script to add GIF fields to leagues table
Run this on cPanel after pulling the latest code
"""
import sqlite3
import sys

def migrate_database(db_path='fifa_bot.db'):
    """Add winner_gif and loser_gif columns to leagues table"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔄 Starting database migration...")
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(leagues)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'winner_gif' in columns and 'loser_gif' in columns:
            print("✅ Columns already exist. No migration needed.")
            conn.close()
            return
        
        # Add winner_gif column if it doesn't exist
        if 'winner_gif' not in columns:
            print("Adding winner_gif column...")
            cursor.execute("""
                ALTER TABLE leagues 
                ADD COLUMN winner_gif TEXT DEFAULT NULL
            """)
            print("✅ winner_gif column added")
        
        # Add loser_gif column if it doesn't exist
        if 'loser_gif' not in columns:
            print("Adding loser_gif column...")
            cursor.execute("""
                ALTER TABLE leagues 
                ADD COLUMN loser_gif TEXT DEFAULT NULL
            """)
            print("✅ loser_gif column added")
        
        conn.commit()
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

