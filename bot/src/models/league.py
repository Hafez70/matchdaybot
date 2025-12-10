"""League model"""
from dataclasses import dataclass, field
from typing import List
from datetime import datetime
import secrets
import string


@dataclass
class League:
    """Represents a league/group"""
    
    code: str
    name: str
    owner_telegram_id: int
    members: List[int] = field(default_factory=list)  # List of telegram IDs
    winner_gif: str = None  # URL or file_id for winner GIF
    loser_gif: str = None  # URL or file_id for loser GIF
    archived: bool = False  # Whether the league is archived
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'code': self.code,
            'name': self.name,
            'owner_telegram_id': self.owner_telegram_id,
            'members': self.members,
            'winner_gif': self.winner_gif,
            'loser_gif': self.loser_gif,
            'archived': self.archived,
            'created_at': self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'League':
        """Create League from dictionary"""
        return cls(
            code=data['code'],
            name=data['name'],
            owner_telegram_id=data['owner_telegram_id'],
            members=data.get('members', []),
            winner_gif=data.get('winner_gif'),
            loser_gif=data.get('loser_gif'),
            archived=bool(data.get('archived', 0)),  # Convert 0/1 to False/True
            created_at=data.get('created_at', datetime.now().isoformat())
        )
    
    @staticmethod
    def generate_code(length: int = 6) -> str:
        """Generate a unique league code"""
        characters = string.ascii_uppercase + string.digits
        return ''.join(secrets.choice(characters) for _ in range(length))
    
    def add_member(self, telegram_id: int) -> None:
        """Add a member to the league"""
        if telegram_id not in self.members:
            self.members.append(telegram_id)
    
    def is_owner(self, telegram_id: int) -> bool:
        """Check if user is the league owner"""
        return self.owner_telegram_id == telegram_id
    
    def is_member(self, telegram_id: int) -> bool:
        """Check if user is a member of the league"""
        return telegram_id in self.members

