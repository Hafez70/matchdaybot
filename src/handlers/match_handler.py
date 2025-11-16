"""Match recording handler"""
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from .base_handler import BaseHandler
from ..config import States


class MatchHandler(BaseHandler):
    """Handles match recording"""
    
    async def record_match_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Start match recording - first select league"""
        query = update.callback_query
        await query.answer()
        
        # Extract league code from callback data
        league_code = query.data.split('_')[1]
        context.user_data['match_league'] = league_code
        
        league = self.league_service.get_league_by_code(league_code)
        if not league:
            await query.edit_message_text(
                "❌ لیگ پیدا نشد!",
                reply_markup=self.keyboard.build_back_button()
            )
            return ConversationHandler.END
        
        # Check if league has enough members
        if len(league.members) < 2:
            await query.edit_message_text(
                "⚠️ لیگ باید حداقل 2 عضو داشته باشه!\n"
                "ابتدا دوستانت رو دعوت کن.",
                reply_markup=self.keyboard.build_back_button(f'select_league_{league_code}')
            )
            return ConversationHandler.END
        
        await query.edit_message_text(
            f"⚽ ثبت مسابقه در لیگ {league.name}\n\n"
            "نوع مسابقه رو انتخاب کن:",
            reply_markup=self.keyboard.build_match_type_keyboard()
        )
        
        return States.MATCH_SELECT_TYPE
    
    async def match_type_selected(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle match type selection"""
        query = update.callback_query
        await query.answer()
        
        match_type = query.data.replace('match_type_', '')
        context.user_data['match_type'] = match_type
        
        league_code = context.user_data['match_league']
        league = self.league_service.get_league_by_code(league_code)
        
        # Get players in this league
        players = self.user_service.get_users_in_league(league_code)
        player_list = [(p.telegram_id, p.name) for p in players]
        
        type_text = self._get_match_type_text(match_type)
        
        await query.edit_message_text(
            f"✅ نوع مسابقه: {type_text}\n\n"
            f"👤 بازیکن {'اول ' if match_type in ['2v2', '2v1'] else ''}تیم 1 رو انتخاب کن:",
            reply_markup=self.keyboard.build_player_selection(
                player_list,
                'select_team1_p1'
            )
        )
        
        return States.MATCH_TEAM1_P1
    
    async def select_team1_player1(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Select first player of team 1"""
        query = update.callback_query
        await query.answer()
        
        telegram_id = int(query.data.replace('select_team1_p1_', ''))
        context.user_data['team1_p1'] = telegram_id
        
        user = self.user_service.get_user_by_telegram_id(telegram_id)
        match_type = context.user_data['match_type']
        league_code = context.user_data['match_league']
        
        # Check if we need second player for team 1
        if match_type in ['2v2', '2v1']:
            players = self.user_service.get_users_in_league(league_code)
            player_list = [(p.telegram_id, p.name) for p in players]
            
            await query.edit_message_text(
                f"✅ تیم 1 - بازیکن 1: {user.name}\n\n"
                f"👤 بازیکن دوم تیم 1 رو انتخاب کن:",
                reply_markup=self.keyboard.build_player_selection(
                    player_list,
                    'select_team1_p2',
                    exclude_ids=[telegram_id]
                )
            )
            return States.MATCH_TEAM1_P2
        else:
            # Move to team 2
            players = self.user_service.get_users_in_league(league_code)
            player_list = [(p.telegram_id, p.name) for p in players]
            
            await query.edit_message_text(
                f"✅ تیم 1: {user.name}\n\n"
                f"👤 بازیکن {'اول ' if match_type == '1v2' else ''}تیم 2 رو انتخاب کن:",
                reply_markup=self.keyboard.build_player_selection(
                    player_list,
                    'select_team2_p1',
                    exclude_ids=[telegram_id]
                )
            )
            return States.MATCH_TEAM2_P1
    
    async def select_team1_player2(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Select second player of team 1"""
        query = update.callback_query
        await query.answer()
        
        telegram_id = int(query.data.replace('select_team1_p2_', ''))
        context.user_data['team1_p2'] = telegram_id
        
        user = self.user_service.get_user_by_telegram_id(telegram_id)
        p1 = self.user_service.get_user_by_telegram_id(context.user_data['team1_p1'])
        
        league_code = context.user_data['match_league']
        players = self.user_service.get_users_in_league(league_code)
        player_list = [(p.telegram_id, p.name) for p in players]
        
        exclude = [context.user_data['team1_p1'], telegram_id]
        
        await query.edit_message_text(
            f"✅ تیم 1: {p1.name} و {user.name}\n\n"
            f"👤 بازیکن اول تیم 2 رو انتخاب کن:",
            reply_markup=self.keyboard.build_player_selection(
                player_list,
                'select_team2_p1',
                exclude_ids=exclude
            )
        )
        
        return States.MATCH_TEAM2_P1
    
    async def select_team2_player1(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Select first player of team 2"""
        query = update.callback_query
        await query.answer()
        
        telegram_id = int(query.data.replace('select_team2_p1_', ''))
        context.user_data['team2_p1'] = telegram_id
        
        user = self.user_service.get_user_by_telegram_id(telegram_id)
        match_type = context.user_data['match_type']
        
        # Check if we need second player for team 2
        if match_type in ['2v2', '1v2']:
            league_code = context.user_data['match_league']
            players = self.user_service.get_users_in_league(league_code)
            player_list = [(p.telegram_id, p.name) for p in players]
            
            exclude = [context.user_data['team1_p1'], 
                      context.user_data.get('team1_p2'), 
                      telegram_id]
            exclude = [x for x in exclude if x is not None]
            
            await query.edit_message_text(
                f"✅ تیم 2 - بازیکن 1: {user.name}\n\n"
                f"👤 بازیکن دوم تیم 2 رو انتخاب کن:",
                reply_markup=self.keyboard.build_player_selection(
                    player_list,
                    'select_team2_p2',
                    exclude_ids=exclude
                )
            )
            return States.MATCH_TEAM2_P2
        else:
            # Ready for result
            return await self._show_result_prompt(query, context)
    
    async def select_team2_player2(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Select second player of team 2"""
        query = update.callback_query
        await query.answer()
        
        telegram_id = int(query.data.replace('select_team2_p2_', ''))
        context.user_data['team2_p2'] = telegram_id
        
        return await self._show_result_prompt(query, context)
    
    async def _show_result_prompt(self, query, context) -> int:
        """Show result input prompt"""
        # Build team descriptions
        team1_ids = [context.user_data['team1_p1']]
        if 'team1_p2' in context.user_data:
            team1_ids.append(context.user_data['team1_p2'])
        
        team2_ids = [context.user_data['team2_p1']]
        if 'team2_p2' in context.user_data:
            team2_ids.append(context.user_data['team2_p2'])
        
        team1_names = [self.user_service.get_user_by_telegram_id(tid).name for tid in team1_ids]
        team2_names = [self.user_service.get_user_by_telegram_id(tid).name for tid in team2_ids]
        
        team1_str = ' و '.join(team1_names)
        team2_str = ' و '.join(team2_names)
        
        await query.edit_message_text(
            f"✅ تیم 1: {team1_str}\n"
            f"✅ تیم 2: {team2_str}\n\n"
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
        
        # Build teams
        team1_ids = [context.user_data['team1_p1']]
        if 'team1_p2' in context.user_data:
            team1_ids.append(context.user_data['team1_p2'])
        
        team2_ids = [context.user_data['team2_p1']]
        if 'team2_p2' in context.user_data:
            team2_ids.append(context.user_data['team2_p2'])
        
        # Save match
        league_code = context.user_data['match_league']
        match = self.match_service.create_match(
            league_code=league_code,
            team1=team1_ids,
            team2=team2_ids,
            team1_score=team1_score,
            team2_score=team2_score
        )
        
        # Build response
        team1_names = [self.user_service.get_user_by_telegram_id(tid).name for tid in team1_ids]
        team2_names = [self.user_service.get_user_by_telegram_id(tid).name for tid in team2_ids]
        
        team1_str = ' و '.join(team1_names)
        team2_str = ' و '.join(team2_names)
        
        winner = match.get_winner()
        winner_emoji = "🏆" if winner == 'team1' else "❌" if winner == 'team2' else "🤝"
        
        league = self.league_service.get_league_by_code(league_code)
        
        text = f"""
✅ مسابقه با موفقیت ثبت شد!

{winner_emoji} {team1_str} {team1_score}-{team2_score} {team2_str}

🏆 لیگ: {league.name}
🎮 نوع: {match.match_type}
"""
        
        await update.message.reply_text(
            text,
            reply_markup=self.keyboard.build_back_button(f'select_league_{league_code}')
        )
        
        # Clear context
        context.user_data.clear()
        
        return ConversationHandler.END
    
    def _get_match_type_text(self, match_type: str) -> str:
        """Get Persian text for match type"""
        types = {
            '1v1': 'تک نفره (1v1)',
            '2v2': 'دو نفره (2v2)',
            '1v2': 'یک به دو (1v2)',
            '2v1': 'دو به یک (2v1)'
        }
        return types.get(match_type, match_type)

