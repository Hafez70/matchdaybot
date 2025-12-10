import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dotenv import load_dotenv
import jdatetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters
)

# بارگذاری متغیرهای محیطی
load_dotenv()

# تنظیمات لاگ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# دریافت تنظیمات
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
DATA_FILE = 'fifa_data.json'

# States برای Conversation Handler - ثبت مسابقه
MATCH_SELECT_TYPE, MATCH_TEAM1_P1, MATCH_TEAM1_P2, MATCH_TEAM2_P1, MATCH_TEAM2_P2, MATCH_RESULT, MATCH_CONTINUE = range(7)

# States برای Conversation Handler - افزودن بازیکن
ADD_PLAYER_NAME = range(1)

# States برای Conversation Handler - جستجو
SEARCH_SELECT_PLAYER, SEARCH_VIEW_MATCHES = range(2)

# States برای Conversation Handler - آمار
STATS_SELECT_PLAYER = range(1)


class FifaDatabase:
    """کلاس مدیریت دیتابیس بازی‌های فیفا"""
    
    def __init__(self, data_file: str):
        self.data_file = data_file
        self.data = self._load_data()
    
    def _load_data(self) -> Dict:
        """بارگذاری داده‌ها از فایل"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"خطا در بارگذاری داده‌ها: {e}")
                return {'persons': [], 'matches': []}
        return {'persons': [], 'matches': []}
    
    def _save_data(self):
        """ذخیره داده‌ها در فایل"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            logger.info("داده‌ها با موفقیت ذخیره شدند")
        except Exception as e:
            logger.error(f"خطا در ذخیره داده‌ها: {e}")
    
    def add_person(self, name: str, telegram_id: Optional[int] = None) -> bool:
        """افزودن بازیکن جدید"""
        # بررسی تکراری نبودن
        if any(p['name'].lower() == name.lower() for p in self.data['persons']):
            return False
        
        person = {
            'id': len(self.data['persons']) + 1,
            'name': name,
            'telegram_id': telegram_id,
            'created_at': datetime.now().isoformat()
        }
        self.data['persons'].append(person)
        self._save_data()
        return True
    
    def get_all_persons(self) -> List[Dict]:
        """دریافت لیست تمام بازیکنان"""
        return self.data['persons']
    
    def find_person_by_name(self, name: str) -> Optional[Dict]:
        """جستجوی بازیکن با نام"""
        for person in self.data['persons']:
            if person['name'].lower() == name.lower():
                return person
        return None
    
    def add_match(self, match_data: Dict) -> int:
        """افزودن مسابقه جدید"""
        match_id = len(self.data['matches']) + 1
        match = {
            'id': match_id,
            'datetime': datetime.now().isoformat(),
            'type': match_data['type'],  # '1v1' or '2v2'
            'team1': match_data['team1'],  # لیست نام بازیکنان
            'team2': match_data['team2'],  # لیست نام بازیکنان
            'result': match_data['result']  # مثلاً {'team1': 3, 'team2': 2}
        }
        self.data['matches'].append(match)
        self._save_data()
        return match_id
    
    def get_matches_by_person(self, person_name: str) -> List[Dict]:
        """دریافت مسابقات یک بازیکن"""
        matches = []
        for match in self.data['matches']:
            if person_name in match['team1'] or person_name in match['team2']:
                matches.append(match)
        return matches
    
    def get_top_players(self, limit: int = 10) -> List[Dict]:
        """دریافت بازیکنان برتر بر اساس تعداد بازی"""
        player_stats = []
        
        for person in self.data['persons']:
            matches = self.get_matches_by_person(person['name'])
            player_stats.append({
                'name': person['name'],
                'matches_count': len(matches)
            })
        
        # مرتب‌سازی بر اساس تعداد بازی
        player_stats.sort(key=lambda x: x['matches_count'], reverse=True)
        
        return player_stats[:limit]
    
    def get_all_matches(self) -> List[Dict]:
        """دریافت تمام مسابقات"""
        return self.data['matches']
    
    def get_person_stats(self, person_name: str) -> Dict:
        """آمار یک بازیکن"""
        matches = self.get_matches_by_person(person_name)
        wins = 0
        losses = 0
        draws = 0
        total_goals_for = 0
        total_goals_against = 0
        
        for match in matches:
            is_team1 = person_name in match['team1']
            team_goals = match['result']['team1'] if is_team1 else match['result']['team2']
            opponent_goals = match['result']['team2'] if is_team1 else match['result']['team1']
            
            total_goals_for += team_goals
            total_goals_against += opponent_goals
            
            if team_goals > opponent_goals:
                wins += 1
            elif team_goals < opponent_goals:
                losses += 1
            else:
                draws += 1
        
        return {
            'total_matches': len(matches),
            'wins': wins,
            'losses': losses,
            'draws': draws,
            'goals_for': total_goals_for,
            'goals_against': total_goals_against,
            'goal_difference': total_goals_for - total_goals_against
        }


class FifaBot:
    """ربات فیفا"""
    
    def __init__(self):
        self.db = FifaDatabase(DATA_FILE)
    
    @staticmethod
    def to_persian_date(iso_datetime: str) -> str:
        """تبدیل تاریخ میلادی به شمسی"""
        dt = datetime.fromisoformat(iso_datetime)
        jdt = jdatetime.datetime.fromgregorian(datetime=dt)
        return jdt.strftime('%Y/%m/%d - %H:%M')
    
    def main_menu_keyboard(self) -> InlineKeyboardMarkup:
        """کیبورد منوی اصلی"""
        keyboard = [
            [InlineKeyboardButton("➕ افزودن بازیکن", callback_data='menu_add_player')],
            [InlineKeyboardButton("👥 لیست بازیکنان", callback_data='menu_list_players')],
            [InlineKeyboardButton("⚽ ثبت مسابقه", callback_data='menu_record_match')],
            [InlineKeyboardButton("🔍 جستجوی بازیکن", callback_data='menu_search')],
            [InlineKeyboardButton("📊 آمار بازیکن", callback_data='menu_stats')],
            [InlineKeyboardButton("🎮 آخرین مسابقات", callback_data='menu_matches')],
            [InlineKeyboardButton("❓ راهنما", callback_data='menu_help')]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def back_to_menu_keyboard(self) -> InlineKeyboardMarkup:
        """دکمه بازگشت به منو"""
        keyboard = [[InlineKeyboardButton("🔙 بازگشت به منو", callback_data='back_to_menu')]]
        return InlineKeyboardMarkup(keyboard)
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """دستور شروع و نمایش منوی اصلی"""
        user_name = update.effective_user.first_name
        
        welcome_text = f"""
🎮 سلام {user_name}! به ربات مسابقات فیفا خوش اومدی! ⚽

با این ربات می‌تونی:
• بازیکنان رو ثبت کنی
• نتایج مسابقات 1v1 و 2v2 رو ذخیره کنی
• آمار کامل و نتایج رو ببینی
• تاریخ‌ها به شمسی نمایش داده میشه

از منوی زیر استفاده کن 👇
"""
        await update.message.reply_text(
            welcome_text,
            reply_markup=self.main_menu_keyboard()
        )
    
    async def show_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمایش منوی اصلی"""
        query = update.callback_query
        if query:
            await query.answer()
            await query.edit_message_text(
                "🎮 منوی اصلی ⚽\n\nیکی از گزینه‌های زیر رو انتخاب کن:",
                reply_markup=self.main_menu_keyboard()
            )
        else:
            await update.message.reply_text(
                "🎮 منوی اصلی ⚽\n\nیکی از گزینه‌های زیر رو انتخاب کن:",
                reply_markup=self.main_menu_keyboard()
            )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمایش راهنما"""
        query = update.callback_query
        
        help_text = """
📖 راهنمای ربات فیفا

🎯 چطور استفاده کنم؟
از دکمه‌های منو استفاده کن! همه چیز ساده و واضحه.

➕ افزودن بازیکن:
از دکمه "افزودن بازیکن" استفاده کن و نام رو وارد کن.

⚽ ثبت مسابقه:
گام به گام ربات ازت می‌پرسه:
1. نوع مسابقه (1v1 یا 2v2)
2. بازیکنان تیم 1
3. بازیکنان تیم 2
4. نتیجه (مثلاً: 3-2)

🔍 جستجو و آمار:
• جستجو: مشاهده مسابقات یک بازیکن
• آمار: نمایش آمار کامل (برد، باخت، گل و...)

🎮 مسابقات اخیر:
نمایش 10 مسابقه آخر سیستم

💡 نکات:
• همه چیز با دکمه‌هاست، نیازی به تایپ دستور نیست
• تاریخ‌ها به شمسی نمایش داده میشه
• می‌تونی چند بار در روز مسابقه ثبت کنی
"""
        
        if query:
            await query.answer()
            await query.edit_message_text(
                help_text,
                reply_markup=self.back_to_menu_keyboard()
            )
        else:
            await update.message.reply_text(
                help_text,
                reply_markup=self.back_to_menu_keyboard()
            )
    
    async def add_player_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """شروع فرآیند افزودن بازیکن"""
        query = update.callback_query
        await query.answer()
        
        keyboard = [[InlineKeyboardButton("❌ لغو", callback_data='cancel_operation')]]
        
        await query.edit_message_text(
            "➕ افزودن بازیکن جدید\n\n"
            "👤 لطفاً نام بازیکن رو وارد کن:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        return ADD_PLAYER_NAME
    
    async def add_player_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """دریافت نام بازیکن و ذخیره"""
        player_name = update.message.text.strip()
        
        if self.db.add_person(player_name, update.effective_user.id):
            await update.message.reply_text(
                f"✅ بازیکن '{player_name}' با موفقیت اضافه شد!",
                reply_markup=self.back_to_menu_keyboard()
            )
        else:
            await update.message.reply_text(
                f"⚠️ بازیکن '{player_name}' قبلاً ثبت شده است!",
                reply_markup=self.back_to_menu_keyboard()
            )
        
        return ConversationHandler.END
    
    async def list_players(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمایش لیست بازیکنان"""
        query = update.callback_query
        await query.answer()
        
        persons = self.db.get_all_persons()
        
        if not persons:
            await query.edit_message_text(
                "📭 هنوز هیچ بازیکنی ثبت نشده!\n"
                "از دکمه 'افزودن بازیکن' استفاده کن.",
                reply_markup=self.back_to_menu_keyboard()
            )
            return
        
        text = "👥 لیست بازیکنان:\n\n"
        for i, person in enumerate(persons, 1):
            text += f"{i}. {person['name']}\n"
        
        text += f"\n📊 تعداد کل: {len(persons)} نفر"
        
        await query.edit_message_text(
            text,
            reply_markup=self.back_to_menu_keyboard()
        )
    
    async def record_match_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """شروع فرآیند ثبت مسابقه"""
        query = update.callback_query
        await query.answer()
        
        persons = self.db.get_all_persons()
        
        if len(persons) < 2:
            await query.edit_message_text(
                "⚠️ حداقل 2 بازیکن باید ثبت شده باشه!\n"
                "اول بازیکن اضافه کن.",
                reply_markup=self.back_to_menu_keyboard()
            )
            return ConversationHandler.END
        
        keyboard = [
            [InlineKeyboardButton("1️⃣ تک نفره (1v1)", callback_data='match_type_1v1')],
            [InlineKeyboardButton("2️⃣ دو نفره (2v2)", callback_data='match_type_2v2')],
            [InlineKeyboardButton("❌ لغو", callback_data='match_cancel')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "⚽ ثبت مسابقه جدید\n\n"
            "نوع مسابقه رو انتخاب کن:",
            reply_markup=reply_markup
        )
        
        return MATCH_SELECT_TYPE
    
    async def match_type_selected(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """انتخاب نوع مسابقه"""
        query = update.callback_query
        await query.answer()
        
        if query.data == 'match_cancel':
            await query.edit_message_text(
                "❌ ثبت مسابقه لغو شد.",
                reply_markup=self.back_to_menu_keyboard()
            )
            return ConversationHandler.END
        
        match_type = query.data.replace('match_type_', '')
        context.user_data['match_type'] = match_type
        context.user_data['match_data'] = {}
        
        type_text = "تک نفره" if match_type == '1v1' else "دو نفره"
        
        # دریافت top 10 بازیکنان
        top_players = self.db.get_top_players(10)
        all_persons = self.db.get_all_persons()
        
        # ساخت دکمه‌های انتخاب بازیکن
        keyboard = []
        
        if top_players:
            # دکمه‌های بازیکنان برتر (2 تا در هر ردیف)
            for i in range(0, len(top_players), 2):
                row = []
                for j in range(2):
                    if i + j < len(top_players):
                        player = top_players[i + j]
                        matches_emoji = "🔥" if player['matches_count'] > 10 else "⚽"
                        row.append(InlineKeyboardButton(
                            f"{matches_emoji} {player['name']} ({player['matches_count']})",
                            callback_data=f"select_player_team1_p1_{player['name']}"
                        ))
                keyboard.append(row)
            
            # خط جداکننده
            keyboard.append([InlineKeyboardButton("➖➖➖ سایر بازیکنان ➖➖➖", callback_data='ignore')])
            
            # بازیکنان دیگر (که در top 10 نیستن)
            top_names = [p['name'] for p in top_players]
            other_players = [p for p in all_persons if p['name'] not in top_names]
            
            for i in range(0, len(other_players), 2):
                row = []
                for j in range(2):
                    if i + j < len(other_players):
                        player = other_players[i + j]
                        row.append(InlineKeyboardButton(
                            f"👤 {player['name']}",
                            callback_data=f"select_player_team1_p1_{player['name']}"
                        ))
                keyboard.append(row)
        else:
            # اگه هیچ بازیکنی نیست
            for i in range(0, len(all_persons), 2):
                row = []
                for j in range(2):
                    if i + j < len(all_persons):
                        player = all_persons[i + j]
                        row.append(InlineKeyboardButton(
                            f"👤 {player['name']}",
                            callback_data=f"select_player_team1_p1_{player['name']}"
                        ))
                keyboard.append(row)
        
        # دکمه افزودن بازیکن جدید
        keyboard.append([InlineKeyboardButton("➕ بازیکن جدید", callback_data='add_new_player_inline_team1_p1')])
        keyboard.append([InlineKeyboardButton("❌ لغو", callback_data='cancel_operation')])
        
        await query.edit_message_text(
            f"✅ نوع مسابقه: {type_text} ({match_type})\n\n"
            f"👤 بازیکن اول تیم 1 رو انتخاب کن:\n"
            f"(🔥 = بیش از 10 بازی)",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        return MATCH_TEAM1_P1
    
    async def select_player_team1_p1(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """انتخاب بازیکن اول تیم 1 از دکمه"""
        query = update.callback_query
        await query.answer()
        
        player_name = query.data.replace('select_player_team1_p1_', '')
        context.user_data['team1_p1'] = player_name
        
        # نمایش دکمه‌های بازیکن بعدی
        if context.user_data['match_type'] == '2v2':
            await self.show_player_selection(
                query, context, 'team1_p2',
                f"✅ تیم 1 - بازیکن 1: {player_name}\n\n👤 بازیکن دوم تیم 1 رو انتخاب کن:",
                exclude_players=[player_name]
            )
            return MATCH_TEAM1_P2
        else:
            await self.show_player_selection(
                query, context, 'team2_p1',
                f"✅ تیم 1: {player_name}\n\n👤 بازیکن تیم 2 رو انتخاب کن:",
                exclude_players=[player_name]
            )
            return MATCH_TEAM2_P1
    
    async def select_player_team1_p2(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """انتخاب بازیکن دوم تیم 1 از دکمه"""
        query = update.callback_query
        await query.answer()
        
        player_name = query.data.replace('select_player_team1_p2_', '')
        context.user_data['team1_p2'] = player_name
        
        await self.show_player_selection(
            query, context, 'team2_p1',
            f"✅ تیم 1: {context.user_data['team1_p1']} و {player_name}\n\n👤 بازیکن اول تیم 2 رو انتخاب کن:",
            exclude_players=[context.user_data['team1_p1'], player_name]
        )
        return MATCH_TEAM2_P1
    
    async def select_player_team2_p1(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """انتخاب بازیکن اول تیم 2 از دکمه"""
        query = update.callback_query
        await query.answer()
        
        player_name = query.data.replace('select_player_team2_p1_', '')
        context.user_data['team2_p1'] = player_name
        
        if context.user_data['match_type'] == '2v2':
            exclude = [context.user_data['team1_p1'], context.user_data.get('team1_p2'), player_name]
            await self.show_player_selection(
                query, context, 'team2_p2',
                f"✅ تیم 2 - بازیکن 1: {player_name}\n\n👤 بازیکن دوم تیم 2 رو انتخاب کن:",
                exclude_players=exclude
            )
            return MATCH_TEAM2_P2
        else:
            # نتیجه رو بگیر
            keyboard = [[InlineKeyboardButton("❌ لغو", callback_data='cancel_operation')]]
            await query.edit_message_text(
                f"✅ تیم 1: {context.user_data['team1_p1']}\n"
                f"✅ تیم 2: {player_name}\n\n"
                f"⚽ نتیجه مسابقه رو وارد کن:\n"
                f"فرمت: گل_تیم1-گل_تیم2\n"
                f"مثال: 3-2",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return MATCH_RESULT
    
    async def select_player_team2_p2(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """انتخاب بازیکن دوم تیم 2 از دکمه"""
        query = update.callback_query
        await query.answer()
        
        player_name = query.data.replace('select_player_team2_p2_', '')
        context.user_data['team2_p2'] = player_name
        
        keyboard = [[InlineKeyboardButton("❌ لغو", callback_data='cancel_operation')]]
        await query.edit_message_text(
            f"✅ تیم 1: {context.user_data['team1_p1']} و {context.user_data['team1_p2']}\n"
            f"✅ تیم 2: {context.user_data['team2_p1']} و {player_name}\n\n"
            f"⚽ نتیجه مسابقه رو وارد کن:\n"
            f"فرمت: گل_تیم1-گل_تیم2\n"
            f"مثال: 5-3",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return MATCH_RESULT
    
    async def show_player_selection(self, query, context, step: str, message: str, exclude_players: List[str] = None):
        """نمایش دکمه‌های انتخاب بازیکن"""
        if exclude_players is None:
            exclude_players = []
        
        exclude_players = [p.lower() for p in exclude_players if p]
        
        # دریافت top 10 بازیکنان
        top_players = self.db.get_top_players(10)
        all_persons = self.db.get_all_persons()
        
        # فیلتر کردن بازیکنان استفاده شده
        top_players = [p for p in top_players if p['name'].lower() not in exclude_players]
        all_persons = [p for p in all_persons if p['name'].lower() not in exclude_players]
        
        # ساخت دکمه‌ها
        keyboard = []
        
        if top_players:
            # بازیکنان برتر
            for i in range(0, len(top_players), 2):
                row = []
                for j in range(2):
                    if i + j < len(top_players):
                        player = top_players[i + j]
                        matches_emoji = "🔥" if player['matches_count'] > 10 else "⚽"
                        row.append(InlineKeyboardButton(
                            f"{matches_emoji} {player['name']} ({player['matches_count']})",
                            callback_data=f"select_player_{step}_{player['name']}"
                        ))
                keyboard.append(row)
            
            # سایر بازیکنان
            top_names = [p['name'] for p in top_players]
            other_players = [p for p in all_persons if p['name'] not in top_names]
            
            if other_players:
                keyboard.append([InlineKeyboardButton("➖➖➖ سایر بازیکنان ➖➖➖", callback_data='ignore')])
                
                for i in range(0, len(other_players), 2):
                    row = []
                    for j in range(2):
                        if i + j < len(other_players):
                            player = other_players[i + j]
                            row.append(InlineKeyboardButton(
                                f"👤 {player['name']}",
                                callback_data=f"select_player_{step}_{player['name']}"
                            ))
                    keyboard.append(row)
        else:
            # همه بازیکنان
            for i in range(0, len(all_persons), 2):
                row = []
                for j in range(2):
                    if i + j < len(all_persons):
                        player = all_persons[i + j]
                        row.append(InlineKeyboardButton(
                            f"👤 {player['name']}",
                            callback_data=f"select_player_{step}_{player['name']}"
                        ))
                keyboard.append(row)
        
        # دکمه افزودن بازیکن جدید
        keyboard.append([InlineKeyboardButton("➕ بازیکن جدید", callback_data=f'add_new_player_inline_{step}')])
        keyboard.append([InlineKeyboardButton("❌ لغو", callback_data='cancel_operation')])
        
        await query.edit_message_text(
            message + "\n(🔥 = بیش از 10 بازی)",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def add_new_player_inline_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """شروع افزودن بازیکن جدید در حین انتخاب"""
        query = update.callback_query
        await query.answer()
        
        # ذخیره step برای بازگشت
        step = query.data.replace('add_new_player_inline_', '')
        context.user_data['add_player_return_step'] = step
        
        keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data=f'back_to_select_{step}')]]
        
        await query.edit_message_text(
            "➕ افزودن بازیکن جدید\n\n"
            "👤 نام بازیکن جدید رو وارد کن:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        return MATCH_TEAM1_P1  # یا هر state مناسب
    
    async def handle_new_player_name_inline(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """دریافت نام بازیکن جدید و افزودن"""
        player_name = update.message.text.strip()
        
        # چک کن آیا از قبل وجود داره
        existing = self.db.find_person_by_name(player_name)
        
        if existing:
            await update.message.reply_text(
                f"⚠️ بازیکن '{player_name}' از قبل وجود داره!\n"
                f"دوباره نام بازیکن رو وارد کن:"
            )
            return MATCH_TEAM1_P1
        
        # اضافه کردن بازیکن
        self.db.add_person(player_name, update.effective_user.id)
        
        # بازگشت به انتخاب
        step = context.user_data.get('add_player_return_step', 'team1_p1')
        
        # ساخت پیام مناسب
        if step == 'team1_p1':
            message = f"✅ بازیکن '{player_name}' اضافه شد و انتخاب شد!\n\n"
            context.user_data['team1_p1'] = player_name
            
            if context.user_data['match_type'] == '2v2':
                message += "👤 بازیکن دوم تیم 1 رو انتخاب کن:"
                keyboard = self._build_player_keyboard('team1_p2', [player_name])
                next_state = MATCH_TEAM1_P2
            else:
                message += "👤 بازیکن تیم 2 رو انتخاب کن:"
                keyboard = self._build_player_keyboard('team2_p1', [player_name])
                next_state = MATCH_TEAM2_P1
                
        elif step == 'team1_p2':
            context.user_data['team1_p2'] = player_name
            message = f"✅ بازیکن '{player_name}' اضافه شد و انتخاب شد!\n\n"
            message += "👤 بازیکن اول تیم 2 رو انتخاب کن:"
            exclude = [context.user_data['team1_p1'], player_name]
            keyboard = self._build_player_keyboard('team2_p1', exclude)
            next_state = MATCH_TEAM2_P1
            
        elif step == 'team2_p1':
            context.user_data['team2_p1'] = player_name
            message = f"✅ بازیکن '{player_name}' اضافه شد و انتخاب شد!\n\n"
            
            if context.user_data['match_type'] == '2v2':
                message += "👤 بازیکن دوم تیم 2 رو انتخاب کن:"
                exclude = [context.user_data['team1_p1'], context.user_data.get('team1_p2'), player_name]
                keyboard = self._build_player_keyboard('team2_p2', exclude)
                next_state = MATCH_TEAM2_P2
            else:
                keyboard = [[InlineKeyboardButton("❌ لغو", callback_data='cancel_operation')]]
                await update.message.reply_text(
                    f"✅ بازیکن '{player_name}' اضافه شد!\n"
                    f"✅ تیم 1: {context.user_data['team1_p1']}\n"
                    f"✅ تیم 2: {player_name}\n\n"
                    f"⚽ نتیجه مسابقه رو وارد کن:\n"
                    f"فرمت: گل_تیم1-گل_تیم2\n"
                    f"مثال: 3-2",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                return MATCH_RESULT
                
        elif step == 'team2_p2':
            context.user_data['team2_p2'] = player_name
            keyboard = [[InlineKeyboardButton("❌ لغو", callback_data='cancel_operation')]]
            await update.message.reply_text(
                f"✅ بازیکن '{player_name}' اضافه شد!\n"
                f"✅ تیم 1: {context.user_data['team1_p1']} و {context.user_data['team1_p2']}\n"
                f"✅ تیم 2: {context.user_data['team2_p1']} و {player_name}\n\n"
                f"⚽ نتیجه مسابقه رو وارد کن:\n"
                f"فرمت: گل_تیم1-گل_تیم2\n"
                f"مثال: 5-3",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return MATCH_RESULT
        
        await update.message.reply_text(
            message + "\n(🔥 = بیش از 10 بازی)",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        return next_state
    
    def _build_player_keyboard(self, step: str, exclude_players: List[str] = None):
        """ساخت کیبورد انتخاب بازیکن"""
        if exclude_players is None:
            exclude_players = []
        
        exclude_players = [p.lower() for p in exclude_players if p]
        
        top_players = self.db.get_top_players(10)
        all_persons = self.db.get_all_persons()
        
        top_players = [p for p in top_players if p['name'].lower() not in exclude_players]
        all_persons = [p for p in all_persons if p['name'].lower() not in exclude_players]
        
        keyboard = []
        
        if top_players:
            for i in range(0, len(top_players), 2):
                row = []
                for j in range(2):
                    if i + j < len(top_players):
                        player = top_players[i + j]
                        matches_emoji = "🔥" if player['matches_count'] > 10 else "⚽"
                        row.append(InlineKeyboardButton(
                            f"{matches_emoji} {player['name']} ({player['matches_count']})",
                            callback_data=f"select_player_{step}_{player['name']}"
                        ))
                keyboard.append(row)
            
            top_names = [p['name'] for p in top_players]
            other_players = [p for p in all_persons if p['name'] not in top_names]
            
            if other_players:
                keyboard.append([InlineKeyboardButton("➖➖➖ سایر بازیکنان ➖➖➖", callback_data='ignore')])
                for i in range(0, len(other_players), 2):
                    row = []
                    for j in range(2):
                        if i + j < len(other_players):
                            player = other_players[i + j]
                            row.append(InlineKeyboardButton(
                                f"👤 {player['name']}",
                                callback_data=f"select_player_{step}_{player['name']}"
                            ))
                    keyboard.append(row)
        else:
            for i in range(0, len(all_persons), 2):
                row = []
                for j in range(2):
                    if i + j < len(all_persons):
                        player = all_persons[i + j]
                        row.append(InlineKeyboardButton(
                            f"👤 {player['name']}",
                            callback_data=f"select_player_{step}_{player['name']}"
                        ))
                keyboard.append(row)
        
        keyboard.append([InlineKeyboardButton("➕ بازیکن جدید", callback_data=f'add_new_player_inline_{step}')])
        keyboard.append([InlineKeyboardButton("❌ لغو", callback_data='cancel_operation')])
        
        return keyboard
    
    async def team1_player1(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """دریافت بازیکن اول تیم 1"""
        player_name = update.message.text.strip()
        
        # چک کردن وجود بازیکن (exact match)
        existing_player = self.db.find_person_by_name(player_name)
        
        if existing_player:
            # بازیکن پیدا شد، ادامه بده
            context.user_data['team1_p1'] = existing_player['name']
            
            persons = self.db.get_all_persons()
            players_list = "\n".join([f"• {p['name']}" for p in persons])
            
            if context.user_data['match_type'] == '2v2':
                keyboard = [[InlineKeyboardButton("❌ لغو", callback_data='cancel_operation')]]
                await update.message.reply_text(
                    f"✅ تیم 1 - بازیکن 1: {existing_player['name']}\n\n"
                    f"👥 لیست بازیکنان:\n{players_list}\n\n"
                    f"👤 نام بازیکن دوم تیم 1 رو وارد کن:",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                return MATCH_TEAM1_P2
            else:
                keyboard = [[InlineKeyboardButton("❌ لغو", callback_data='cancel_operation')]]
                await update.message.reply_text(
                    f"✅ تیم 1: {existing_player['name']}\n\n"
                    f"👥 لیست بازیکنان:\n{players_list}\n\n"
                    f"👤 نام بازیکن تیم 2 رو وارد کن:",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                return MATCH_TEAM2_P1
        else:
            # بازیکن وجود نداره - بپرس می‌خوای اضافه کنم؟
            context.user_data['pending_player_name'] = player_name
            context.user_data['pending_step'] = 'team1_p1'
            
            keyboard = [
                [InlineKeyboardButton("✅ بله، اضافه کن", callback_data='add_new_player_yes')],
                [InlineKeyboardButton("❌ خیر، اسم دیگه‌ای وارد می‌کنم", callback_data='add_new_player_no')],
                [InlineKeyboardButton("🔙 لغو", callback_data='cancel_operation')]
            ]
            
            await update.message.reply_text(
                f"❓ بازیکن '{player_name}' در لیست وجود نداره.\n\n"
                f"می‌خوای اضافه‌ش کنم؟",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return MATCH_TEAM1_P1
    
    async def team1_player2(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """دریافت بازیکن دوم تیم 1 (برای 2v2)"""
        player_name = update.message.text.strip()
        
        # چک کردن تکراری نبودن
        if player_name.lower() == context.user_data['team1_p1'].lower():
            await update.message.reply_text(
                "❌ این بازیکن قبلاً انتخاب شده!\n"
                "نام بازیکن دیگری رو وارد کن:"
            )
            return MATCH_TEAM1_P2
        
        # چک کردن وجود بازیکن
        existing_player = self.db.find_person_by_name(player_name)
        
        if existing_player:
            context.user_data['team1_p2'] = existing_player['name']
            
            persons = self.db.get_all_persons()
            players_list = "\n".join([f"• {p['name']}" for p in persons])
            
            keyboard = [[InlineKeyboardButton("❌ لغو", callback_data='cancel_operation')]]
            await update.message.reply_text(
                f"✅ تیم 1: {context.user_data['team1_p1']} و {existing_player['name']}\n\n"
                f"👥 لیست بازیکنان:\n{players_list}\n\n"
                f"👤 نام بازیکن اول تیم 2 رو وارد کن:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return MATCH_TEAM2_P1
        else:
            # بازیکن جدیده
            context.user_data['pending_player_name'] = player_name
            context.user_data['pending_step'] = 'team1_p2'
            
            keyboard = [
                [InlineKeyboardButton("✅ بله، اضافه کن", callback_data='add_new_player_yes')],
                [InlineKeyboardButton("❌ خیر، اسم دیگه‌ای وارد می‌کنم", callback_data='add_new_player_no')],
                [InlineKeyboardButton("🔙 لغو", callback_data='cancel_operation')]
            ]
            
            await update.message.reply_text(
                f"❓ بازیکن '{player_name}' در لیست وجود نداره.\n\n"
                f"می‌خوای اضافه‌ش کنم؟",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return MATCH_TEAM1_P2
    
    async def team2_player1(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """دریافت بازیکن اول تیم 2"""
        player_name = update.message.text.strip()
        
        # بررسی تکراری نبودن
        used_players = [context.user_data.get('team1_p1'), context.user_data.get('team1_p2')]
        used_players = [p.lower() for p in used_players if p]
        
        if player_name.lower() in used_players:
            await update.message.reply_text(
                "❌ این بازیکن قبلاً در تیم 1 انتخاب شده!\n"
                "نام بازیکن دیگری رو وارد کن:"
            )
            return MATCH_TEAM2_P1
        
        # چک کردن وجود بازیکن
        existing_player = self.db.find_person_by_name(player_name)
        
        if existing_player:
            context.user_data['team2_p1'] = existing_player['name']
            
            persons = self.db.get_all_persons()
            players_list = "\n".join([f"• {p['name']}" for p in persons])
            
            if context.user_data['match_type'] == '2v2':
                keyboard = [[InlineKeyboardButton("❌ لغو", callback_data='cancel_operation')]]
                await update.message.reply_text(
                    f"✅ تیم 2 - بازیکن 1: {existing_player['name']}\n\n"
                    f"👥 لیست بازیکنان:\n{players_list}\n\n"
                    f"👤 نام بازیکن دوم تیم 2 رو وارد کن:",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                return MATCH_TEAM2_P2
            else:
                keyboard = [[InlineKeyboardButton("❌ لغو", callback_data='cancel_operation')]]
                await update.message.reply_text(
                    f"✅ تیم 2: {existing_player['name']}\n\n"
                    f"⚽ نتیجه مسابقه رو وارد کن:\n"
                    f"فرمت: گل_تیم1-گل_تیم2\n"
                    f"مثال: 3-2",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                return MATCH_RESULT
        else:
            # بازیکن جدیده
            context.user_data['pending_player_name'] = player_name
            context.user_data['pending_step'] = 'team2_p1'
            
            keyboard = [
                [InlineKeyboardButton("✅ بله، اضافه کن", callback_data='add_new_player_yes')],
                [InlineKeyboardButton("❌ خیر، اسم دیگه‌ای وارد می‌کنم", callback_data='add_new_player_no')],
                [InlineKeyboardButton("🔙 لغو", callback_data='cancel_operation')]
            ]
            
            await update.message.reply_text(
                f"❓ بازیکن '{player_name}' در لیست وجود نداره.\n\n"
                f"می‌خوای اضافه‌ش کنم؟",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return MATCH_TEAM2_P1
    
    async def team2_player2(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """دریافت بازیکن دوم تیم 2 (برای 2v2)"""
        player_name = update.message.text.strip()
        
        # بررسی تکراری نبودن
        used_players = [
            context.user_data.get('team1_p1'),
            context.user_data.get('team1_p2'),
            context.user_data.get('team2_p1')
        ]
        used_players = [p.lower() for p in used_players if p]
        
        if player_name.lower() in used_players:
            await update.message.reply_text(
                "❌ این بازیکن قبلاً انتخاب شده!\n"
                "نام بازیکن دیگری رو وارد کن:"
            )
            return MATCH_TEAM2_P2
        
        # چک کردن وجود بازیکن
        existing_player = self.db.find_person_by_name(player_name)
        
        if existing_player:
            context.user_data['team2_p2'] = existing_player['name']
            
            keyboard = [[InlineKeyboardButton("❌ لغو", callback_data='cancel_operation')]]
            await update.message.reply_text(
                f"✅ تیم 2: {context.user_data['team2_p1']} و {existing_player['name']}\n\n"
                f"⚽ نتیجه مسابقه رو وارد کن:\n"
                f"فرمت: گل_تیم1-گل_تیم2\n"
                f"مثال: 5-3",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return MATCH_RESULT
        else:
            # بازیکن جدیده
            context.user_data['pending_player_name'] = player_name
            context.user_data['pending_step'] = 'team2_p2'
            
            keyboard = [
                [InlineKeyboardButton("✅ بله، اضافه کن", callback_data='add_new_player_yes')],
                [InlineKeyboardButton("❌ خیر، اسم دیگه‌ای وارد می‌کنم", callback_data='add_new_player_no')],
                [InlineKeyboardButton("🔙 لغو", callback_data='cancel_operation')]
            ]
            
            await update.message.reply_text(
                f"❓ بازیکن '{player_name}' در لیست وجود نداره.\n\n"
                f"می‌خوای اضافه‌ش کنم؟",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return MATCH_TEAM2_P2
    
    async def match_result(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """دریافت نتیجه مسابقه و ذخیره"""
        result_text = update.message.text.strip()
        
        # پارس کردن نتیجه
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
                "مثال: 3-2"
            )
            return MATCH_RESULT
        
        # ساخت تیم‌ها
        team1 = [context.user_data['team1_p1']]
        if context.user_data['match_type'] == '2v2':
            team1.append(context.user_data['team1_p2'])
        
        team2 = [context.user_data['team2_p1']]
        if context.user_data['match_type'] == '2v2':
            team2.append(context.user_data['team2_p2'])
        
        # ذخیره مسابقه
        match_data = {
            'type': context.user_data['match_type'],
            'team1': team1,
            'team2': team2,
            'result': {
                'team1': team1_score,
                'team2': team2_score
            }
        }
        
        match_id = self.db.add_match(match_data)
        
        # ذخیره در لیست نتایج
        if 'recorded_matches' not in context.user_data:
            context.user_data['recorded_matches'] = []
        
        context.user_data['recorded_matches'].append({
            'id': match_id,
            'team1_score': team1_score,
            'team2_score': team2_score,
            'team1': team1,
            'team2': team2
        })
        
        # نمایش پیام و دکمه‌ها برای ادامه
        team1_str = ' و '.join(team1)
        team2_str = ' و '.join(team2)
        
        winner_emoji = ""
        if team1_score > team2_score:
            winner_emoji = "🏆"
        elif team2_score > team1_score:
            winner_emoji = "❌"
        else:
            winner_emoji = "🤝"
        
        matches_count = len(context.user_data['recorded_matches'])
        
        keyboard = [
            [InlineKeyboardButton("➕ ثبت مسابقه بعدی", callback_data='continue_matches')],
            [InlineKeyboardButton("✅ پایان و نمایش نتایج", callback_data='finish_matches')],
            [InlineKeyboardButton("❌ لغو", callback_data='cancel_operation')]
        ]
        
        summary = f"""
✅ مسابقه #{matches_count} ثبت شد!

{winner_emoji} {team1_str} {team1_score}-{team2_score} {team2_str}

📊 تعداد مسابقات ثبت شده: {matches_count}

می‌خوای مسابقه بعدی رو ثبت کنی؟
"""
        
        await update.message.reply_text(
            summary,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        return MATCH_CONTINUE
    
    async def continue_matches(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """ادامه ثبت مسابقه با همون تیم‌ها"""
        query = update.callback_query
        await query.answer()
        
        # نمایش تیم‌ها و درخواست نتیجه جدید
        team1 = [context.user_data['team1_p1']]
        if context.user_data['match_type'] == '2v2':
            team1.append(context.user_data['team1_p2'])
        
        team2 = [context.user_data['team2_p1']]
        if context.user_data['match_type'] == '2v2':
            team2.append(context.user_data['team2_p2'])
        
        team1_str = ' و '.join(team1)
        team2_str = ' و '.join(team2)
        
        keyboard = [[InlineKeyboardButton("❌ لغو", callback_data='cancel_operation')]]
        
        await query.edit_message_text(
            f"⚽ مسابقه بعدی\n\n"
            f"👥 تیم 1: {team1_str}\n"
            f"👥 تیم 2: {team2_str}\n\n"
            f"⚽ نتیجه مسابقه رو وارد کن:\n"
            f"فرمت: گل_تیم1-گل_تیم2\n"
            f"مثال: 3-2",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        return MATCH_RESULT
    
    async def finish_matches(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمایش خلاصه همه نتایج و پایان"""
        query = update.callback_query
        await query.answer()
        
        recorded_matches = context.user_data.get('recorded_matches', [])
        
        if not recorded_matches:
            await query.edit_message_text(
                "❌ هیچ مسابقه‌ای ثبت نشده!",
                reply_markup=self.back_to_menu_keyboard()
            )
            context.user_data.clear()
            return ConversationHandler.END
        
        # محاسبه آمار کلی
        team1_total_wins = 0
        team2_total_wins = 0
        draws = 0
        
        for match in recorded_matches:
            if match['team1_score'] > match['team2_score']:
                team1_total_wins += 1
            elif match['team2_score'] > match['team1_score']:
                team2_total_wins += 1
            else:
                draws += 1
        
        # ساخت پیام خلاصه
        team1_str = ' و '.join(recorded_matches[0]['team1'])
        team2_str = ' و '.join(recorded_matches[0]['team2'])
        
        summary = f"""
🏁 خلاصه مسابقات

👥 تیم 1: {team1_str}
👥 تیم 2: {team2_str}

📊 تعداد مسابقات: {len(recorded_matches)}

"""
        
        # نمایش نتایج تک تک
        for i, match in enumerate(recorded_matches, 1):
            winner_emoji = ""
            if match['team1_score'] > match['team2_score']:
                winner_emoji = "🏆"
            elif match['team2_score'] > match['team1_score']:
                winner_emoji = "❌"
            else:
                winner_emoji = "🤝"
            
            summary += f"{i}. {winner_emoji} {match['team1_score']}-{match['team2_score']}\n"
        
        summary += f"\n📈 آمار کلی:\n"
        summary += f"🏆 برد {team1_str}: {team1_total_wins}\n"
        summary += f"🏆 برد {team2_str}: {team2_total_wins}\n"
        if draws > 0:
            summary += f"🤝 مساوی: {draws}\n"
        
        # تعیین برنده کلی
        if team1_total_wins > team2_total_wins:
            summary += f"\n🎉 برنده کلی: {team1_str}"
        elif team2_total_wins > team1_total_wins:
            summary += f"\n🎉 برنده کلی: {team2_str}"
        else:
            summary += f"\n🤝 نتیجه کلی مساوی!"
        
        # دکمه‌های پایانی
        keyboard = [
            [InlineKeyboardButton("⚽ مسابقه جدید", callback_data='menu_record_match')],
            [InlineKeyboardButton("🔙 منوی اصلی", callback_data='back_to_menu')]
        ]
        
        await query.edit_message_text(
            summary,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        # پاک کردن داده‌های موقت
        context.user_data.clear()
        
        return ConversationHandler.END
    
    async def handle_add_new_player(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """مدیریت اضافه کردن بازیکن جدید در حین ثبت مسابقه"""
        query = update.callback_query
        await query.answer()
        
        if query.data == 'add_new_player_yes':
            # اضافه کردن بازیکن
            player_name = context.user_data.get('pending_player_name')
            self.db.add_person(player_name, update.effective_user.id)
            
            step = context.user_data.get('pending_step')
            
            if step == 'team1_p1':
                context.user_data['team1_p1'] = player_name
                
                persons = self.db.get_all_persons()
                players_list = "\n".join([f"• {p['name']}" for p in persons])
                
                if context.user_data['match_type'] == '2v2':
                    keyboard = [[InlineKeyboardButton("❌ لغو", callback_data='cancel_operation')]]
                    await query.edit_message_text(
                        f"✅ بازیکن '{player_name}' اضافه شد!\n"
                        f"✅ تیم 1 - بازیکن 1: {player_name}\n\n"
                        f"👥 لیست بازیکنان:\n{players_list}\n\n"
                        f"👤 نام بازیکن دوم تیم 1 رو وارد کن:",
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                    return MATCH_TEAM1_P2
                else:
                    keyboard = [[InlineKeyboardButton("❌ لغو", callback_data='cancel_operation')]]
                    await query.edit_message_text(
                        f"✅ بازیکن '{player_name}' اضافه شد!\n"
                        f"✅ تیم 1: {player_name}\n\n"
                        f"👥 لیست بازیکنان:\n{players_list}\n\n"
                        f"👤 نام بازیکن تیم 2 رو وارد کن:",
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                    return MATCH_TEAM2_P1
                    
            elif step == 'team1_p2':
                context.user_data['team1_p2'] = player_name
                
                persons = self.db.get_all_persons()
                players_list = "\n".join([f"• {p['name']}" for p in persons])
                
                keyboard = [[InlineKeyboardButton("❌ لغو", callback_data='cancel_operation')]]
                await query.edit_message_text(
                    f"✅ بازیکن '{player_name}' اضافه شد!\n"
                    f"✅ تیم 1: {context.user_data['team1_p1']} و {player_name}\n\n"
                    f"👥 لیست بازیکنان:\n{players_list}\n\n"
                    f"👤 نام بازیکن اول تیم 2 رو وارد کن:",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                return MATCH_TEAM2_P1
                
            elif step == 'team2_p1':
                context.user_data['team2_p1'] = player_name
                
                persons = self.db.get_all_persons()
                players_list = "\n".join([f"• {p['name']}" for p in persons])
                
                if context.user_data['match_type'] == '2v2':
                    keyboard = [[InlineKeyboardButton("❌ لغو", callback_data='cancel_operation')]]
                    await query.edit_message_text(
                        f"✅ بازیکن '{player_name}' اضافه شد!\n"
                        f"✅ تیم 2 - بازیکن 1: {player_name}\n\n"
                        f"👥 لیست بازیکنان:\n{players_list}\n\n"
                        f"👤 نام بازیکن دوم تیم 2 رو وارد کن:",
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                    return MATCH_TEAM2_P2
                else:
                    keyboard = [[InlineKeyboardButton("❌ لغو", callback_data='cancel_operation')]]
                    await query.edit_message_text(
                        f"✅ بازیکن '{player_name}' اضافه شد!\n"
                        f"✅ تیم 2: {player_name}\n\n"
                        f"⚽ نتیجه مسابقه رو وارد کن:\n"
                        f"فرمت: گل_تیم1-گل_تیم2\n"
                        f"مثال: 3-2",
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                    return MATCH_RESULT
                    
            elif step == 'team2_p2':
                context.user_data['team2_p2'] = player_name
                
                keyboard = [[InlineKeyboardButton("❌ لغو", callback_data='cancel_operation')]]
                await query.edit_message_text(
                    f"✅ بازیکن '{player_name}' اضافه شد!\n"
                    f"✅ تیم 2: {context.user_data['team2_p1']} و {player_name}\n\n"
                    f"⚽ نتیجه مسابقه رو وارد کن:\n"
                    f"فرمت: گل_تیم1-گل_تیم2\n"
                    f"مثال: 5-3",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                return MATCH_RESULT
                
        elif query.data == 'add_new_player_no':
            # کاربر نمی‌خواد اضافه کنه، دوباره بپرس
            step = context.user_data.get('pending_step')
            
            persons = self.db.get_all_persons()
            players_list = "\n".join([f"• {p['name']}" for p in persons])
            
            keyboard = [[InlineKeyboardButton("❌ لغو", callback_data='cancel_operation')]]
            await query.edit_message_text(
                f"👥 لیست بازیکنان:\n{players_list}\n\n"
                f"👤 لطفاً نام بازیکن رو وارد کن:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
            if step == 'team1_p1':
                return MATCH_TEAM1_P1
            elif step == 'team1_p2':
                return MATCH_TEAM1_P2
            elif step == 'team2_p1':
                return MATCH_TEAM2_P1
            elif step == 'team2_p2':
                return MATCH_TEAM2_P2
    
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """لغو عملیات از طریق دکمه"""
        query = update.callback_query
        if query:
            await query.answer()
            await query.edit_message_text(
                "❌ عملیات لغو شد.",
                reply_markup=self.back_to_menu_keyboard()
            )
        else:
            await update.message.reply_text(
                "❌ عملیات لغو شد.",
                reply_markup=self.back_to_menu_keyboard()
            )
        context.user_data.clear()
        return ConversationHandler.END
    
    async def search_player_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """شروع جستجوی بازیکن"""
        query = update.callback_query
        await query.answer()
        
        persons = self.db.get_all_persons()
        
        if not persons:
            await query.edit_message_text(
                "📭 هنوز هیچ بازیکنی ثبت نشده!",
                reply_markup=self.back_to_menu_keyboard()
            )
            return ConversationHandler.END
        
        # ساخت دکمه‌های انتخاب بازیکن
        keyboard = []
        for person in persons:
            keyboard.append([InlineKeyboardButton(
                f"👤 {person['name']}",
                callback_data=f"search_{person['name']}"
            )])
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_menu')])
        
        await query.edit_message_text(
            "🔍 جستجوی مسابقات بازیکن\n\n"
            "یک بازیکن رو انتخاب کن:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        return SEARCH_SELECT_PLAYER
    
    async def search_player_selected(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمایش مسابقات بازیکن انتخاب شده"""
        query = update.callback_query
        await query.answer()
        
        if query.data == 'back_to_menu':
            await self.show_main_menu(update, context)
            return ConversationHandler.END
        
        player_name = query.data.replace('search_', '')
        
        matches = self.db.get_matches_by_person(player_name)
        
        if not matches:
            await query.edit_message_text(
                f"📭 هیچ مسابقه‌ای برای '{player_name}' ثبت نشده!",
                reply_markup=self.back_to_menu_keyboard()
            )
            return ConversationHandler.END
        
        text = f"⚽ مسابقات {player_name}:\n\n"
        
        for i, match in enumerate(reversed(matches[-10:]), 1):  # آخرین 10 تا
            team1_str = ' و '.join(match['team1'])
            team2_str = ' و '.join(match['team2'])
            date_str = self.to_persian_date(match['datetime'])
            
            result_emoji = ""
            if player_name in match['team1']:
                if match['result']['team1'] > match['result']['team2']:
                    result_emoji = "🏆"
                elif match['result']['team1'] < match['result']['team2']:
                    result_emoji = "❌"
                else:
                    result_emoji = "🤝"
            else:
                if match['result']['team2'] > match['result']['team1']:
                    result_emoji = "🏆"
                elif match['result']['team2'] < match['result']['team1']:
                    result_emoji = "❌"
                else:
                    result_emoji = "🤝"
            
            text += f"{i}. {result_emoji} {team1_str} {match['result']['team1']}-{match['result']['team2']} {team2_str}\n"
            text += f"   📅 {date_str}\n\n"
        
        if len(matches) > 10:
            text += f"📊 و {len(matches) - 10} مسابقه دیگر..."
        
        await query.edit_message_text(
            text,
            reply_markup=self.back_to_menu_keyboard()
        )
        
        return ConversationHandler.END
    
    async def stats_player_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """شروع مشاهده آمار بازیکن"""
        query = update.callback_query
        await query.answer()
        
        persons = self.db.get_all_persons()
        
        if not persons:
            await query.edit_message_text(
                "📭 هنوز هیچ بازیکنی ثبت نشده!",
                reply_markup=self.back_to_menu_keyboard()
            )
            return ConversationHandler.END
        
        # ساخت دکمه‌های انتخاب بازیکن
        keyboard = []
        for person in persons:
            keyboard.append([InlineKeyboardButton(
                f"👤 {person['name']}",
                callback_data=f"stats_{person['name']}"
            )])
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_menu')])
        
        await query.edit_message_text(
            "📊 آمار بازیکن\n\n"
            "یک بازیکن رو انتخاب کن:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        return STATS_SELECT_PLAYER
    
    async def stats_player_selected(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمایش آمار بازیکن انتخاب شده"""
        query = update.callback_query
        await query.answer()
        
        if query.data == 'back_to_menu':
            await self.show_main_menu(update, context)
            return ConversationHandler.END
        
        player_name = query.data.replace('stats_', '')
        
        stats = self.db.get_person_stats(player_name)
        
        if stats['total_matches'] == 0:
            await query.edit_message_text(
                f"📭 هیچ مسابقه‌ای برای '{player_name}' ثبت نشده!",
                reply_markup=self.back_to_menu_keyboard()
            )
            return ConversationHandler.END
        
        win_rate = (stats['wins'] / stats['total_matches'] * 100) if stats['total_matches'] > 0 else 0
        
        text = f"""
📊 آمار {player_name}

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
            reply_markup=self.back_to_menu_keyboard()
        )
        
        return ConversationHandler.END
    
    async def recent_matches(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمایش آخرین مسابقات"""
        query = update.callback_query
        await query.answer()
        
        matches = self.db.get_all_matches()
        
        if not matches:
            await query.edit_message_text(
                "📭 هنوز هیچ مسابقه‌ای ثبت نشده!",
                reply_markup=self.back_to_menu_keyboard()
            )
            return
        
        text = "⚽ آخرین مسابقات:\n\n"
        
        for i, match in enumerate(reversed(matches[-10:]), 1):
            team1_str = ' و '.join(match['team1'])
            team2_str = ' و '.join(match['team2'])
            date_str = self.to_persian_date(match['datetime'])
            
            winner = ""
            if match['result']['team1'] > match['result']['team2']:
                winner = "🏆"
            elif match['result']['team1'] < match['result']['team2']:
                winner = "🏆"
            else:
                winner = "🤝"
            
            text += f"{i}. {team1_str} {match['result']['team1']}-{match['result']['team2']} {team2_str} {winner}\n"
            text += f"   📅 {date_str} | {match['type']}\n\n"
        
        if len(matches) > 10:
            text += f"📊 و {len(matches) - 10} مسابقه دیگر..."
        
        await query.edit_message_text(
            text,
            reply_markup=self.back_to_menu_keyboard()
        )


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مدیریت خطاها"""
    logger.error(f"خطا در آپدیت {update}: {context.error}")


def main():
    """تابع اصلی"""
    
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN تنظیم نشده است!")
        return
    
    # ساخت instance از ربات
    bot = FifaBot()
    
    # ساخت application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Conversation handler برای افزودن بازیکن
    add_player_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(bot.add_player_start, pattern='^menu_add_player$')],
        states={
            ADD_PLAYER_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, bot.add_player_name),
                CallbackQueryHandler(bot.cancel, pattern='^cancel_operation$')
            ],
        },
        fallbacks=[CallbackQueryHandler(bot.cancel, pattern='^cancel_operation$')],
    )
    
    # Conversation handler برای ثبت مسابقه
    match_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(bot.record_match_start, pattern='^menu_record_match$')],
        states={
            MATCH_SELECT_TYPE: [CallbackQueryHandler(bot.match_type_selected)],
            MATCH_TEAM1_P1: [
                CallbackQueryHandler(bot.select_player_team1_p1, pattern='^select_player_team1_p1_'),
                CallbackQueryHandler(bot.add_new_player_inline_start, pattern='^add_new_player_inline_team1_p1$'),
                MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_new_player_name_inline),
                CallbackQueryHandler(bot.cancel, pattern='^cancel_operation$')
            ],
            MATCH_TEAM1_P2: [
                CallbackQueryHandler(bot.select_player_team1_p2, pattern='^select_player_team1_p2_'),
                CallbackQueryHandler(bot.add_new_player_inline_start, pattern='^add_new_player_inline_team1_p2$'),
                MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_new_player_name_inline),
                CallbackQueryHandler(bot.cancel, pattern='^cancel_operation$')
            ],
            MATCH_TEAM2_P1: [
                CallbackQueryHandler(bot.select_player_team2_p1, pattern='^select_player_team2_p1_'),
                CallbackQueryHandler(bot.add_new_player_inline_start, pattern='^add_new_player_inline_team2_p1$'),
                MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_new_player_name_inline),
                CallbackQueryHandler(bot.cancel, pattern='^cancel_operation$')
            ],
            MATCH_TEAM2_P2: [
                CallbackQueryHandler(bot.select_player_team2_p2, pattern='^select_player_team2_p2_'),
                CallbackQueryHandler(bot.add_new_player_inline_start, pattern='^add_new_player_inline_team2_p2$'),
                MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_new_player_name_inline),
                CallbackQueryHandler(bot.cancel, pattern='^cancel_operation$')
            ],
            MATCH_RESULT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, bot.match_result),
                CallbackQueryHandler(bot.cancel, pattern='^cancel_operation$')
            ],
            MATCH_CONTINUE: [
                CallbackQueryHandler(bot.continue_matches, pattern='^continue_matches$'),
                CallbackQueryHandler(bot.finish_matches, pattern='^finish_matches$'),
                CallbackQueryHandler(bot.cancel, pattern='^cancel_operation$')
            ],
        },
        fallbacks=[CallbackQueryHandler(bot.cancel, pattern='^cancel_operation$')],
    )
    
    # Conversation handler برای جستجوی بازیکن
    search_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(bot.search_player_start, pattern='^menu_search$')],
        states={
            SEARCH_SELECT_PLAYER: [CallbackQueryHandler(bot.search_player_selected)],
        },
        fallbacks=[CallbackQueryHandler(bot.cancel, pattern='^cancel_operation$')],
    )
    
    # Conversation handler برای آمار بازیکن
    stats_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(bot.stats_player_start, pattern='^menu_stats$')],
        states={
            STATS_SELECT_PLAYER: [CallbackQueryHandler(bot.stats_player_selected)],
        },
        fallbacks=[CallbackQueryHandler(bot.cancel, pattern='^cancel_operation$')],
    )
    
    # اضافه کردن handler ها
    application.add_handler(CommandHandler('start', bot.start))
    application.add_handler(CommandHandler('help', bot.help_command))
    application.add_handler(add_player_conv_handler)
    application.add_handler(match_conv_handler)
    application.add_handler(search_conv_handler)
    application.add_handler(stats_conv_handler)
    
    # Callback handlers برای دکمه‌های ساده
    application.add_handler(CallbackQueryHandler(bot.list_players, pattern='^menu_list_players$'))
    application.add_handler(CallbackQueryHandler(bot.recent_matches, pattern='^menu_matches$'))
    application.add_handler(CallbackQueryHandler(bot.help_command, pattern='^menu_help$'))
    application.add_handler(CallbackQueryHandler(bot.show_main_menu, pattern='^back_to_menu$'))
    
    # اضافه کردن error handler
    application.add_error_handler(error_handler)
    
    # شروع polling
    logger.info("🎮⚽ ربات فیفا شروع به کار کرد...")
    logger.info("📱 همه چیز با دکمه‌هاست! فقط /start رو بزن و از منو استفاده کن!")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
