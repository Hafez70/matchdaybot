"""Match recording handler - Flexible team building"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from .base_handler import BaseHandler
from ..config import States


class MatchHandler(BaseHandler):
    """Handles match recording with flexible team building"""
    
    async def record_match_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Start match recording - select Team 1 players"""
        query = update.callback_query
        await query.answer()
        
        # Extract league code
        league_code = query.data.split('_')[1]
        context.user_data['match_league'] = league_code
        context.user_data['team1_players'] = []
        context.user_data['team2_players'] = []
        context.user_data['match_results'] = []
        
        league = self.league_service.get_league_by_code(league_code)
        if not league:
            await query.edit_message_text(
                "❌ لیگ پیدا نشد!",
                reply_markup=self.keyboard.build_back_button()
            )
            return ConversationHandler.END
        
        # Check members
        if len(league.members) < 2:
            await query.edit_message_text(
                "⚠️ لیگ باید حداقل 2 عضو داشته باشه!",
                reply_markup=self.keyboard.build_back_button(f'select_league_{league_code}')
            )
            return ConversationHandler.END
        
        # Start team 1 selection
        await self._show_team_selection(query, context, league_code, 1)
        return States.MATCH_TEAM1_P1
    
    async def _show_team_selection(self, query, context, league_code: str, team_num: int):
        """Show player selection for a team"""
        players = self.user_service.get_users_in_league(league_code)
        
        # Get already selected players
        team1 = context.user_data.get('team1_players', [])
        team2 = context.user_data.get('team2_players', [])
        exclude_ids = team1 + team2
        
        # Build keyboard
        keyboard = []
        row = []
        
        for player in players:
            if player.telegram_id not in exclude_ids:
                button = InlineKeyboardButton(
                    f"👤 {player.name}",
                    callback_data=f"select_team{team_num}_{player.telegram_id}"
                )
                row.append(button)
                
                if len(row) == 2:
                    keyboard.append(row)
                    row = []
        
        if row:
            keyboard.append(row)
        
        # Add "Finish selection" button if at least one player selected
        current_team = team1 if team_num == 1 else team2
        if len(current_team) > 0:
            keyboard.append([InlineKeyboardButton(
                "✅ پایان انتخاب تیم",
                callback_data=f"finish_team{team_num}"
            )])
        
        keyboard.append([InlineKeyboardButton("❌ لغو", callback_data='cancel_operation')])
        
        # Build message
        if team_num == 1:
            selected = [self.user_service.get_user_by_telegram_id(tid).name for tid in team1]
            text = f"⚽ انتخاب بازیکنان تیم 1 (حداکثر 2 نفر)\n\n"
            if selected:
                text += f"✅ انتخاب شده: {' و '.join(selected)}\n\n"
            text += "👤 بازیکن بعدی رو انتخاب کن یا پایان انتخاب:"
        else:
            selected = [self.user_service.get_user_by_telegram_id(tid).name for tid in team2]
            text = f"⚽ انتخاب بازیکنان تیم 2 (حداکثر 2 نفر)\n\n"
            if selected:
                text += f"✅ انتخاب شده: {' و '.join(selected)}\n\n"
            text += "👤 بازیکن بعدی رو انتخاب کن یا پایان انتخاب:"
        
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    
    async def select_team1_player(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Add player to team 1"""
        query = update.callback_query
        await query.answer()
        
        # Handle finish selection
        if query.data == 'finish_team1':
            return await self._start_team2_selection(query, context)
        
        # Get player ID
        telegram_id = int(query.data.replace('select_team1_', ''))
        
        # Add to team1
        team1 = context.user_data.get('team1_players', [])
        
        if len(team1) >= 2:
            await query.answer("⚠️ حداکثر 2 بازیکن!", show_alert=True)
            return States.MATCH_TEAM1_P1
        
        team1.append(telegram_id)
        context.user_data['team1_players'] = team1
        
        # If 2 players selected, go to team 2
        if len(team1) == 2:
            return await self._start_team2_selection(query, context)
        
        # Show updated selection
        league_code = context.user_data['match_league']
        await self._show_team_selection(query, context, league_code, 1)
        return States.MATCH_TEAM1_P1
    
    async def _start_team2_selection(self, query, context):
        """Start team 2 selection"""
        league_code = context.user_data['match_league']
        await self._show_team_selection(query, context, league_code, 2)
        return States.MATCH_TEAM2_P1
    
    async def select_team2_player(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Add player to team 2"""
        query = update.callback_query
        await query.answer()
        
        # Handle finish selection
        if query.data == 'finish_team2':
            return await self._show_result_prompt(query, context)
        
        # Get player ID
        telegram_id = int(query.data.replace('select_team2_', ''))
        
        # Add to team2
        team2 = context.user_data.get('team2_players', [])
        
        if len(team2) >= 2:
            await query.answer("⚠️ حداکثر 2 بازیکن!", show_alert=True)
            return States.MATCH_TEAM2_P1
        
        team2.append(telegram_id)
        context.user_data['team2_players'] = team2
        
        # If 2 players selected, go to result
        if len(team2) == 2:
            return await self._show_result_prompt(query, context)
        
        # Show updated selection
        league_code = context.user_data['match_league']
        await self._show_team_selection(query, context, league_code, 2)
        return States.MATCH_TEAM2_P1
    
    async def _show_result_prompt(self, query, context) -> int:
        """Show result input prompt"""
        team1_ids = context.user_data['team1_players']
        team2_ids = context.user_data['team2_players']
        
        team1_names = [self.user_service.get_user_by_telegram_id(tid).name for tid in team1_ids]
        team2_names = [self.user_service.get_user_by_telegram_id(tid).name for tid in team2_ids]
        
        team1_str = ' و '.join(team1_names)
        team2_str = ' و '.join(team2_names)
        
        results = context.user_data.get('match_results', [])
        results_text = ""
        if results:
            results_text = "\n\n📊 نتایج ثبت شده:\n"
            for i, r in enumerate(results, 1):
                results_text += f"{i}. {r['team1_score']}-{r['team2_score']}\n"
        
        await query.edit_message_text(
            f"✅ تیم 1: {team1_str}\n"
            f"✅ تیم 2: {team2_str}"
            f"{results_text}\n\n"
            f"⚽ نتیجه مسابقه رو وارد کن:\n"
            f"فرمت: گل_تیم1-گل_تیم2\n"
            f"مثال: 3-2",
            reply_markup=self.keyboard.build_cancel_button()
        )
        
        return States.MATCH_RESULT
    
    async def match_result(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Process match result"""
        result_text = update.message.text.strip()
        
        # Parse result
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
            return States.MATCH_RESULT
        
        # Save result to context
        results = context.user_data.get('match_results', [])
        results.append({
            'team1_score': team1_score,
            'team2_score': team2_score
        })
        context.user_data['match_results'] = results
        
        # Build teams info
        team1_ids = context.user_data['team1_players']
        team2_ids = context.user_data['team2_players']
        team1_names = [self.user_service.get_user_by_telegram_id(tid).name for tid in team1_ids]
        team2_names = [self.user_service.get_user_by_telegram_id(tid).name for tid in team2_ids]
        team1_str = ' و '.join(team1_names)
        team2_str = ' و '.join(team2_names)
        
        winner_emoji = "🏆" if team1_score > team2_score else "❌" if team1_score < team2_score else "🤝"
        
        # Show result and ask for more
        results_text = "\n📊 نتایج ثبت شده:\n"
        for i, r in enumerate(results, 1):
            emoji = "🏆" if r['team1_score'] > r['team2_score'] else "❌" if r['team1_score'] < r['team2_score'] else "🤝"
            results_text += f"{i}. {emoji} {r['team1_score']}-{r['team2_score']}\n"
        
        keyboard = [
            [InlineKeyboardButton("➕ ثبت نتیجه بعدی", callback_data='add_another_result')],
            [InlineKeyboardButton("✅ پایان و ذخیره مسابقات", callback_data='finish_competition')],
            [InlineKeyboardButton("❌ لغو", callback_data='cancel_operation')]
        ]
        
        text = f"""
✅ نتیجه ثبت شد!

{winner_emoji} {team1_str} {team1_score}-{team2_score} {team2_str}

{results_text}
می‌خوای نتیجه بعدی رو ثبت کنی یا تمام مسابقات رو ذخیره کنی؟
"""
        
        await update.message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        return States.MATCH_CONTINUE
    
    async def add_another_result(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Add another result"""
        query = update.callback_query
        await query.answer()
        
        team1_ids = context.user_data['team1_players']
        team2_ids = context.user_data['team2_players']
        team1_names = [self.user_service.get_user_by_telegram_id(tid).name for tid in team1_ids]
        team2_names = [self.user_service.get_user_by_telegram_id(tid).name for tid in team2_ids]
        team1_str = ' و '.join(team1_names)
        team2_str = ' و '.join(team2_names)
        
        results = context.user_data.get('match_results', [])
        results_text = "\n📊 نتایج قبلی:\n"
        for i, r in enumerate(results, 1):
            emoji = "🏆" if r['team1_score'] > r['team2_score'] else "❌" if r['team1_score'] < r['team2_score'] else "🤝"
            results_text += f"{i}. {emoji} {r['team1_score']}-{r['team2_score']}\n"
        
        await query.edit_message_text(
            f"✅ تیم 1: {team1_str}\n"
            f"✅ تیم 2: {team2_str}"
            f"{results_text}\n\n"
            f"⚽ نتیجه مسابقه بعدی رو وارد کن:\n"
            f"فرمت: گل_تیم1-گل_تیم2\n"
            f"مثال: 3-2",
            reply_markup=self.keyboard.build_cancel_button()
        )
        
        return States.MATCH_RESULT
    
    async def finish_competition(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Finish and save all matches"""
        query = update.callback_query
        await query.answer()
        
        league_code = context.user_data['match_league']
        team1_ids = context.user_data['team1_players']
        team2_ids = context.user_data['team2_players']
        results = context.user_data['match_results']
        
        # Save each match
        saved_count = 0
        for result in results:
            self.match_service.create_match(
                league_code=league_code,
                team1=team1_ids,
                team2=team2_ids,
                team1_score=result['team1_score'],
                team2_score=result['team2_score']
            )
            saved_count += 1
        
        # Build summary
        team1_names = [self.user_service.get_user_by_telegram_id(tid).name for tid in team1_ids]
        team2_names = [self.user_service.get_user_by_telegram_id(tid).name for tid in team2_ids]
        team1_str = ' و '.join(team1_names)
        team2_str = ' و '.join(team2_names)
        
        league = self.league_service.get_league_by_code(league_code)
        
        # Calculate overall winner
        team1_wins = sum(1 for r in results if r['team1_score'] > r['team2_score'])
        team2_wins = sum(1 for r in results if r['team2_score'] > r['team1_score'])
        draws = sum(1 for r in results if r['team1_score'] == r['team2_score'])
        
        results_text = "\n📊 نتایج نهایی:\n"
        for i, r in enumerate(results, 1):
            emoji = "🏆" if r['team1_score'] > r['team2_score'] else "❌" if r['team1_score'] < r['team2_score'] else "🤝"
            results_text += f"{i}. {emoji} {r['team1_score']}-{r['team2_score']}\n"
        
        overall = f"\n🏅 نتیجه کلی:\n"
        overall += f"🏆 برد {team1_str}: {team1_wins}\n"
        overall += f"🏆 برد {team2_str}: {team2_wins}\n"
        if draws > 0:
            overall += f"🤝 مساوی: {draws}\n"
        
        if team1_wins > team2_wins:
            overall += f"\n🎉 برنده کلی: {team1_str}"
        elif team2_wins > team1_wins:
            overall += f"\n🎉 برنده کلی: {team2_str}"
        else:
            overall += f"\n🤝 نتیجه کلی مساوی!"
        
        text = f"""
✅ {saved_count} مسابقه با موفقیت ذخیره شد!

🏆 لیگ: {league.name}
👥 {team1_str} VS {team2_str}
{results_text}
{overall}
"""
        
        await query.edit_message_text(
            text,
            reply_markup=self.keyboard.build_back_button(f'select_league_{league_code}')
        )
        
        # Send notifications to all participants
        await self._send_match_notifications(query, context, team1_ids, team2_ids, results, league.name)
        
        # Clear context
        context.user_data.clear()
        
        return ConversationHandler.END
    
    async def _send_match_notifications(self, query, context, team1_ids, team2_ids, results, league_name):
        """Send match result notifications to all league members"""
        from telegram.error import TelegramError
        
        # Win/loss stickers (you can replace with your preferred sticker IDs)
        WIN_STICKER = "CAACAgQAAxkBAAEMHx5nOQdKVoE_4i3AXZLgBFQAAUUIhg8AAtUTAALb4uxT6h2SmO5DdwI2BA"  # Victory/celebration
        LOSS_STICKER = "CAACAgQAAxkBAAEMHyBnOQdZ8bxqAAHX6sBfmb3PW5gAAV4EAALmAAEZYH9P8IaYxY_I-tY2BA"  # Sad/loss
        
        league_code = context.user_data['match_league']
        league = self.league_service.get_league_by_code(league_code)
        
        if not league:
            return
        
        # Calculate points for each participant
        player_results = {}
        
        for telegram_id in team1_ids + team2_ids:
            wins = 0
            losses = 0
            draws = 0
            
            for result in results:
                if telegram_id in team1_ids:
                    if result['team1_score'] > result['team2_score']:
                        wins += 1
                    elif result['team1_score'] < result['team2_score']:
                        losses += 1
                    else:
                        draws += 1
                else:  # team2
                    if result['team2_score'] > result['team1_score']:
                        wins += 1
                    elif result['team2_score'] < result['team1_score']:
                        losses += 1
                    else:
                        draws += 1
            
            points = wins - losses
            player_results[telegram_id] = {
                'wins': wins,
                'losses': losses,
                'draws': draws,
                'points': points
            }
        
        # Build team names for message
        team1_names = [self.user_service.get_user_by_telegram_id(tid).name for tid in team1_ids]
        team2_names = [self.user_service.get_user_by_telegram_id(tid).name for tid in team2_ids]
        team1_str = ' و '.join(team1_names)
        team2_str = ' و '.join(team2_names)
        
        # Build results text
        results_text = "📊 نتایج:\n"
        for i, r in enumerate(results, 1):
            emoji = "🏆" if r['team1_score'] > r['team2_score'] else "❌" if r['team1_score'] < r['team2_score'] else "🤝"
            results_text += f"{i}. {emoji} {r['team1_score']}-{r['team2_score']}\n"
        
        # Send notifications to ALL league members
        all_members = league.members
        
        for telegram_id in all_members:
            # Skip the user who recorded the match
            if telegram_id == query.from_user.id:
                continue
            
            try:
                user = self.user_service.get_user_by_telegram_id(telegram_id)
                
                # Check if this user participated in the match
                is_participant = telegram_id in team1_ids or telegram_id in team2_ids
                
                if is_participant:
                    # Send detailed message with personal stats and sticker
                    stats = player_results[telegram_id]
                    
                    message = f"⚽ نتیجه مسابقات جدید در لیگ {league_name}\n\n"
                    message += f"👥 {team1_str} VS {team2_str}\n\n"
                    message += results_text
                    message += f"\n📈 آمار شما:\n"
                    message += f"برد: {stats['wins']} | باخت: {stats['losses']} | مساوی: {stats['draws']}\n"
                    message += f"امتیاز کسب شده: {stats['points']:+d}"
                    
                    # Choose sticker based on overall performance
                    sticker = WIN_STICKER if stats['points'] > 0 else LOSS_STICKER
                    
                    # Try to send sticker (optional, don't fail if it doesn't work)
                    try:
                        await context.bot.send_sticker(
                            chat_id=telegram_id,
                            sticker=sticker
                        )
                    except TelegramError:
                        pass  # Sticker failed, but continue to send message
                    
                    # Send message with keyboard
                    await context.bot.send_message(
                        chat_id=telegram_id,
                        text=message,
                        reply_markup=self.keyboard.build_league_update_menu(league_code)
                    )
                else:
                    # Send league update notification to non-participants
                    message = f"🔔 به‌روزرسانی لیگ {league_name}\n\n"
                    message += f"⚽ مسابقه جدید ثبت شد!\n\n"
                    message += f"👥 {team1_str} VS {team2_str}\n\n"
                    message += results_text
                    
                    # Send message with keyboard (no sticker for non-participants)
                    await context.bot.send_message(
                        chat_id=telegram_id,
                        text=message,
                        reply_markup=self.keyboard.build_league_update_menu(league_code)
                    )
                
            except TelegramError as e:
                # User might have blocked the bot or deleted account
                continue

