"""Match model"""
from dataclasses import dataclass, field
from typing import List, Dict
from datetime import datetime


@dataclass
class Match:
    """Represents a match between teams"""
    
    league_code: str
    match_type: str  # '1v1', '2v2', '1v2', '2v1'
    team1: List[int]  # List of telegram IDs
    team2: List[int]  # List of telegram IDs
    result: Dict[str, int]  # {'team1': score, 'team2': score}
    match_id: int = 0
    datetime: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.match_id,
            'league_code': self.league_code,
            'type': self.match_type,
            'team1': self.team1,
            'team2': self.team2,
            'result': self.result,
            'datetime': self.datetime
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Match':
        """Create Match from dictionary"""
        return cls(
            match_id=data.get('id', 0),
            league_code=data['league_code'],
            match_type=data['type'],
            team1=data['team1'],
            team2=data['team2'],
            result=data['result'],
            datetime=data.get('datetime', datetime.now().isoformat())
        )
    
    def get_winner(self) -> str:
        """Determine the winner"""
        if self.result['team1'] > self.result['team2']:
            return 'team1'
        elif self.result['team2'] > self.result['team1']:
            return 'team2'
        return 'draw'
    
    def is_player_in_match(self, telegram_id: int) -> bool:
        """Check if a player participated in this match"""
        return telegram_id in self.team1 or telegram_id in self.team2
    
    def get_player_team(self, telegram_id: int) -> str:
        """Get which team the player was on"""
        if telegram_id in self.team1:
            return 'team1'
        elif telegram_id in self.team2:
            return 'team2'
        return None

