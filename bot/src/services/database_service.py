"""Database service for data persistence"""
import os
import json
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class DatabaseService:
    """Manages database operations (JSON file storage)"""
    
    def __init__(self, data_file: str = 'fifa_data.json'):
        self.data_file = data_file
        self.data = self._load_data()
    
    def _load_data(self) -> Dict:
        """Load data from JSON file"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"خطا در بارگذاری داده‌ها: {e}")
                return self._get_default_structure()
        return self._get_default_structure()
    
    def _get_default_structure(self) -> Dict:
        """Get default data structure"""
        return {
            'users': [],
            'leagues': [],
            'matches': []
        }
    
    def save_data(self) -> None:
        """Save data to JSON file"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            logger.info("داده‌ها با موفقیت ذخیره شدند")
        except Exception as e:
            logger.error(f"خطا در ذخیره داده‌ها: {e}")
    
    # User operations
    def get_all_users(self) -> List[Dict]:
        """Get all users"""
        return self.data.get('users', [])
    
    def add_user(self, user_data: Dict) -> None:
        """Add a new user"""
        self.data['users'].append(user_data)
        self.save_data()
    
    def update_user(self, telegram_id: int, user_data: Dict) -> None:
        """Update user data"""
        for i, user in enumerate(self.data['users']):
            if user['telegram_id'] == telegram_id:
                self.data['users'][i] = user_data
                self.save_data()
                return
    
    def delete_user(self, telegram_id: int) -> None:
        """Delete a user"""
        self.data['users'] = [u for u in self.data['users'] if u['telegram_id'] != telegram_id]
        self.save_data()
    
    # League operations
    def get_all_leagues(self) -> List[Dict]:
        """Get all leagues"""
        return self.data.get('leagues', [])
    
    def add_league(self, league_data: Dict) -> None:
        """Add a new league"""
        self.data['leagues'].append(league_data)
        self.save_data()
    
    def update_league(self, league_code: str, league_data: Dict) -> None:
        """Update league data"""
        for i, league in enumerate(self.data['leagues']):
            if league['code'] == league_code:
                self.data['leagues'][i] = league_data
                self.save_data()
                return
    
    def delete_league(self, league_code: str) -> None:
        """Delete a league"""
        self.data['leagues'] = [l for l in self.data['leagues'] if l['code'] != league_code]
        self.save_data()
    
    # Match operations
    def get_all_matches(self) -> List[Dict]:
        """Get all matches"""
        return self.data.get('matches', [])
    
    def add_match(self, match_data: Dict) -> int:
        """Add a new match and return its ID"""
        match_id = len(self.data['matches']) + 1
        match_data['id'] = match_id
        self.data['matches'].append(match_data)
        self.save_data()
        return match_id
    
    def update_match(self, match_id: int, match_data: Dict) -> None:
        """Update match data"""
        for i, match in enumerate(self.data['matches']):
            if match['id'] == match_id:
                self.data['matches'][i] = match_data
                self.save_data()
                return
    
    def delete_match(self, match_id: int) -> None:
        """Delete a match"""
        self.data['matches'] = [m for m in self.data['matches'] if m['id'] != match_id]
        self.save_data()

