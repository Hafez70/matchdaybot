"""Registration handler"""
from telegram import Update, MenuButtonWebApp, WebAppInfo
from telegram.ext import ContextTypes, ConversationHandler
from .base_handler import BaseHandler
from ..config import States, Messages

# Mini App URL
MINI_APP_URL = "https://matchdayfc.ir"


class RegistrationHandler(BaseHandler):
    """Handles user registration"""
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle /start command with deep link support"""
        user = update.effective_user
        
        # Set up Mini App menu button at the bottom of chat
        try:
            await context.bot.set_chat_menu_button(
                chat_id=update.effective_chat.id,
                menu_button=MenuButtonWebApp(
                    text="📊 مینی‌اپ",
                    web_app=WebAppInfo(url=MINI_APP_URL)
                )
            )
        except Exception:
            pass  # Ignore if setting menu button fails
        
        # Check for deep link parameter (e.g., /start join_LEAGUECODE)
        deep_link_param = None
        if context.args and len(context.args) > 0:
            deep_link_param = context.args[0]
        
        # Check if user is already registered
        existing_user = self.get_user_or_none(user.id)
        
        if existing_user:
            # Handle deep link join if provided
            if deep_link_param and deep_link_param.startswith('join_'):
                league_code = deep_link_param[5:].upper()  # Remove 'join_' prefix
                return await self._handle_deep_link_join(update, context, existing_user, league_code)
            
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
            # Save pending league join for after registration
            if deep_link_param and deep_link_param.startswith('join_'):
                context.user_data['pending_league_join'] = deep_link_param[5:].upper()
            
            # New user, start registration
            await update.message.reply_text(
                Messages.REGISTRATION_PROMPT,
                reply_markup=self.keyboard.build_cancel_button()
            )
            return States.REGISTRATION_NAME
    
    async def _handle_deep_link_join(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                      user, league_code: str) -> int:
        """Handle joining a league via deep link"""
        try:
            league = self.league_service.get_league_by_code(league_code)
            
            if not league:
                await update.message.reply_text(
                    f"❌ لیگ با کد `{league_code}` پیدا نشد!",
                    reply_markup=self.keyboard.build_main_menu(),
                    parse_mode='Markdown'
                )
                return ConversationHandler.END
            
            # Check if already a member
            if league.is_member(user.telegram_id):
                await update.message.reply_text(
                    f"ℹ️ شما قبلاً عضو لیگ '{league.name}' هستید!",
                    reply_markup=self.keyboard.build_main_menu()
                )
                return ConversationHandler.END
            
            # Join the league
            self.league_service.join_league(league_code, user.telegram_id)
            
            await update.message.reply_text(
                f"✅ به لیگ '{league.name}' خوش اومدید!\n\n"
                f"🏆 نام لیگ: {league.name}\n"
                f"👥 اعضا: {len(league.members) + 1} نفر",
                reply_markup=self.keyboard.build_main_menu()
            )
            return ConversationHandler.END
            
        except Exception as e:
            await update.message.reply_text(
                f"⚠️ خطا در پیوستن به لیگ: {str(e)}",
                reply_markup=self.keyboard.build_main_menu()
            )
            return ConversationHandler.END
    
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
            
            # Check for pending league join from deep link
            pending_league = context.user_data.pop('pending_league_join', None)
            
            if pending_league:
                # Try to join the pending league
                try:
                    league = self.league_service.get_league_by_code(pending_league)
                    if league:
                        self.league_service.join_league(pending_league, telegram_id)
                        await update.message.reply_text(
                            f"✅ ثبت نام با موفقیت انجام شد!\n\n"
                            f"🎉 همچنین به لیگ '{league.name}' پیوستید!",
                            reply_markup=self.keyboard.build_main_menu()
                        )
                        return ConversationHandler.END
                except Exception:
                    pass  # If join fails, just show normal success message
            
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

