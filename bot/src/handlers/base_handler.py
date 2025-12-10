"""Base handler with common functionality"""
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from ..services import DatabaseService, UserService, LeagueService, MatchService
from ..utils import KeyboardBuilder
from ..config import States, Messages


class BaseHandler:
    """Base class for all handlers"""
    
    def __init__(self, db_service: DatabaseService):
        self.db = db_service
        self.user_service = UserService(db_service)
        self.league_service = LeagueService(db_service)
        self.match_service = MatchService(db_service)
        self.keyboard = KeyboardBuilder()
    
    async def ensure_user_registered(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """
        Check if user is registered. If not, prompt them to register.
        Returns True if user exists, False if redirect to registration.
        """
        telegram_id = update.effective_user.id
        user = self.get_user_or_none(telegram_id)
        
        if user:
            return True
        
        # User not registered - prompt to register
        register_message = (
            "⚠️ شما هنوز ثبت‌نام نکردید!\n\n"
            "لطفاً اول /start رو بزنید و ثبت‌نام کنید."
        )
        
        query = update.callback_query
        if query:
            await query.answer("لطفاً اول ثبت‌نام کنید!")
            await query.edit_message_text(
                register_message,
                reply_markup=self.keyboard.build_back_button()
            )
        else:
            await update.message.reply_text(
                register_message,
                reply_markup=self.keyboard.build_back_button()
            )
        
        return False
    
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Cancel current operation"""
        query = update.callback_query
        if query:
            await query.answer()
            await query.edit_message_text(
                "❌ عملیات لغو شد.",
                reply_markup=self.keyboard.build_back_button()
            )
        else:
            await update.message.reply_text(
                "❌ عملیات لغو شد.",
                reply_markup=self.keyboard.build_back_button()
            )
        
        context.user_data.clear()
        return ConversationHandler.END
    
    async def back_to_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show main menu"""
        query = update.callback_query
        if query:
            await query.answer()
            await query.edit_message_text(
                "🎮 منوی اصلی ⚽\n\nیکی از گزینه‌های زیر رو انتخاب کن:",
                reply_markup=self.keyboard.build_main_menu()
            )
        else:
            await update.message.reply_text(
                "🎮 منوی اصلی ⚽\n\nیکی از گزینه‌های زیر رو انتخاب کن:",
                reply_markup=self.keyboard.build_main_menu()
            )
    
    def get_user_or_none(self, telegram_id: int):
        """Get user by telegram ID or return None"""
        try:
            return self.user_service.get_user_by_telegram_id(telegram_id)
        except Exception:
            return None

