"""FastAPI Backend for FIFA Bot Mini App"""
import os
import sqlite3
from datetime import datetime
from contextlib import contextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'database', 'fifa_bot.db')

app = FastAPI(
    title="MatchDay API",
    description="API for FIFA Bot Mini App",
    version="1.0.0"
)

# CORS middleware for Mini App
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your mini app domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============ Database Connection ============

@contextmanager
def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


# ============ Pydantic Models ============

class LeagueInfo(BaseModel):
    code: str
    name: str
    owner_telegram_id: int
    owner_name: str
    member_count: int
    archived: bool
    created_at: str


class PlayerStats(BaseModel):
    telegram_id: int
    name: str
    rank: int
    points: int
    matches: int
    wins: int
    losses: int
    draws: int
    goal_difference: int


class MatchInfo(BaseModel):
    id: int
    match_type: str
    team1: list[str]
    team2: list[str]
    team1_score: int
    team2_score: int
    created_at: str
    result_emoji: str


class UserInfo(BaseModel):
    telegram_id: int
    name: str
    created_at: str


# ============ API Routes ============

@app.get("/")
async def root():
    """Health check"""
    return {"status": "ok", "message": "MatchDay API is running 🎮⚽"}


@app.get("/api/league/{league_code}", response_model=LeagueInfo)
async def get_league_info(league_code: str):
    """Get league information"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Get league info
        cursor.execute("""
            SELECT l.*, u.name as owner_name
            FROM leagues l
            LEFT JOIN users u ON l.owner_telegram_id = u.telegram_id
            WHERE l.code = ?
        """, (league_code,))
        league = cursor.fetchone()
        
        if not league:
            raise HTTPException(status_code=404, detail="League not found")
        
        # Get member count
        cursor.execute(
            "SELECT COUNT(*) FROM league_members WHERE league_code = ?",
            (league_code,)
        )
        member_count = cursor.fetchone()[0]
        
        # Handle missing 'archived' column gracefully
        try:
            archived = bool(league['archived'])
        except (KeyError, IndexError):
            archived = False
        
        return LeagueInfo(
            code=league['code'],
            name=league['name'],
            owner_telegram_id=league['owner_telegram_id'],
            owner_name=league['owner_name'] or 'Unknown',
            member_count=member_count,
            archived=archived,
            created_at=league['created_at']
        )


@app.get("/api/league/{league_code}/leaderboard", response_model=list[PlayerStats])
async def get_leaderboard(
    league_code: str,
    user_id: Optional[int] = Query(None, description="Telegram user ID for filtering")
):
    """Get league leaderboard with 20% participation filter"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Check league exists
        cursor.execute("SELECT code FROM leagues WHERE code = ?", (league_code,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="League not found")
        
        # Get all members with their stats
        cursor.execute("""
            SELECT 
                u.telegram_id,
                u.name,
                COUNT(DISTINCT mp.match_id) as matches,
                COALESCE(SUM(CASE 
                    WHEN (mp.team_number = 1 AND m.team1_score > m.team2_score) OR
                         (mp.team_number = 2 AND m.team2_score > m.team1_score)
                    THEN 1 ELSE 0 END), 0) as wins,
                COALESCE(SUM(CASE 
                    WHEN (mp.team_number = 1 AND m.team1_score < m.team2_score) OR
                         (mp.team_number = 2 AND m.team2_score < m.team1_score)
                    THEN 1 ELSE 0 END), 0) as losses,
                COALESCE(SUM(CASE 
                    WHEN m.team1_score = m.team2_score THEN 1 ELSE 0 END), 0) as draws,
                COALESCE(SUM(CASE 
                    WHEN mp.team_number = 1 THEN m.team1_score - m.team2_score
                    ELSE m.team2_score - m.team1_score END), 0) as goal_difference
            FROM league_members lm
            JOIN users u ON lm.telegram_id = u.telegram_id
            LEFT JOIN match_players mp ON u.telegram_id = mp.telegram_id
            LEFT JOIN matches m ON mp.match_id = m.id AND m.league_code = ?
            WHERE lm.league_code = ?
            GROUP BY u.telegram_id, u.name
        """, (league_code, league_code))
        
        players = []
        for row in cursor.fetchall():
            points = row['wins'] - row['losses']
            players.append({
                'telegram_id': row['telegram_id'],
                'name': row['name'],
                'matches': row['matches'],
                'wins': row['wins'],
                'losses': row['losses'],
                'draws': row['draws'],
                'goal_difference': row['goal_difference'],
                'points': points
            })
        
        if not players:
            return []
        
        # Calculate max matches and filter
        max_matches = max(p['matches'] for p in players)
        min_threshold = int(max_matches * 0.20)
        
        filtered = []
        user_included = False
        
        for p in players:
            if p['matches'] >= min_threshold:
                filtered.append(p)
                if user_id and p['telegram_id'] == user_id:
                    user_included = True
            elif user_id and p['telegram_id'] == user_id:
                filtered.append(p)
                user_included = True
        
        # Sort by points, goal difference, wins
        filtered.sort(key=lambda x: (x['points'], x['goal_difference'], x['wins']), reverse=True)
        
        # Assign ranks
        result = []
        for i, p in enumerate(filtered, 1):
            result.append(PlayerStats(
                telegram_id=p['telegram_id'],
                name=p['name'],
                rank=i,
                points=p['points'],
                matches=p['matches'],
                wins=p['wins'],
                losses=p['losses'],
                draws=p['draws'],
                goal_difference=p['goal_difference']
            ))
        
        return result


@app.get("/api/league/{league_code}/matches", response_model=list[MatchInfo])
async def get_matches(
    league_code: str,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Get recent matches for a league"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Check league exists
        cursor.execute("SELECT code FROM leagues WHERE code = ?", (league_code,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="League not found")
        
        # Get matches
        cursor.execute("""
            SELECT id, match_type, team1_score, team2_score, created_at
            FROM matches
            WHERE league_code = ?
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """, (league_code, limit, offset))
        
        matches = []
        for match in cursor.fetchall():
            # Get team players
            cursor.execute("""
                SELECT u.name, mp.team_number
                FROM match_players mp
                JOIN users u ON mp.telegram_id = u.telegram_id
                WHERE mp.match_id = ?
            """, (match['id'],))
            
            team1 = []
            team2 = []
            for player in cursor.fetchall():
                if player['team_number'] == 1:
                    team1.append(player['name'])
                else:
                    team2.append(player['name'])
            
            # Determine result emoji
            if match['team1_score'] > match['team2_score']:
                result_emoji = "🏆"
            elif match['team1_score'] < match['team2_score']:
                result_emoji = "❌"
            else:
                result_emoji = "🤝"
            
            matches.append(MatchInfo(
                id=match['id'],
                match_type=match['match_type'],
                team1=team1,
                team2=team2,
                team1_score=match['team1_score'],
                team2_score=match['team2_score'],
                created_at=match['created_at'],
                result_emoji=result_emoji
            ))
        
        return matches


@app.get("/api/league/{league_code}/members", response_model=list[UserInfo])
async def get_members(league_code: str):
    """Get all league members"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Check league exists
        cursor.execute("SELECT code FROM leagues WHERE code = ?", (league_code,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="League not found")
        
        cursor.execute("""
            SELECT u.telegram_id, u.name, u.created_at
            FROM league_members lm
            JOIN users u ON lm.telegram_id = u.telegram_id
            WHERE lm.league_code = ?
            ORDER BY u.name
        """, (league_code,))
        
        return [
            UserInfo(
                telegram_id=row['telegram_id'],
                name=row['name'],
                created_at=row['created_at']
            )
            for row in cursor.fetchall()
        ]


@app.get("/api/league/{league_code}/player/{telegram_id}", response_model=PlayerStats)
async def get_player_stats(league_code: str, telegram_id: int):
    """Get specific player stats in a league"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Check league exists
        cursor.execute("SELECT code FROM leagues WHERE code = ?", (league_code,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="League not found")
        
        # Check user is member
        cursor.execute("""
            SELECT u.name FROM league_members lm
            JOIN users u ON lm.telegram_id = u.telegram_id
            WHERE lm.league_code = ? AND lm.telegram_id = ?
        """, (league_code, telegram_id))
        
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="Player not found in this league")
        
        # Get stats
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT mp.match_id) as matches,
                COALESCE(SUM(CASE 
                    WHEN (mp.team_number = 1 AND m.team1_score > m.team2_score) OR
                         (mp.team_number = 2 AND m.team2_score > m.team1_score)
                    THEN 1 ELSE 0 END), 0) as wins,
                COALESCE(SUM(CASE 
                    WHEN (mp.team_number = 1 AND m.team1_score < m.team2_score) OR
                         (mp.team_number = 2 AND m.team2_score < m.team1_score)
                    THEN 1 ELSE 0 END), 0) as losses,
                COALESCE(SUM(CASE 
                    WHEN m.team1_score = m.team2_score THEN 1 ELSE 0 END), 0) as draws,
                COALESCE(SUM(CASE 
                    WHEN mp.team_number = 1 THEN m.team1_score - m.team2_score
                    ELSE m.team2_score - m.team1_score END), 0) as goal_difference
            FROM match_players mp
            JOIN matches m ON mp.match_id = m.id AND m.league_code = ?
            WHERE mp.telegram_id = ?
        """, (league_code, telegram_id))
        
        stats = cursor.fetchone()
        points = stats['wins'] - stats['losses']
        
        # Get rank
        leaderboard = await get_leaderboard(league_code, telegram_id)
        rank = next((p.rank for p in leaderboard if p.telegram_id == telegram_id), 0)
        
        return PlayerStats(
            telegram_id=telegram_id,
            name=user['name'],
            rank=rank,
            points=points,
            matches=stats['matches'],
            wins=stats['wins'],
            losses=stats['losses'],
            draws=stats['draws'],
            goal_difference=stats['goal_difference']
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

