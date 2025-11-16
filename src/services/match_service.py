"""Match service for match-related operations"""
from typing import List, Dict, Optional
from ..models.match import Match
from .database_service import DatabaseService


class MatchService:
    """Service for match management"""
    
    def __init__(self, db: DatabaseService):
        self.db = db
    
    def create_match(
        self,
        league_code: str,
        team1: List[int],
        team2: List[int],
        team1_score: int,
        team2_score: int
    ) -> Match:
        """Create a new match"""
        # Determine match type
        match_type = f"{len(team1)}v{len(team2)}"
        
        # Create match
        match = Match(
            league_code=league_code,
            match_type=match_type,
            team1=team1,
            team2=team2,
            result={'team1': team1_score, 'team2': team2_score}
        )
        
        match_id = self.db.add_match(match.to_dict())
        match.match_id = match_id
        return match
    
    def get_matches_by_league(self, league_code: str) -> List[Match]:
        """Get all matches in a league"""
        matches = self.db.get_all_matches()
        league_matches = []
        for match_data in matches:
            if match_data.get('league_code') == league_code:
                league_matches.append(Match.from_dict(match_data))
        return league_matches
    
    def get_matches_by_player(self, telegram_id: int, league_code: Optional[str] = None) -> List[Match]:
        """Get all matches a player participated in"""
        matches = self.db.get_all_matches()
        player_matches = []
        for match_data in matches:
            match = Match.from_dict(match_data)
            if match.is_player_in_match(telegram_id):
                if league_code is None or match.league_code == league_code:
                    player_matches.append(match)
        return player_matches
    
    def get_player_stats(self, telegram_id: int, league_code: str) -> Dict:
        """Get player statistics in a specific league"""
        matches = self.get_matches_by_player(telegram_id, league_code)
        
        wins = 0
        losses = 0
        draws = 0
        total_goals_for = 0
        total_goals_against = 0
        
        for match in matches:
            player_team = match.get_player_team(telegram_id)
            if not player_team:
                continue
            
            team_goals = match.result[player_team]
            opponent_team = 'team2' if player_team == 'team1' else 'team1'
            opponent_goals = match.result[opponent_team]
            
            total_goals_for += team_goals
            total_goals_against += opponent_goals
            
            if team_goals > opponent_goals:
                wins += 1
            elif team_goals < opponent_goals:
                losses += 1
            else:
                draws += 1
        
        return {
            'total_matches': len(matches),
            'wins': wins,
            'losses': losses,
            'draws': draws,
            'goals_for': total_goals_for,
            'goals_against': total_goals_against,
            'goal_difference': total_goals_for - total_goals_against
        }
    
    def get_recent_matches(self, league_code: str, limit: int = 10) -> List[Match]:
        """Get recent matches in a league"""
        matches = self.get_matches_by_league(league_code)
        return sorted(matches, key=lambda m: m.datetime, reverse=True)[:limit]
    
    def get_league_leaderboard(self, league_code: str, user_service) -> List[Dict]:
        """Get leaderboard for a league"""
        from .user_service import UserService
        
        users = user_service.get_users_in_league(league_code)
        leaderboard = []
        
        for user in users:
            stats = self.get_player_stats(user.telegram_id, league_code)
            if stats['total_matches'] > 0:
                leaderboard.append({
                    'name': user.name,
                    'telegram_id': user.telegram_id,
                    **stats
                })
        
        # Sort by wins, then by goal difference
        leaderboard.sort(key=lambda x: (x['wins'], x['goal_difference']), reverse=True)
        return leaderboard

