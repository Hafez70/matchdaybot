"""League service for league-related operations"""
from typing import Optional, List
from ..models.league import League
from .database_service import DatabaseService


class LeagueService:
    """Service for league management"""
    
    def __init__(self, db: DatabaseService):
        self.db = db
    
    def get_league_by_code(self, code: str) -> Optional[League]:
        """Get league by code"""
        leagues = self.db.get_all_leagues()
        for league_data in leagues:
            if league_data['code'].upper() == code.upper():
                return League.from_dict(league_data)
        return None
    
    def create_league(self, name: str, owner_telegram_id: int) -> League:
        """Create a new league"""
        # Generate unique code
        code = self._generate_unique_code()
        
        # Create league
        league = League(
            code=code,
            name=name,
            owner_telegram_id=owner_telegram_id,
            members=[owner_telegram_id]  # Owner is automatically a member
        )
        
        self.db.add_league(code, name, owner_telegram_id)
        return league
    
    def _generate_unique_code(self) -> str:
        """Generate a unique league code"""
        while True:
            code = League.generate_code()
            if not self.get_league_by_code(code):
                return code
    
    def join_league(self, league_code: str, telegram_id: int) -> League:
        """Join a league"""
        league = self.get_league_by_code(league_code)
        if not league:
            raise ValueError("لیگ با این کد پیدا نشد!")
        
        # Add member to database
        self.db.add_league_member(league_code, telegram_id)
        
        # Update league object
        league.add_member(telegram_id)
        return league
    
    def get_user_leagues(self, telegram_id: int) -> List[League]:
        """Get all leagues a user is a member of"""
        leagues = self.db.get_all_leagues()
        user_leagues = []
        for league_data in leagues:
            league = League.from_dict(league_data)
            if league.is_member(telegram_id):
                user_leagues.append(league)
        return user_leagues
    
    def get_league_members_count(self, league_code: str) -> int:
        """Get number of members in a league"""
        league = self.get_league_by_code(league_code)
        if not league:
            return 0
        return len(league.members)
    
    def is_user_in_league(self, telegram_id: int, league_code: str) -> bool:
        """Check if user is in a specific league"""
        league = self.get_league_by_code(league_code)
        if not league:
            return False
        return league.is_member(telegram_id)
    
    def leave_league(self, league_code: str, telegram_id: int) -> None:
        """Leave a league"""
        league = self.get_league_by_code(league_code)
        if not league:
            raise ValueError("لیگ پیدا نشد!")
        
        if league.is_owner(telegram_id):
            raise ValueError("مالک لیگ نمی‌تواند لیگ را ترک کند!")
        
        if telegram_id in league.members:
            league.members.remove(telegram_id)
            self.db.update_league(league.code, league.to_dict())
    
    def delete_league(self, league_code: str, telegram_id: int) -> None:
        """Delete a league (only by owner)"""
        league = self.get_league_by_code(league_code)
        if not league:
            raise ValueError("لیگ پیدا نشد!")
        
        if not league.is_owner(telegram_id):
            raise ValueError("فقط مالک لیگ می‌تواند آن را حذف کند!")
        
        self.db.delete_league(league_code)

