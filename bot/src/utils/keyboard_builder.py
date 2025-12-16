"""Keyboard builder utility"""
from typing import List, Tuple
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

# Mini App URL
MINI_APP_URL = "https://matchdayfc.ir"


class KeyboardBuilder:
    """Utility class to build inline keyboards"""
    
    @staticmethod
    def build_main_menu() -> InlineKeyboardMarkup:
        """Build main menu keyboard"""
        keyboard = [
            [InlineKeyboardButton("⚙️ تنظیمات حساب", callback_data='menu_account')],
            [InlineKeyboardButton("🏆 لیگ‌های من", callback_data='menu_my_leagues')],
            [InlineKeyboardButton("➕ ایجاد لیگ جدید", callback_data='menu_create_league')],
            [InlineKeyboardButton("🔗 پیوستن به لیگ", callback_data='menu_join_league')],
            [InlineKeyboardButton("❓ راهنما", callback_data='menu_help')]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def build_league_menu(league_code: str, is_owner: bool = False) -> InlineKeyboardMarkup:
        """Build league-specific menu"""
        keyboard = [
            # Mini App button - opens league view in Telegram WebApp
            [InlineKeyboardButton(
                "📊 مشاهده لیگ",
                web_app=WebAppInfo(url=f"{MINI_APP_URL}?league={league_code}")
            )],
            [InlineKeyboardButton("⚽ ثبت مسابقه", callback_data=f'league_{league_code}_record_match')],
            [InlineKeyboardButton("👥 اعضای لیگ", callback_data=f'league_{league_code}_members')],
            [InlineKeyboardButton("📊 آمار من", callback_data=f'league_{league_code}_my_stats')],
            [InlineKeyboardButton("🏅 جدول لیگ", callback_data=f'league_{league_code}_leaderboard')],
            [InlineKeyboardButton("🎮 مسابقات اخیر", callback_data=f'league_{league_code}_recent_matches')],
        ]
        
        # Add settings and delete buttons for league owner
        if is_owner:
            keyboard.append([InlineKeyboardButton("⚙️ تنظیمات لیگ", callback_data=f'league_settings_{league_code}')])
        
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_main_menu')])
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def build_account_menu() -> InlineKeyboardMarkup:
        """Build account settings menu"""
        keyboard = [
            [InlineKeyboardButton("✏️ ویرایش نام", callback_data='account_edit_name')],
            [InlineKeyboardButton("📋 اطلاعات من", callback_data='account_info')],
            [InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_main_menu')]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def build_player_selection(
        players: List[Tuple[int, str]],
        callback_prefix: str,
        exclude_ids: List[int] = None
    ) -> InlineKeyboardMarkup:
        """Build player selection keyboard"""
        if exclude_ids is None:
            exclude_ids = []
        
        keyboard = []
        row = []
        
        for telegram_id, name in players:
            if telegram_id not in exclude_ids:
                button = InlineKeyboardButton(
                    f"👤 {name}",
                    callback_data=f"{callback_prefix}_{telegram_id}"
                )
                row.append(button)
                
                if len(row) == 2:
                    keyboard.append(row)
                    row = []
        
        if row:
            keyboard.append(row)
        
        keyboard.append([InlineKeyboardButton("❌ لغو", callback_data='cancel_operation')])
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def build_match_type_keyboard() -> InlineKeyboardMarkup:
        """Build match type selection keyboard"""
        keyboard = [
            [InlineKeyboardButton("1️⃣ تک نفره (1v1)", callback_data='match_type_1v1')],
            [InlineKeyboardButton("2️⃣ دو نفره (2v2)", callback_data='match_type_2v2')],
            [InlineKeyboardButton("🔀 یک به دو (1v2)", callback_data='match_type_1v2')],
            [InlineKeyboardButton("🔀 دو به یک (2v1)", callback_data='match_type_2v1')],
            [InlineKeyboardButton("❌ لغو", callback_data='cancel_operation')]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def build_league_list(leagues: List[Tuple[str, str]]) -> InlineKeyboardMarkup:
        """Build league list keyboard"""
        keyboard = []
        
        for code, name in leagues:
            keyboard.append([InlineKeyboardButton(
                f"🏆 {name}",
                callback_data=f'select_league_{code}'
            )])
        
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_main_menu')])
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def build_back_button(callback_data: str = 'back_to_main_menu') -> InlineKeyboardMarkup:
        """Build simple back button"""
        keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data=callback_data)]]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def build_cancel_button() -> InlineKeyboardMarkup:
        """Build cancel button"""
        keyboard = [[InlineKeyboardButton("❌ لغو", callback_data='cancel_operation')]]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def build_yes_no(yes_callback: str, no_callback: str) -> InlineKeyboardMarkup:
        """Build yes/no buttons"""
        keyboard = [
            [
                InlineKeyboardButton("✅ بله", callback_data=yes_callback),
                InlineKeyboardButton("❌ خیر", callback_data=no_callback)
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def build_league_update_menu(league_code: str) -> InlineKeyboardMarkup:
        """Build league update notification menu"""
        keyboard = [
            [InlineKeyboardButton("🎮 مسابقات اخیر", callback_data=f'league_{league_code}_recent_matches')],
            [InlineKeyboardButton("🏅 جدول لیگ", callback_data=f'league_{league_code}_leaderboard')],
            [InlineKeyboardButton("🔙 منوی اصلی", callback_data='back_to_main_menu')]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def build_match_management_list(matches: List, league_code: str) -> InlineKeyboardMarkup:
        """Build match list with management buttons for league owner"""
        keyboard = []
        
        for match in matches[:10]:  # Limit to 10 matches
            button_text = f"#{match.match_id}: {match.result['team1']}-{match.result['team2']}"
            keyboard.append([InlineKeyboardButton(
                button_text,
                callback_data=f'manage_match_{league_code}_{match.match_id}'
            )])
        
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data=f'select_league_{league_code}')])
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def build_match_action_buttons(match_id: int, league_code: str) -> InlineKeyboardMarkup:
        """Build edit/delete buttons for a match"""
        keyboard = [
            [InlineKeyboardButton("✏️ ویرایش نتیجه", callback_data=f'edit_match_{league_code}_{match_id}')],
            [InlineKeyboardButton("🗑 حذف مسابقه", callback_data=f'delete_match_{league_code}_{match_id}')],
            [InlineKeyboardButton("🔙 بازگشت", callback_data=f'league_{league_code}_recent_matches')]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def build_league_settings_menu(league_code: str, is_archived: bool = False) -> InlineKeyboardMarkup:
        """Build league settings menu for owners"""
        keyboard = [
            [InlineKeyboardButton("✏️ ویرایش نام لیگ", callback_data=f'edit_league_name_{league_code}')],
            [InlineKeyboardButton("🏆 تنظیم GIF برد", callback_data=f'set_winner_gif_{league_code}')],
            [InlineKeyboardButton("❌ تنظیم GIF باخت", callback_data=f'set_loser_gif_{league_code}')],
        ]
        
        # Archive/Unarchive button
        if is_archived:
            keyboard.append([InlineKeyboardButton("📂 فعال کردن لیگ", callback_data=f'unarchive_league_{league_code}')])
        else:
            keyboard.append([InlineKeyboardButton("📦 آرشیو کردن لیگ", callback_data=f'archive_league_{league_code}')])
        
        keyboard.append([InlineKeyboardButton("🗑 حذف لیگ", callback_data=f'delete_league_{league_code}')])
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data=f'select_league_{league_code}')])
        
        return InlineKeyboardMarkup(keyboard)

