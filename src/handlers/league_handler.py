"""League management handler"""
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from .base_handler import BaseHandler
from ..config import States, Messages
from ..utils import to_persian_date


class LeagueHandler(BaseHandler):
    """Handles league-related operations"""
    
    async def show_my_leagues(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show user's leagues"""
        query = update.callback_query
        await query.answer()
        
        user = self.user_service.get_user_by_telegram_id(update.effective_user.id)
        leagues = self.league_service.get_user_leagues(user.telegram_id)
        
        if not leagues:
            await query.edit_message_text(
                "📭 شما هنوز عضو هیچ لیگی نیستید!\n\n"
                "می‌تونید لیگ جدید بسازید یا به لیگی بپیوندید.",
                reply_markup=self.keyboard.build_back_button()
            )
            return
        
        text = "🏆 لیگ‌های من:\n\n"
        league_list = []
        
        for league in leagues:
            member_count = len(league.members)
            owner_mark = " 👑" if league.is_owner(user.telegram_id) else ""
            text += f"• {league.name} ({league.code}){owner_mark}\n"
            text += f"  👥 {member_count} عضو\n\n"
            league_list.append((league.code, league.name))
        
        await query.edit_message_text(
            text + "یک لیگ رو انتخاب کن:",
            reply_markup=self.keyboard.build_league_list(league_list)
        )
    
    async def show_league_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show league-specific menu"""
        query = update.callback_query
        await query.answer()
        
        # Extract league code from callback data
        league_code = query.data.replace('select_league_', '')
        context.user_data['current_league'] = league_code
        
        league = self.league_service.get_league_by_code(league_code)
        if not league:
            await query.edit_message_text(
                "❌ لیگ پیدا نشد!",
                reply_markup=self.keyboard.build_back_button()
            )
            return
        
        member_count = len(league.members)
        owner_user = self.user_service.get_user_by_telegram_id(league.owner_telegram_id)
        
        text = f"""
🏆 {league.name}

🔑 کد لیگ: `{league.code}`
👑 مالک: {owner_user.name if owner_user else 'نامشخص'}
👥 اعضا: {member_count} نفر
📅 تاریخ ایجاد: {league.created_at.split('T')[0]}
"""
        
        await query.edit_message_text(
            text,
            reply_markup=self.keyboard.build_league_menu(league_code),
            parse_mode='Markdown'
        )
    
    async def create_league_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Start league creation process"""
        query = update.callback_query
        await query.answer()
        
        await query.edit_message_text(
            Messages.CREATE_LEAGUE_PROMPT,
            reply_markup=self.keyboard.build_cancel_button()
        )
        
        return States.CREATE_LEAGUE_NAME
    
    async def create_league_process(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Process league creation"""
        league_name = update.message.text.strip()
        telegram_id = update.effective_user.id
        
        if not league_name or len(league_name) < 3:
            await update.message.reply_text(
                "⚠️ نام لیگ باید حداقل 3 حرف باشه!\n\nلطفاً نام معتبر وارد کن:",
                reply_markup=self.keyboard.build_cancel_button()
            )
            return States.CREATE_LEAGUE_NAME
        
        try:
            # Create league
            league = self.league_service.create_league(league_name, telegram_id)
            
            # Add league to user
            self.user_service.add_league_to_user(telegram_id, league.code)
            
            await update.message.reply_text(
                Messages.LEAGUE_CREATED.format(name=league.name, code=league.code),
                reply_markup=self.keyboard.build_back_button(),
                parse_mode='Markdown'
            )
            
            return ConversationHandler.END
            
        except Exception as e:
            await update.message.reply_text(
                f"⚠️ خطا در ایجاد لیگ: {str(e)}\n\nلطفاً دوباره تلاش کن:",
                reply_markup=self.keyboard.build_cancel_button()
            )
            return States.CREATE_LEAGUE_NAME
    
    async def join_league_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Start league joining process"""
        query = update.callback_query
        await query.answer()
        
        await query.edit_message_text(
            Messages.JOIN_LEAGUE_PROMPT,
            reply_markup=self.keyboard.build_cancel_button()
        )
        
        return States.JOIN_LEAGUE_CODE
    
    async def join_league_process(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Process league joining"""
        league_code = update.message.text.strip().upper()
        telegram_id = update.effective_user.id
        
        try:
            # Join league
            league = self.league_service.join_league(league_code, telegram_id)
            
            # Add league to user
            self.user_service.add_league_to_user(telegram_id, league.code)
            
            await update.message.reply_text(
                f"✅ با موفقیت به لیگ '{league.name}' پیوستید!\n\n"
                f"🔑 کد لیگ: {league.code}\n"
                f"👥 اعضا: {len(league.members)} نفر",
                reply_markup=self.keyboard.build_back_button()
            )
            
            return ConversationHandler.END
            
        except ValueError as e:
            await update.message.reply_text(
                f"⚠️ {str(e)}\n\nلطفاً کد معتبر وارد کن:",
                reply_markup=self.keyboard.build_cancel_button()
            )
            return States.JOIN_LEAGUE_CODE
    
    async def show_league_members(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show league members"""
        query = update.callback_query
        await query.answer()
        
        # Extract league code from callback data
        parts = query.data.split('_')
        league_code = parts[1]
        
        league = self.league_service.get_league_by_code(league_code)
        if not league:
            await query.edit_message_text(
                "❌ لیگ پیدا نشد!",
                reply_markup=self.keyboard.build_back_button()
            )
            return
        
        users = self.user_service.get_users_in_league(league_code)
        
        text = f"👥 اعضای لیگ {league.name}:\n\n"
        
        for user in users:
            owner_mark = " 👑" if user.telegram_id == league.owner_telegram_id else ""
            text += f"• {user.name}{owner_mark}\n"
        
        text += f"\n📊 تعداد کل: {len(users)} نفر"
        
        await query.edit_message_text(
            text,
            reply_markup=self.keyboard.build_back_button(f'select_league_{league_code}')
        )
    
    async def show_league_leaderboard(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show league leaderboard with points"""
        query = update.callback_query
        await query.answer()
        
        # Extract league code from callback data
        parts = query.data.split('_')
        league_code = parts[1]
        
        league = self.league_service.get_league_by_code(league_code)
        if not league:
            await query.edit_message_text(
                "❌ لیگ پیدا نشد!",
                reply_markup=self.keyboard.build_back_button()
            )
            return
        
        leaderboard = self.match_service.get_league_leaderboard(league_code, self.user_service)
        
        if not leaderboard or all(p['matches'] == 0 for p in leaderboard):
            await query.edit_message_text(
                f"📭 هنوز مسابقه‌ای در لیگ '{league.name}' ثبت نشده!",
                reply_markup=self.keyboard.build_back_button(f'select_league_{league_code}')
            )
            return
        
        text = f"جدول لیگ {league.name}\n"
        text += "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        for player in leaderboard:
            if player['matches'] > 0:
                rank_icon = "🥇" if player['rank'] == 1 else "🥈" if player['rank'] == 2 else "🥉" if player['rank'] == 3 else f"{player['rank']}."
                
                text += f"{rank_icon} {player['name']}\n"
                text += f"   امتیاز: {player['points']:+d} | "
                text += f"بازی: {player['matches']} | "
                text += f"برد: {player['wins']} | "
                text += f"باخت: {player['losses']}\n"
                text += f"   تفاضل گل: {player['goal_difference']:+d}\n\n"
        
        await query.edit_message_text(
            text,
            reply_markup=self.keyboard.build_back_button(f'select_league_{league_code}')
        )

    
    async def show_recent_matches(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show recent matches in league"""
        query = update.callback_query
        await query.answer()
        
        # Extract league code from callback data
        parts = query.data.split('_')
        league_code = parts[1]
        
        league = self.league_service.get_league_by_code(league_code)
        if not league:
            await query.edit_message_text(
                "❌ لیگ پیدا نشد!",
                reply_markup=self.keyboard.build_back_button()
            )
            return
        
        matches = self.match_service.get_recent_matches(league_code, 10)
        
        if not matches:
            await query.edit_message_text(
                f"📭 هنوز مسابقه‌ای در لیگ '{league.name}' ثبت نشده!",
                reply_markup=self.keyboard.build_back_button(f'select_league_{league_code}')
            )
            return
        
        text = f"🎮 آخرین مسابقات لیگ {league.name}:\n\n"
        
        for i, match in enumerate(matches, 1):
            # Get player names
            team1_names = [self.user_service.get_user_by_telegram_id(tid).name 
                          for tid in match.team1]
            team2_names = [self.user_service.get_user_by_telegram_id(tid).name 
                          for tid in match.team2]
            
            team1_str = ' و '.join(team1_names)
            team2_str = ' و '.join(team2_names)
            
            winner = match.get_winner()
            winner_emoji = "🏆" if winner == 'team1' else "❌" if winner == 'team2' else "🤝"
            
            text += f"{i}. {team1_str} {match.result['team1']}-{match.result['team2']} {team2_str} {winner_emoji}\n"
            text += f"   📅 {to_persian_date(match.datetime)} | {match.match_type}\n\n"
        
        await query.edit_message_text(
            text,
            reply_markup=self.keyboard.build_back_button(f'select_league_{league_code}')
        )
    
    async def show_my_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show user's stats in league"""
        query = update.callback_query
        await query.answer()
        
        # Extract league code from callback data
        parts = query.data.split('_')
        league_code = parts[1]
        
        league = self.league_service.get_league_by_code(league_code)
        if not league:
            await query.edit_message_text(
                "❌ لیگ پیدا نشد!",
                reply_markup=self.keyboard.build_back_button()
            )
            return
        
        telegram_id = update.effective_user.id
        user = self.user_service.get_user_by_telegram_id(telegram_id)
        stats = self.match_service.get_player_stats(telegram_id, league_code)
        
        if stats['total_matches'] == 0:
            await query.edit_message_text(
                f"📭 شما هنوز در لیگ '{league.name}' مسابقه‌ای نداشتید!",
                reply_markup=self.keyboard.build_back_button(f'select_league_{league_code}')
            )
            return
        
        win_rate = (stats['wins'] / stats['total_matches'] * 100) if stats['total_matches'] > 0 else 0
        
        text = f"""
📊 آمار {user.name} در لیگ {league.name}

🎮 تعداد مسابقات: {stats['total_matches']}
🏆 برد: {stats['wins']}
❌ باخت: {stats['losses']}
🤝 مساوی: {stats['draws']}

⚽ گل زده: {stats['goals_for']}
🥅 گل خورده: {stats['goals_against']}
📈 تفاضل گل: {stats['goal_difference']:+d}

📊 درصد برد: {win_rate:.1f}%
"""
        
        await query.edit_message_text(
            text,
            reply_markup=self.keyboard.build_back_button(f'select_league_{league_code}')
        )

