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
        is_owner = update.effective_user.id == league.owner_telegram_id
        
        text = f"""
🏆 {league.name}

🔑 کد لیگ: `{league.code}`
👑 مالک: {owner_user.name if owner_user else 'نامشخص'}
👥 اعضا: {member_count} نفر
📅 تاریخ ایجاد: {league.created_at.split('T')[0]}
"""
        
        await query.edit_message_text(
            text,
            reply_markup=self.keyboard.build_league_menu(league_code, is_owner=is_owner),
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
        
        # Check if user is the league owner
        is_owner = update.effective_user.id == league.owner_telegram_id
        
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
        
        # If owner, show match management buttons
        if is_owner:
            text += "\n👑 شما مالک این لیگ هستید\nبرای ویرایش یا حذف مسابقه، آن را انتخاب کنید:"
            await query.edit_message_text(
                text,
                reply_markup=self.keyboard.build_match_management_list(matches, league_code)
            )
        else:
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
    
    async def show_match_actions(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show edit/delete options for a specific match"""
        query = update.callback_query
        await query.answer()
        
        # Extract match_id and league_code from callback data
        # Format: manage_match_{league_code}_{match_id}
        parts = query.data.split('_')
        league_code = parts[2]
        match_id = int(parts[3])
        
        league = self.league_service.get_league_by_code(league_code)
        if not league:
            await query.edit_message_text(
                "❌ لیگ پیدا نشد!",
                reply_markup=self.keyboard.build_back_button()
            )
            return
        
        # Verify user is owner
        if update.effective_user.id != league.owner_telegram_id:
            await query.answer("⚠️ فقط مالک لیگ می‌تواند مسابقات را مدیریت کند!", show_alert=True)
            return
        
        # Get match details
        match = self.match_service.get_match_by_id(match_id)
        if not match:
            await query.edit_message_text(
                "❌ مسابقه پیدا نشد!",
                reply_markup=self.keyboard.build_back_button(f'league_{league_code}_recent_matches')
            )
            return
        
        # Build match details text
        team1_names = [self.user_service.get_user_by_telegram_id(tid).name for tid in match.team1]
        team2_names = [self.user_service.get_user_by_telegram_id(tid).name for tid in match.team2]
        team1_str = ' و '.join(team1_names)
        team2_str = ' و '.join(team2_names)
        
        text = f"🎮 مدیریت مسابقه\n\n"
        text += f"👥 {team1_str} VS {team2_str}\n"
        text += f"📊 نتیجه: {match.result['team1']}-{match.result['team2']}\n"
        text += f"📅 تاریخ: {to_persian_date(match.datetime)}\n"
        text += f"🏆 نوع: {match.match_type}\n\n"
        text += "چه عملیاتی می‌خواهید انجام دهید؟"
        
        await query.edit_message_text(
            text,
            reply_markup=self.keyboard.build_match_action_buttons(match_id, league_code)
        )
    
    async def edit_match_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Start editing a match"""
        query = update.callback_query
        await query.answer()
        
        # Extract match_id and league_code from callback data
        # Format: edit_match_{league_code}_{match_id}
        parts = query.data.split('_')
        league_code = parts[2]
        match_id = int(parts[3])
        
        match = self.match_service.get_match_by_id(match_id)
        if not match:
            await query.edit_message_text(
                "❌ مسابقه پیدا نشد!",
                reply_markup=self.keyboard.build_back_button(f'league_{league_code}_recent_matches')
            )
            return ConversationHandler.END
        
        # Store in context
        context.user_data['editing_match_id'] = match_id
        context.user_data['editing_league_code'] = league_code
        
        team1_names = [self.user_service.get_user_by_telegram_id(tid).name for tid in match.team1]
        team2_names = [self.user_service.get_user_by_telegram_id(tid).name for tid in match.team2]
        team1_str = ' و '.join(team1_names)
        team2_str = ' و '.join(team2_names)
        
        text = f"✏️ ویرایش نتیجه مسابقه\n\n"
        text += f"👥 {team1_str} VS {team2_str}\n"
        text += f"📊 نتیجه فعلی: {match.result['team1']}-{match.result['team2']}\n\n"
        text += f"⚽ نتیجه جدید را وارد کنید:\n"
        text += f"فرمت: گل_تیم1-گل_تیم2\n"
        text += f"مثال: 3-2"
        
        await query.edit_message_text(
            text,
            reply_markup=self.keyboard.build_cancel_button()
        )
        
        return States.EDIT_MATCH_RESULT
    
    async def edit_match_result(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Process new match result"""
        result_text = update.message.text.strip()
        
        try:
            parts = result_text.split('-')
            if len(parts) != 2:
                raise ValueError()
            
            team1_score = int(parts[0].strip())
            team2_score = int(parts[1].strip())
            
            if team1_score < 0 or team2_score < 0:
                raise ValueError()
        
        except ValueError:
            await update.message.reply_text(
                "❌ فرمت نتیجه اشتباه است!\n"
                "لطفاً به فرمت 'عدد-عدد' وارد کنید\n"
                "مثال: 3-2",
                reply_markup=self.keyboard.build_cancel_button()
            )
            return States.EDIT_MATCH_RESULT
        
        match_id = context.user_data['editing_match_id']
        league_code = context.user_data['editing_league_code']
        
        # Update match
        success = self.match_service.update_match_score(match_id, team1_score, team2_score)
        
        if success:
            match = self.match_service.get_match_by_id(match_id)
            team1_names = [self.user_service.get_user_by_telegram_id(tid).name for tid in match.team1]
            team2_names = [self.user_service.get_user_by_telegram_id(tid).name for tid in match.team2]
            team1_str = ' و '.join(team1_names)
            team2_str = ' و '.join(team2_names)
            
            await update.message.reply_text(
                f"✅ نتیجه مسابقه با موفقیت ویرایش شد!\n\n"
                f"👥 {team1_str} VS {team2_str}\n"
                f"📊 نتیجه جدید: {team1_score}-{team2_score}",
                reply_markup=self.keyboard.build_back_button(f'league_{league_code}_recent_matches')
            )
        else:
            await update.message.reply_text(
                "❌ خطا در ویرایش مسابقه!",
                reply_markup=self.keyboard.build_back_button(f'league_{league_code}_recent_matches')
            )
        
        context.user_data.clear()
        return ConversationHandler.END
    
    async def delete_match_confirm(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Ask for confirmation before deleting a match"""
        query = update.callback_query
        await query.answer()
        
        # Extract match_id and league_code from callback data
        # Format: delete_match_{league_code}_{match_id}
        parts = query.data.split('_')
        league_code = parts[2]
        match_id = int(parts[3])
        
        match = self.match_service.get_match_by_id(match_id)
        if not match:
            await query.edit_message_text(
                "❌ مسابقه پیدا نشد!",
                reply_markup=self.keyboard.build_back_button(f'league_{league_code}_recent_matches')
            )
            return
        
        team1_names = [self.user_service.get_user_by_telegram_id(tid).name for tid in match.team1]
        team2_names = [self.user_service.get_user_by_telegram_id(tid).name for tid in match.team2]
        team1_str = ' و '.join(team1_names)
        team2_str = ' و '.join(team2_names)
        
        text = f"⚠️ تأیید حذف مسابقه\n\n"
        text += f"👥 {team1_str} VS {team2_str}\n"
        text += f"📊 نتیجه: {match.result['team1']}-{match.result['team2']}\n"
        text += f"📅 تاریخ: {to_persian_date(match.datetime)}\n\n"
        text += "⚠️ این عملیات غیرقابل بازگشت است!\n"
        text += "آیا مطمئن هستید؟"
        
        await query.edit_message_text(
            text,
            reply_markup=self.keyboard.build_yes_no(
                f'confirm_delete_match_{league_code}_{match_id}',
                f'manage_match_{league_code}_{match_id}'
            )
        )
    
    async def delete_match_execute(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Execute match deletion"""
        query = update.callback_query
        await query.answer()
        
        # Extract match_id and league_code from callback data
        # Format: confirm_delete_match_{league_code}_{match_id}
        parts = query.data.split('_')
        league_code = parts[3]
        match_id = int(parts[4])
        
        league = self.league_service.get_league_by_code(league_code)
        
        # Verify user is owner
        if update.effective_user.id != league.owner_telegram_id:
            await query.answer("⚠️ فقط مالک لیگ می‌تواند مسابقات را حذف کند!", show_alert=True)
            return
        
        success = self.match_service.delete_match(match_id)
        
        if success:
            await query.edit_message_text(
                "✅ مسابقه با موفقیت حذف شد!",
                reply_markup=self.keyboard.build_back_button(f'league_{league_code}_recent_matches')
            )
        else:
            await query.edit_message_text(
                "❌ خطا در حذف مسابقه!",
                reply_markup=self.keyboard.build_back_button(f'league_{league_code}_recent_matches')
            )
    
    async def cancel_edit(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Cancel match editing"""
        query = update.callback_query
        await query.answer()
        
        league_code = context.user_data.get('editing_league_code')
        context.user_data.clear()
        
        await query.edit_message_text(
            "❌ عملیات لغو شد.",
            reply_markup=self.keyboard.build_back_button(f'league_{league_code}_recent_matches')
        )
        
        return ConversationHandler.END
    
    # League Settings Handlers
    async def show_league_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show league settings menu (owner only)"""
        query = update.callback_query
        await query.answer()
        
        league_code = query.data.replace('league_settings_', '')
        league = self.league_service.get_league_by_code(league_code)
        
        if not league:
            await query.edit_message_text(
                "❌ لیگ پیدا نشد!",
                reply_markup=self.keyboard.build_back_button()
            )
            return
        
        # Verify user is owner
        if update.effective_user.id != league.owner_telegram_id:
            await query.answer("⚠️ فقط مالک لیگ می‌تواند تنظیمات را تغییر دهد!", show_alert=True)
            return
        
        text = f"""
⚙️ تنظیمات لیگ {league.name}

🔑 کد: `{league.code}`
📝 نام فعلی: {league.name}
🏆 GIF برد: {'✅ تنظیم شده' if league.winner_gif else '❌ تنظیم نشده'}
❌ GIF باخت: {'✅ تنظیم شده' if league.loser_gif else '❌ تنظیم نشده'}

از منوی زیر استفاده کن:
"""
        
        await query.edit_message_text(
            text,
            reply_markup=self.keyboard.build_league_settings_menu(league_code),
            parse_mode='Markdown'
        )
    
    async def edit_league_name_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Start editing league name"""
        query = update.callback_query
        await query.answer()
        
        league_code = query.data.replace('edit_league_name_', '')
        league = self.league_service.get_league_by_code(league_code)
        
        if not league or update.effective_user.id != league.owner_telegram_id:
            await query.answer("⚠️ خطا در دسترسی!", show_alert=True)
            return ConversationHandler.END
        
        context.user_data['editing_league_code'] = league_code
        
        await query.edit_message_text(
            f"✏️ ویرایش نام لیگ\n\nنام فعلی: {league.name}\n\nنام جدید را وارد کن:",
            reply_markup=self.keyboard.build_cancel_button()
        )
        
        return States.EDIT_LEAGUE_NAME
    
    async def edit_league_name_process(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Process new league name"""
        new_name = update.message.text.strip()
        league_code = context.user_data.get('editing_league_code')
        
        if not new_name or len(new_name) < 3:
            await update.message.reply_text(
                "⚠️ نام لیگ باید حداقل 3 حرف باشد!",
                reply_markup=self.keyboard.build_cancel_button()
            )
            return States.EDIT_LEAGUE_NAME
        
        try:
            success = self.db.update_league_name(league_code, new_name)
            
            if success:
                await update.message.reply_text(
                    f"✅ نام لیگ به '{new_name}' تغییر یافت!",
                    reply_markup=self.keyboard.build_back_button(f'league_settings_{league_code}')
                )
            else:
                await update.message.reply_text(
                    "❌ خطا در تغییر نام لیگ!",
                    reply_markup=self.keyboard.build_back_button(f'league_settings_{league_code}')
                )
        except Exception as e:
            await update.message.reply_text(
                f"❌ خطا: {str(e)}",
                reply_markup=self.keyboard.build_back_button(f'league_settings_{league_code}')
            )
        
        context.user_data.clear()
        return ConversationHandler.END
    
    async def set_winner_gif_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Start setting winner GIF"""
        query = update.callback_query
        await query.answer()
        
        league_code = query.data.replace('set_winner_gif_', '')
        league = self.league_service.get_league_by_code(league_code)
        
        if not league or update.effective_user.id != league.owner_telegram_id:
            await query.answer("⚠️ خطا در دسترسی!", show_alert=True)
            return ConversationHandler.END
        
        context.user_data['editing_league_code'] = league_code
        context.user_data['gif_type'] = 'winner'
        
        await query.edit_message_text(
            "🏆 تنظیم GIF برد\n\nیک GIF/انیمیشن ارسال کن یا لینک GIF را وارد کن:",
            reply_markup=self.keyboard.build_cancel_button()
        )
        
        return States.SET_WINNER_GIF
    
    async def set_loser_gif_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Start setting loser GIF"""
        query = update.callback_query
        await query.answer()
        
        league_code = query.data.replace('set_loser_gif_', '')
        league = self.league_service.get_league_by_code(league_code)
        
        if not league or update.effective_user.id != league.owner_telegram_id:
            await query.answer("⚠️ خطا در دسترسی!", show_alert=True)
            return ConversationHandler.END
        
        context.user_data['editing_league_code'] = league_code
        context.user_data['gif_type'] = 'loser'
        
        await query.edit_message_text(
            "❌ تنظیم GIF باخت\n\nیک GIF/انیمیشن ارسال کن یا لینک GIF را وارد کن:",
            reply_markup=self.keyboard.build_cancel_button()
        )
        
        return States.SET_LOSER_GIF
    
    async def set_gif_process(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Process GIF input (animation or text URL)"""
        league_code = context.user_data.get('editing_league_code')
        gif_type = context.user_data.get('gif_type')  # 'winner' or 'loser'
        
        gif_url = None
        
        # Check if user sent an animation/document
        if update.message.animation:
            gif_url = update.message.animation.file_id
        elif update.message.document and update.message.document.mime_type.startswith('image/gif'):
            gif_url = update.message.document.file_id
        elif update.message.text:
            # User sent a URL
            gif_url = update.message.text.strip()
            if not (gif_url.startswith('http://') or gif_url.startswith('https://')):
                await update.message.reply_text(
                    "⚠️ لطفاً یک لینک معتبر (شروع با http:// یا https://) وارد کن یا یک GIF ارسال کن!",
                    reply_markup=self.keyboard.build_cancel_button()
                )
                return States.SET_WINNER_GIF if gif_type == 'winner' else States.SET_LOSER_GIF
        
        if not gif_url:
            await update.message.reply_text(
                "⚠️ لطفاً یک GIF/انیمیشن ارسال کن یا لینک GIF را وارد کن!",
                reply_markup=self.keyboard.build_cancel_button()
            )
            return States.SET_WINNER_GIF if gif_type == 'winner' else States.SET_LOSER_GIF
        
        try:
            if gif_type == 'winner':
                success = self.db.update_league_gifs(league_code, winner_gif=gif_url)
                emoji = "🏆"
                text = "برد"
            else:
                success = self.db.update_league_gifs(league_code, loser_gif=gif_url)
                emoji = "❌"
                text = "باخت"
            
            if success:
                await update.message.reply_text(
                    f"✅ GIF {text} با موفقیت تنظیم شد! {emoji}",
                    reply_markup=self.keyboard.build_back_button(f'league_settings_{league_code}')
                )
            else:
                await update.message.reply_text(
                    f"❌ خطا در تنظیم GIF {text}!",
                    reply_markup=self.keyboard.build_back_button(f'league_settings_{league_code}')
                )
        except Exception as e:
            await update.message.reply_text(
                f"❌ خطا: {str(e)}",
                reply_markup=self.keyboard.build_back_button(f'league_settings_{league_code}')
            )
        
        context.user_data.clear()
        return ConversationHandler.END
    
    async def delete_league_confirm(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Ask for confirmation before deleting league"""
        query = update.callback_query
        await query.answer()
        
        league_code = query.data.replace('delete_league_', '')
        league = self.league_service.get_league_by_code(league_code)
        
        if not league:
            await query.edit_message_text(
                "❌ لیگ پیدا نشد!",
                reply_markup=self.keyboard.build_back_button()
            )
            return
        
        # Verify user is owner
        if update.effective_user.id != league.owner_telegram_id:
            await query.answer("⚠️ فقط مالک لیگ می‌تواند آن را حذف کند!", show_alert=True)
            return
        
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
        text = f"""
⚠️ حذف لیگ {league.name}

آیا مطمئنی که می‌خوای این لیگ رو حذف کنی؟

🔴 تمام اطلاعات لیگ شامل:
• اعضا ({len(league.members)} نفر)
• تمام مسابقات
• تمام آمار

برای همیشه حذف خواهند شد!

این عمل قابل بازگشت نیست!
"""
        
        keyboard = [
            [InlineKeyboardButton("✅ بله، حذف شود", callback_data=f'confirm_delete_league_{league_code}')],
            [InlineKeyboardButton("❌ خیر، منصرف شدم", callback_data=f'league_settings_{league_code}')]
        ]
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def delete_league_execute(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Execute league deletion"""
        query = update.callback_query
        await query.answer()
        
        league_code = query.data.replace('confirm_delete_league_', '')
        league = self.league_service.get_league_by_code(league_code)
        
        if not league:
            await query.edit_message_text(
                "❌ لیگ پیدا نشد!",
                reply_markup=self.keyboard.build_back_button()
            )
            return
        
        # Verify user is owner
        if update.effective_user.id != league.owner_telegram_id:
            await query.answer("⚠️ فقط مالک لیگ می‌تواند آن را حذف کند!", show_alert=True)
            return
        
        try:
            self.league_service.delete_league(league_code, update.effective_user.id)
            
            await query.edit_message_text(
                f"✅ لیگ '{league.name}' با موفقیت حذف شد.",
                reply_markup=self.keyboard.build_back_button('back_to_main_menu')
            )
        except Exception as e:
            await query.edit_message_text(
                f"❌ خطا در حذف لیگ: {str(e)}",
                reply_markup=self.keyboard.build_back_button(f'league_settings_{league_code}')
            )
    
    async def cancel_league_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Cancel league settings operation"""
        query = update.callback_query
        await query.answer()
        
        league_code = context.user_data.get('editing_league_code')
        context.user_data.clear()
        
        if league_code:
            await query.edit_message_text(
                "❌ عملیات لغو شد.",
                reply_markup=self.keyboard.build_back_button(f'league_settings_{league_code}')
            )
        else:
            await query.edit_message_text(
                "❌ عملیات لغو شد.",
                reply_markup=self.keyboard.build_back_button()
            )
        
        return ConversationHandler.END

