"""User service for user-related operations"""
from typing import Optional, List
from ..models.user import User
from .database_service import DatabaseService


class UserService:
    """Service for user management"""
    
    def __init__(self, db: DatabaseService):
        self.db = db
    
    def get_user_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Get user by telegram ID"""
        users = self.db.get_all_users()
        for user_data in users:
            if user_data['telegram_id'] == telegram_id:
                return User.from_dict(user_data)
        return None
    
    def get_user_by_name(self, name: str) -> Optional[User]:
        """Get user by name (case-insensitive)"""
        users = self.db.get_all_users()
        for user_data in users:
            if user_data['name'].lower() == name.lower():
                return User.from_dict(user_data)
        return None
    
    def is_user_registered(self, telegram_id: int) -> bool:
        """Check if user is registered"""
        return self.get_user_by_telegram_id(telegram_id) is not None
    
    def register_user(self, telegram_id: int, name: str) -> User:
        """Register a new user"""
        # Check if user already exists
        existing = self.get_user_by_telegram_id(telegram_id)
        if existing:
            return existing
        
        # Check if name is taken
        name_taken = self.get_user_by_name(name)
        if name_taken:
            raise ValueError(f"نام '{name}' قبلاً توسط کاربر دیگری استفاده شده است!")
        
        # Create new user
        user = User(telegram_id=telegram_id, name=name)
        self.db.add_user(user.to_dict())
        return user
    
    def update_user_name(self, telegram_id: int, new_name: str) -> User:
        """Update user's name"""
        user = self.get_user_by_telegram_id(telegram_id)
        if not user:
            raise ValueError("کاربر پیدا نشد!")
        
        # Check if new name is taken by someone else
        existing = self.get_user_by_name(new_name)
        if existing and existing.telegram_id != telegram_id:
            raise ValueError(f"نام '{new_name}' قبلاً توسط کاربر دیگری استفاده شده است!")
        
        user.name = new_name
        self.db.update_user(telegram_id, user.to_dict())
        return user
    
    def add_league_to_user(self, telegram_id: int, league_code: str) -> None:
        """Add a league to user's leagues"""
        user = self.get_user_by_telegram_id(telegram_id)
        if not user:
            raise ValueError("کاربر پیدا نشد!")
        
        user.add_league(league_code)
        self.db.update_user(telegram_id, user.to_dict())
    
    def get_users_in_league(self, league_code: str) -> List[User]:
        """Get all users in a specific league"""
        users = self.db.get_all_users()
        league_users = []
        for user_data in users:
            user = User.from_dict(user_data)
            if user.is_in_league(league_code):
                league_users.append(user)
        return league_users
    
    def get_all_users(self) -> List[User]:
        """Get all registered users"""
        users = self.db.get_all_users()
        return [User.from_dict(u) for u in users]

