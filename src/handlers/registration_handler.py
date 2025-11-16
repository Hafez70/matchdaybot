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
            # User already registered, show main menu
            await update.message.reply_text(
                Messages.WELCOME.format(name=existing_user.name),
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

