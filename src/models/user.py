"""User model"""
from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime


@dataclass
class User:
    """Represents a registered user/player"""
    
    telegram_id: int
    name: str
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    leagues: List[str] = field(default_factory=list)  # List of league codes
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'telegram_id': self.telegram_id,
            'name': self.name,
            'created_at': self.created_at,
            'leagues': self.leagues
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'User':
        """Create User from dictionary"""
        return cls(
            telegram_id=data['telegram_id'],
            name=data['name'],
            created_at=data.get('created_at', datetime.now().isoformat()),
            leagues=data.get('leagues', [])
        )
    
    def add_league(self, league_code: str) -> None:
        """Add user to a league"""
        if league_code not in self.leagues:
            self.leagues.append(league_code)
    
    def is_in_league(self, league_code: str) -> bool:
        """Check if user is in a specific league"""
        return league_code in self.leagues

