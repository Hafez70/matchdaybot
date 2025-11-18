"""SQLite Database Service"""
import sqlite3
import logging
from typing import List, Dict, Optional
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class SQLiteDatabaseService:
    """SQLite database service for FIFA bot"""
    
    def __init__(self, db_path: str = 'fifa_bot.db'):
        self.db_path = db_path
        self._init_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Access columns by name
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def _init_database(self):
        """Initialize database schema"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Enable foreign keys
            cursor.execute("PRAGMA foreign_keys = ON")
            
            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    telegram_id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Leagues table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS leagues (
                    code TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    owner_telegram_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (owner_telegram_id) REFERENCES users(telegram_id)
                )
            """)
            
            # League members (many-to-many)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS league_members (
                    league_code TEXT NOT NULL,
                    telegram_id INTEGER NOT NULL,
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (league_code, telegram_id),
                    FOREIGN KEY (league_code) REFERENCES leagues(code) ON DELETE CASCADE,
                    FOREIGN KEY (telegram_id) REFERENCES users(telegram_id) ON DELETE CASCADE
                )
            """)
            
            # Matches table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS matches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    league_code TEXT NOT NULL,
                    match_type TEXT NOT NULL,
                    team1_score INTEGER NOT NULL,
                    team2_score INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (league_code) REFERENCES leagues(code) ON DELETE CASCADE
                )
            """)
            
            # Match players table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS match_players (
                    match_id INTEGER NOT NULL,
                    telegram_id INTEGER NOT NULL,
                    team_number INTEGER NOT NULL,
                    PRIMARY KEY (match_id, telegram_id),
                    FOREIGN KEY (match_id) REFERENCES matches(id) ON DELETE CASCADE,
                    FOREIGN KEY (telegram_id) REFERENCES users(telegram_id) ON DELETE CASCADE
                )
            """)
            
            # Create indexes for performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_league_members_telegram 
                ON league_members(telegram_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_matches_league 
                ON matches(league_code)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_matches_created 
                ON matches(created_at DESC)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_match_players_telegram 
                ON match_players(telegram_id)
            """)
            
            logger.info("Database initialized successfully")
    
    # User operations
    def add_user(self, telegram_id: int, name: str) -> None:
        """Add a new user"""
        with self.get_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO users (telegram_id, name) VALUES (?, ?)",
                (telegram_id, name)
            )
    
    def get_user(self, telegram_id: int) -> Optional[Dict]:
        """Get user by telegram ID"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM users WHERE telegram_id = ?",
                (telegram_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_user_by_name(self, name: str) -> Optional[Dict]:
        """Get user by name"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM users WHERE LOWER(name) = LOWER(?)",
                (name,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def update_user_name(self, telegram_id: int, new_name: str) -> None:
        """Update user's name"""
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE users SET name = ? WHERE telegram_id = ?",
                (new_name, telegram_id)
            )
    
    def get_all_users(self) -> List[Dict]:
        """Get all users"""
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM users ORDER BY name")
            return [dict(row) for row in cursor.fetchall()]
    
    # League operations
    def get_all_leagues(self) -> List[Dict]:
        """Get all leagues"""
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM leagues ORDER BY created_at DESC")
            leagues = []
            for row in cursor.fetchall():
                league = dict(row)
                
                # Get members
                cursor2 = conn.execute(
                    "SELECT telegram_id FROM league_members WHERE league_code = ?",
                    (league['code'],)
                )
                league['members'] = [r['telegram_id'] for r in cursor2.fetchall()]
                leagues.append(league)
            
            return leagues
    def add_league(self, code: str, name: str, owner_telegram_id: int) -> None:
        """Create a new league"""
        with self.get_connection() as conn:
            conn.execute(
                "INSERT INTO leagues (code, name, owner_telegram_id) VALUES (?, ?, ?)",
                (code, name, owner_telegram_id)
            )
            # Add owner as member
            conn.execute(
                "INSERT INTO league_members (league_code, telegram_id) VALUES (?, ?)",
                (code, owner_telegram_id)
            )
    
    def get_league(self, code: str) -> Optional[Dict]:
        """Get league by code"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM leagues WHERE UPPER(code) = UPPER(?)",
                (code,)
            )
            row = cursor.fetchone()
            if not row:
                return None
            
            league = dict(row)
            
            # Get members
            cursor = conn.execute(
                "SELECT telegram_id FROM league_members WHERE league_code = ?",
                (code,)
            )
            league['members'] = [row['telegram_id'] for row in cursor.fetchall()]
            
            return league
    
    def add_league_member(self, league_code: str, telegram_id: int) -> None:
        """Add member to league"""
        with self.get_connection() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO league_members (league_code, telegram_id) VALUES (?, ?)",
                (league_code, telegram_id)
            )
    
    def get_user_leagues(self, telegram_id: int) -> List[Dict]:
        """Get all leagues a user is member of"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT l.* FROM leagues l
                JOIN league_members lm ON l.code = lm.league_code
                WHERE lm.telegram_id = ?
                ORDER BY l.created_at DESC
            """, (telegram_id,))
            
            leagues = []
            for row in cursor.fetchall():
                league = dict(row)
                
                # Get members
                cursor2 = conn.execute(
                    "SELECT telegram_id FROM league_members WHERE league_code = ?",
                    (league['code'],)
                )
                league['members'] = [r['telegram_id'] for r in cursor2.fetchall()]
                leagues.append(league)
            
            return leagues
    
    def get_league_members(self, league_code: str) -> List[int]:
        """Get all member telegram IDs for a league"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT telegram_id FROM league_members WHERE league_code = ?",
                (league_code,)
            )
            return [row['telegram_id'] for row in cursor.fetchall()]
    
    # Match operations
    def get_all_matches(self) -> List[Dict]:
        """Get all matches"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM matches 
                ORDER BY created_at DESC
            """)
            
            matches = []
            for row in cursor.fetchall():
                match = dict(row)
                match['datetime'] = match['created_at']  # Compatibility
                
                # Get team players
                cursor2 = conn.execute("""
                    SELECT telegram_id, team_number 
                    FROM match_players 
                    WHERE match_id = ?
                """, (match['id'],))
                
                team1 = []
                team2 = []
                for player_row in cursor2.fetchall():
                    if player_row['team_number'] == 1:
                        team1.append(player_row['telegram_id'])
                    else:
                        team2.append(player_row['telegram_id'])
                
                match['team1'] = team1
                match['team2'] = team2
                match['result'] = {
                    'team1': match['team1_score'],
                    'team2': match['team2_score']
                }
                
                matches.append(match)
            
            return matches
    
    def add_match(self, league_code: str, match_type: str, team1: List[int], 
                  team2: List[int], team1_score: int, team2_score: int) -> int:
        """Add a match and return its ID"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO matches (league_code, match_type, team1_score, team2_score)
                VALUES (?, ?, ?, ?)
            """, (league_code, match_type, team1_score, team2_score))
            
            match_id = cursor.lastrowid
            
            # Add team 1 players
            for telegram_id in team1:
                conn.execute(
                    "INSERT INTO match_players (match_id, telegram_id, team_number) VALUES (?, ?, ?)",
                    (match_id, telegram_id, 1)
                )
            
            # Add team 2 players
            for telegram_id in team2:
                conn.execute(
                    "INSERT INTO match_players (match_id, telegram_id, team_number) VALUES (?, ?, ?)",
                    (match_id, telegram_id, 2)
                )
            
            return match_id
    
    def get_matches_by_league(self, league_code: str) -> List[Dict]:
        """Get all matches in a league"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM matches 
                WHERE league_code = ? 
                ORDER BY created_at DESC
            """, (league_code,))
            
            matches = []
            for row in cursor.fetchall():
                match = dict(row)
                match['datetime'] = match['created_at']  # Compatibility
                
                # Get team players
                cursor2 = conn.execute("""
                    SELECT telegram_id, team_number 
                    FROM match_players 
                    WHERE match_id = ?
                """, (match['id'],))
                
                team1 = []
                team2 = []
                for player_row in cursor2.fetchall():
                    if player_row['team_number'] == 1:
                        team1.append(player_row['telegram_id'])
                    else:
                        team2.append(player_row['telegram_id'])
                
                match['team1'] = team1
                match['team2'] = team2
                match['result'] = {
                    'team1': match['team1_score'],
                    'team2': match['team2_score']
                }
                
                matches.append(match)
            
            return matches
    
    def get_matches_by_player(self, telegram_id: int, league_code: Optional[str] = None) -> List[Dict]:
        """Get all matches for a player"""
        with self.get_connection() as conn:
            if league_code:
                cursor = conn.execute("""
                    SELECT DISTINCT m.* FROM matches m
                    JOIN match_players mp ON m.id = mp.match_id
                    WHERE mp.telegram_id = ? AND m.league_code = ?
                    ORDER BY m.created_at DESC
                """, (telegram_id, league_code))
            else:
                cursor = conn.execute("""
                    SELECT DISTINCT m.* FROM matches m
                    JOIN match_players mp ON m.id = mp.match_id
                    WHERE mp.telegram_id = ?
                    ORDER BY m.created_at DESC
                """, (telegram_id,))
            
            matches = []
            for row in cursor.fetchall():
                match = dict(row)
                match['datetime'] = match['created_at']
                
                # Get team players
                cursor2 = conn.execute("""
                    SELECT telegram_id, team_number 
                    FROM match_players 
                    WHERE match_id = ?
                """, (match['id'],))
                
                team1 = []
                team2 = []
                for player_row in cursor2.fetchall():
                    if player_row['team_number'] == 1:
                        team1.append(player_row['telegram_id'])
                    else:
                        team2.append(player_row['telegram_id'])
                
                match['team1'] = team1
                match['team2'] = team2
                match['result'] = {
                    'team1': match['team1_score'],
                    'team2': match['team2_score']
                }
                
                matches.append(match)
            
            return matches
    
    def update_match_score(self, match_id: int, team1_score: int, team2_score: int) -> bool:
        """Update match score"""
        try:
            with self.get_connection() as conn:
                conn.execute("""
                    UPDATE matches 
                    SET team1_score = ?, team2_score = ?
                    WHERE id = ?
                """, (team1_score, team2_score, match_id))
                return True
        except Exception as e:
            logger.error(f"Error updating match score: {e}")
            return False
    
    def delete_match(self, match_id: int) -> bool:
        """Delete a match and its associated players"""
        try:
            with self.get_connection() as conn:
                # Delete match players first (foreign key)
                conn.execute("DELETE FROM match_players WHERE match_id = ?", (match_id,))
                # Delete match
                conn.execute("DELETE FROM matches WHERE id = ?", (match_id,))
                return True
        except Exception as e:
            logger.error(f"Error deleting match: {e}")
            return False
