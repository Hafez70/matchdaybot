"""Main bot application - Modular FIFA Match Tracking System"""
import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters
)

from src.services import SQLiteDatabaseService
from src.handlers import (
    RegistrationHandler,
    LeagueHandler,
    MatchHandler,
    AccountHandler
)
from src.config import States

# Load environment variables
load_dotenv('config.env')

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get settings
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
DB_FILE = 'fifa_bot.db'


class FifaBot:
    """Main FIFA Bot Application"""
    
    def __init__(self):
        self.db_service = SQLiteDatabaseService(DB_FILE)
        
        # Initialize handlers
        self.registration_handler = RegistrationHandler(self.db_service)
        self.league_handler = LeagueHandler(self.db_service)
        self.match_handler = MatchHandler(self.db_service)
        self.account_handler = AccountHandler(self.db_service)
    
    def setup_handlers(self, application: Application) -> None:
        """Setup all conversation handlers"""
        
        # Registration conversation
        registration_conv = ConversationHandler(
            entry_points=[CommandHandler('start', self.registration_handler.start)],
            states={
                States.REGISTRATION_NAME: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, 
                                 self.registration_handler.registration_name),
                    CallbackQueryHandler(self.registration_handler.cancel, 
                                       pattern='^cancel_operation$')
                ],
            },
            fallbacks=[CallbackQueryHandler(self.registration_handler.cancel, 
                                          pattern='^cancel_operation$')],
        )
        
        # League creation conversation
        create_league_conv = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.league_handler.create_league_start, 
                                              pattern='^menu_create_league$')],
            states={
                States.CREATE_LEAGUE_NAME: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, 
                                 self.league_handler.create_league_process),
                    CallbackQueryHandler(self.league_handler.cancel, 
                                       pattern='^cancel_operation$')
                ],
            },
            fallbacks=[CallbackQueryHandler(self.league_handler.cancel, 
                                          pattern='^cancel_operation$')],
        )
        
        # League joining conversation
        join_league_conv = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.league_handler.join_league_start, 
                                              pattern='^menu_join_league$')],
            states={
                States.JOIN_LEAGUE_CODE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, 
                                 self.league_handler.join_league_process),
                    CallbackQueryHandler(self.league_handler.cancel, 
                                       pattern='^cancel_operation$')
                ],
            },
            fallbacks=[CallbackQueryHandler(self.league_handler.cancel, 
                                          pattern='^cancel_operation$')],
        )
        
        # Account editing conversation
        edit_name_conv = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.account_handler.edit_name_start, 
                                              pattern='^account_edit_name$')],
            states={
                States.EDIT_NAME: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, 
                                 self.account_handler.edit_name_process),
                    CallbackQueryHandler(self.account_handler.cancel, 
                                       pattern='^cancel_operation$')
                ],
            },
            fallbacks=[CallbackQueryHandler(self.account_handler.cancel, 
                                          pattern='^cancel_operation$')],
        )
        
        # Match recording conversation
        match_conv = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.match_handler.record_match_start, 
                                              pattern='^league_.*_record_match$')],
            states={
                States.MATCH_TEAM1_P1: [
                    CallbackQueryHandler(self.match_handler.select_team1_player, 
                                       pattern='^(select_team1_|finish_team1)')
                ],
                States.MATCH_TEAM2_P1: [
                    CallbackQueryHandler(self.match_handler.select_team2_player, 
                                       pattern='^(select_team2_|finish_team2)')
                ],
                States.MATCH_RESULT: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, 
                                 self.match_handler.match_result)
                ],
                States.MATCH_CONTINUE: [
                    CallbackQueryHandler(self.match_handler.add_another_result, 
                                       pattern='^add_another_result$'),
                    CallbackQueryHandler(self.match_handler.finish_competition, 
                                       pattern='^finish_competition$')
                ],
            },
            fallbacks=[CallbackQueryHandler(self.match_handler.cancel, 
                                          pattern='^cancel_operation$')],
        )
        
        # Add conversation handlers
        application.add_handler(registration_conv)
        application.add_handler(create_league_conv)
        application.add_handler(join_league_conv)
        application.add_handler(edit_name_conv)
        application.add_handler(match_conv)
        
        # Simple callback handlers
        application.add_handler(CommandHandler('help', self.registration_handler.help_command))
        
        application.add_handler(CallbackQueryHandler(
            self.registration_handler.back_to_main_menu, 
            pattern='^back_to_main_menu$'
        ))
        
        application.add_handler(CallbackQueryHandler(
            self.registration_handler.help_command, 
            pattern='^menu_help$'
        ))
        
        application.add_handler(CallbackQueryHandler(
            self.account_handler.show_account_menu, 
            pattern='^menu_account$'
        ))
        
        application.add_handler(CallbackQueryHandler(
            self.account_handler.show_account_info, 
            pattern='^account_info$'
        ))
        
        application.add_handler(CallbackQueryHandler(
            self.league_handler.show_my_leagues, 
            pattern='^menu_my_leagues$'
        ))
        
        application.add_handler(CallbackQueryHandler(
            self.league_handler.show_league_menu, 
            pattern='^select_league_'
        ))
        
        application.add_handler(CallbackQueryHandler(
            self.league_handler.show_league_members, 
            pattern='^league_.*_members$'
        ))
        
        application.add_handler(CallbackQueryHandler(
            self.league_handler.show_league_leaderboard, 
            pattern='^league_.*_leaderboard$'
        ))
        
        application.add_handler(CallbackQueryHandler(
            self.league_handler.show_recent_matches, 
            pattern='^league_.*_recent_matches$'
        ))
        
        application.add_handler(CallbackQueryHandler(
            self.league_handler.show_my_stats, 
            pattern='^league_.*_my_stats$'
        ))


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    logger.error(f"خطا در آپدیت {update}: {context.error}")


def main():
    """Main function"""
    
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN تنظیم نشده است!")
        return
    
    # Create bot instance
    bot = FifaBot()
    
    # Create application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Setup handlers
    bot.setup_handlers(application)
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # Start polling
    logger.info("🎮⚽ ربات فیفا (نسخه مدولار) شروع به کار کرد...")
    logger.info("📱 ویژگی‌های جدید: ثبت نام، لیگ، مسابقات 1v2 و 2v1!")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()

