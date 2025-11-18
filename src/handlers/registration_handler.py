"""Registration handler"""
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from .base_handler import BaseHandler
from ..config import States, Messages


class RegistrationHandler(BaseHandler):
    """Handles user registration"""
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle /start command"""
        user = update.effective_user
        
        # Check if user is already registered
        existing_user = self.get_user_or_none(user.id)
        
        if existing_user:
            # User already registered, show main menu with points
            leagues = self.league_service.get_user_leagues(existing_user.telegram_id)
            
            welcome_text = f"🎮 منوی اصلی ⚽\n\n"
            welcome_text += f"سلام {existing_user.name}!\n\n"
            
            if leagues:
                welcome_text += "📊 امتیازات شما:\n"
                welcome_text += "━━━━━━━━━━━━━━━━━\n\n"
                
                for league in leagues:
                    leaderboard = self.match_service.get_league_leaderboard(
                        league.code, 
                        self.user_service
                    )
                    
                    # Find user in leaderboard
                    user_stats = next(
                        (p for p in leaderboard if p['telegram_id'] == existing_user.telegram_id),
                        None
                    )
                    
                    if user_stats:
                        points = user_stats['points']
                        rank = user_stats['rank']
                        
                        # Determine rank suffix
                        if rank == 1:
                            rank_text = "نفر اول 🥇"
                        elif rank == 2:
                            rank_text = "نفر دوم 🥈"
                        elif rank == 3:
                            rank_text = "نفر سوم 🥉"
                        else:
                            rank_text = f"نفر {rank}"
                        
                        welcome_text += f"• {league.name}\n"
                        welcome_text += f"  {points:+d} امتیاز | {rank_text}\n\n"
                    else:
                        welcome_text += f"• {league.name}\n"
                        welcome_text += f"  0 امتیاز | بدون بازی\n\n"
            else:
                welcome_text += "شما هنوز عضو هیچ لیگی نیستید.\n"
            
            await update.message.reply_text(
                welcome_text,
                reply_markup=self.keyboard.build_main_menu()
            )
            return ConversationHandler.END
        else:
            # New user, start registration
            await update.message.reply_text(
                Messages.REGISTRATION_PROMPT,
                reply_markup=self.keyboard.build_cancel_button()
            )
            return States.REGISTRATION_NAME
    
    async def registration_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle registration name input"""
        name = update.message.text.strip()
        telegram_id = update.effective_user.id
        
        if not name or len(name) < 2:
            await update.message.reply_text(
                "⚠️ نام باید حداقل 2 حرف باشه!\n\nلطفاً نام معتبر وارد کن:",
                reply_markup=self.keyboard.build_cancel_button()
            )
            return States.REGISTRATION_NAME
        
        try:
            # Register user
            user = self.user_service.register_user(telegram_id, name)
            
            await update.message.reply_text(
                Messages.REGISTRATION_SUCCESS,
                reply_markup=self.keyboard.build_main_menu()
            )
            
            return ConversationHandler.END
            
        except ValueError as e:
            await update.message.reply_text(
                f"⚠️ {str(e)}\n\nلطفاً نام دیگری وارد کن:",
                reply_markup=self.keyboard.build_cancel_button()
            )
            return States.REGISTRATION_NAME
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show help message"""
        query = update.callback_query
        
        if query:
            await query.answer()
            await query.edit_message_text(
                Messages.HELP,
                reply_markup=self.keyboard.build_back_button(),
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                Messages.HELP,
                reply_markup=self.keyboard.build_back_button(),
                parse_mode='Markdown'
            )

