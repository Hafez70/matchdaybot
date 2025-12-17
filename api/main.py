"""FastAPI Backend for FIFA Bot Mini App"""
import os
import sys
import sqlite3
import logging
import traceback
from datetime import datetime
from contextlib import contextmanager
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from telegram_auth import TelegramUser, get_current_user, get_optional_user

# ============ Logging Setup ============
LOG_FILE = os.path.join(os.path.dirname(__file__), 'api_debug.log')
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE, encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)
logger.info(f"=== API Starting, log file: {LOG_FILE} ===")

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'config.env'))

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'database', 'fifa_bot.db')
logger.info(f"Database path: {DB_PATH}")
logger.info(f"Database exists: {os.path.exists(DB_PATH)}")

app = FastAPI(
    title="MatchDay API",
    description="API for FIFA Bot Mini App",
    version="1.0.0"
)


# ============ Exception Handler ============
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch all exceptions and log them with full traceback"""
    error_msg = f"Internal Server Error: {str(exc)}"
    tb = traceback.format_exc()
    
    logger.error(f"🔴 Error on {request.method} {request.url}")
    logger.error(f"🔴 Exception: {type(exc).__name__}: {exc}")
    logger.error(f"🔴 Traceback:\n{tb}")
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": str(exc),
            "type": type(exc).__name__,
            "path": str(request.url.path)
        }
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
    rank: Optional[int]  # None for unqualified players
    points: int
    matches: int
    wins: int
    losses: int
    draws: int
    goal_difference: int
    qualified: bool = True  # Whether player meets 20% threshold


class LeaderboardResponse(BaseModel):
    qualified: list[PlayerStats]
    unqualified: list[PlayerStats]
    min_matches: int  # Minimum matches needed to qualify


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


class UserLeague(BaseModel):
    code: str
    name: str
    member_count: int
    is_owner: bool
    my_points: int
    my_rank: Optional[int]  # None if not qualified
    my_matches: int
    my_wins: int
    my_losses: int
    my_draws: int
    my_goal_difference: int
    qualified: bool  # Whether user meets 20% threshold
    matches_needed: int  # How many more matches needed (0 if qualified)
    min_matches: int  # Minimum matches required (20% threshold)


# ============ API Routes ============

@app.get("/")
def root():
    """Health check"""
    return {"status": "ok", "message": "MatchDay API is running"}


@app.get("/api/me")
async def get_me(user: TelegramUser = Depends(get_current_user)):
    """Get current authenticated user info"""
    return {
        "telegram_id": user.id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "username": user.username,
        "is_premium": user.is_premium
    }


@app.get("/api/me/leagues", response_model=list)
async def get_my_leagues(user: TelegramUser = Depends(get_current_user)):
    """Get leagues for authenticated user - secure version"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Check user exists
        cursor.execute("SELECT name FROM users WHERE telegram_id = ?", (user.id,))
        db_user = cursor.fetchone()
        if not db_user:
            return []
        
        # Get user's leagues
        cursor.execute("""
            SELECT l.code, l.name, l.owner_telegram_id,
                   (SELECT COUNT(*) FROM league_members WHERE league_code = l.code) as member_count
            FROM leagues l
            JOIN league_members lm ON l.code = lm.league_code
            WHERE lm.telegram_id = ?
            ORDER BY l.name
        """, (user.id,))
        
        leagues = []
        for row in cursor.fetchall():
            # Get user's match count and stats
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
                        WHEN m.team1_score = m.team2_score 
                        THEN 1 ELSE 0 END), 0) as draws,
                    COALESCE(SUM(CASE 
                        WHEN mp.team_number = 1 THEN m.team1_score - m.team2_score
                        ELSE m.team2_score - m.team1_score END), 0) as goal_difference
                FROM match_players mp
                JOIN matches m ON mp.match_id = m.id AND m.league_code = ?
                WHERE mp.telegram_id = ?
            """, (row['code'], user.id))
            stats = cursor.fetchone()
            my_matches = stats['matches'] or 0
            my_wins = stats['wins'] or 0
            my_losses = stats['losses'] or 0
            my_draws = stats['draws'] or 0
            my_goal_difference = stats['goal_difference'] or 0
            my_points = my_wins - my_losses
            
            # Get max matches in league (for 20% threshold)
            cursor.execute("""
                SELECT MAX(match_count) as max_matches FROM (
                    SELECT COUNT(DISTINCT mp.match_id) as match_count
                    FROM match_players mp
                    JOIN matches m ON mp.match_id = m.id AND m.league_code = ?
                    GROUP BY mp.telegram_id
                )
            """, (row['code'],))
            max_result = cursor.fetchone()
            max_matches = max_result['max_matches'] or 0
            
            # Calculate threshold (20% of max)
            min_threshold = int(max_matches * 0.20)
            qualified = my_matches >= min_threshold if min_threshold > 0 else True
            matches_needed = max(0, min_threshold - my_matches) if not qualified else 0
            
            # Get rank only if qualified
            my_rank = None
            if qualified:
                # Count players with more points who are also qualified
                cursor.execute("""
                    SELECT COUNT(*) + 1 as rank
                    FROM (
                        SELECT mp.telegram_id,
                            COUNT(DISTINCT mp.match_id) as match_count,
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
                        HAVING match_count >= ? AND points > ?
                    )
                """, (row['code'], min_threshold, my_points))
                rank_result = cursor.fetchone()
                my_rank = rank_result['rank'] if rank_result else 1
            
            leagues.append({
                "code": row['code'],
                "name": row['name'],
                "member_count": row['member_count'],
                "is_owner": row['owner_telegram_id'] == user.id,
                "my_points": my_points,
                "my_rank": my_rank,
                "my_matches": my_matches,
                "my_wins": my_wins,
                "my_losses": my_losses,
                "my_draws": my_draws,
                "my_goal_difference": my_goal_difference,
                "qualified": qualified,
                "matches_needed": matches_needed,
                "min_matches": min_threshold
            })
        
        return leagues


@app.get("/api/user/{telegram_id}")
async def get_user_info(telegram_id: int):
    """Get user information"""
    logger.info(f"📥 get_user_info called with telegram_id={telegram_id}")
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT telegram_id, name, created_at FROM users WHERE telegram_id = ?", (telegram_id,))
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return {
            "telegram_id": user['telegram_id'],
            "name": user['name'],
            "created_at": user['created_at']
        }


@app.get("/api/user/{telegram_id}/leagues", response_model=list[UserLeague])
async def get_user_leagues(telegram_id: int):
    """Get all leagues for a user"""
    logger.info(f"📥 get_user_leagues called with telegram_id={telegram_id}")
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Check user exists
            cursor.execute("SELECT name FROM users WHERE telegram_id = ?", (telegram_id,))
            user = cursor.fetchone()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Get user's leagues
            cursor.execute("""
                SELECT l.code, l.name, l.owner_telegram_id,
                       (SELECT COUNT(*) FROM league_members WHERE league_code = l.code) as member_count
                FROM leagues l
                JOIN league_members lm ON l.code = lm.league_code
                WHERE lm.telegram_id = ?
                ORDER BY l.name
            """, (telegram_id,))
            
            leagues = []
            for row in cursor.fetchall():
                # Calculate user's points and rank in this league
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
                
                # Get rank (simplified - just count players with more points)
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
                
                leagues.append(UserLeague(
                    code=row['code'],
                    name=row['name'],
                    member_count=row['member_count'],
                    is_owner=row['owner_telegram_id'] == telegram_id,
                    my_points=my_points,
                    my_rank=my_rank
                ))
            
            return leagues
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"🔴 Error in get_user_leagues: {type(e).__name__}: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


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


@app.get("/api/league/{league_code}/leaderboard", response_model=LeaderboardResponse)
async def get_leaderboard(
    league_code: str,
    user_id: Optional[int] = Query(None, description="Telegram user ID for filtering")
):
    """Get league leaderboard with qualified and unqualified sections"""
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
            return LeaderboardResponse(qualified=[], unqualified=[], min_matches=0)
        
        # Calculate max matches and threshold
        max_matches = max(p['matches'] for p in players)
        min_threshold = int(max_matches * 0.20)
        
        # Separate qualified and unqualified
        qualified_players = []
        unqualified_players = []
        
        for p in players:
            if p['matches'] >= min_threshold:
                qualified_players.append(p)
            else:
                unqualified_players.append(p)
        
        # Sort qualified by points, goal difference, wins
        qualified_players.sort(key=lambda x: (x['points'], x['goal_difference'], x['wins']), reverse=True)
        
        # Sort unqualified by matches (most matches first)
        unqualified_players.sort(key=lambda x: x['matches'], reverse=True)
        
        # Build qualified list with ranks
        qualified_result = []
        for i, p in enumerate(qualified_players, 1):
            qualified_result.append(PlayerStats(
                telegram_id=p['telegram_id'],
                name=p['name'],
                rank=i,
                points=p['points'],
                matches=p['matches'],
                wins=p['wins'],
                losses=p['losses'],
                draws=p['draws'],
                goal_difference=p['goal_difference'],
                qualified=True
            ))
        
        # Build unqualified list (no rank)
        unqualified_result = []
        for p in unqualified_players:
            unqualified_result.append(PlayerStats(
                telegram_id=p['telegram_id'],
                name=p['name'],
                rank=None,
                points=p['points'],
                matches=p['matches'],
                wins=p['wins'],
                losses=p['losses'],
                draws=p['draws'],
                goal_difference=p['goal_difference'],
                qualified=False
            ))
        
        return LeaderboardResponse(
            qualified=qualified_result,
            unqualified=unqualified_result,
            min_matches=min_threshold
        )


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

