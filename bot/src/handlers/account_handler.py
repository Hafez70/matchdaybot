"""Account management handler"""
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from .base_handler import BaseHandler
from ..config import States


class AccountHandler(BaseHandler):
    """Handles account-related operations"""
    
    async def show_account_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show account settings menu"""
        query = update.callback_query
        await query.answer()
        
        user = self.user_service.get_user_by_telegram_id(update.effective_user.id)
        
        text = f"""
⚙️ تنظیمات حساب

👤 نام: {user.name}
🆔 شناسه تلگرام: {user.telegram_id}
🏆 تعداد لیگ‌ها: {len(user.leagues)}
📅 عضو از: {user.created_at.split('T')[0]}
"""
        
        await query.edit_message_text(
            text,
            reply_markup=self.keyboard.build_account_menu()
        )
    
    async def show_account_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show detailed account information"""
        query = update.callback_query
        await query.answer()
        
        user = self.user_service.get_user_by_telegram_id(update.effective_user.id)
        leagues = self.league_service.get_user_leagues(user.telegram_id)
        
        text = f"""
📋 اطلاعات کامل حساب

👤 نام: {user.name}
🆔 شناسه تلگرام: {user.telegram_id}
📅 عضو از: {user.created_at.split('T')[0]}

🏆 لیگ‌های شما ({len(leagues)}):\n"""
        
        if leagues:
            for league in leagues:
                member_count = len(league.members)
                text += f"• {league.name} ({league.code}) - {member_count} عضو\n"
        else:
            text += "هنوز عضو هیچ لیگی نیستید!"
        
        await query.edit_message_text(
            text,
            reply_markup=self.keyboard.build_back_button('menu_account')
        )
    
    async def edit_name_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Start name editing process"""
        query = update.callback_query
        await query.answer()
        
        user = self.user_service.get_user_by_telegram_id(update.effective_user.id)
        
        await query.edit_message_text(
            f"✏️ ویرایش نام\n\n"
            f"نام فعلی: {user.name}\n\n"
            f"نام جدید خودت رو وارد کن:",
            reply_markup=self.keyboard.build_cancel_button()
        )
        
        return States.EDIT_NAME
    
    async def edit_name_process(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Process name change"""
        new_name = update.message.text.strip()
        telegram_id = update.effective_user.id
        
        if not new_name or len(new_name) < 2:
            await update.message.reply_text(
                "⚠️ نام باید حداقل 2 حرف باشه!\n\nلطفاً نام معتبر وارد کن:",
                reply_markup=self.keyboard.build_cancel_button()
            )
            return States.EDIT_NAME
        
        try:
            user = self.user_service.update_user_name(telegram_id, new_name)
            
            await update.message.reply_text(
                f"✅ نام شما با موفقیت به '{user.name}' تغییر کرد!",
                reply_markup=self.keyboard.build_back_button('menu_account')
            )
            
            return ConversationHandler.END
            
        except ValueError as e:
            await update.message.reply_text(
                f"⚠️ {str(e)}\n\nلطفاً نام دیگری وارد کن:",
                reply_markup=self.keyboard.build_cancel_button()
            )
            return States.EDIT_NAME

