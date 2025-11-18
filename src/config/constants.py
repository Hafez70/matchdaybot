"""Configuration constants"""

# Conversation states
class States:
    """Conversation handler states"""
    # Registration
    REGISTRATION_NAME = 0
    
    # League creation
    CREATE_LEAGUE_NAME = 10
    
    # League joining
    JOIN_LEAGUE_CODE = 20
    
    # Account editing
    EDIT_NAME = 30
    
    # Match recording
    MATCH_SELECT_LEAGUE = 40
    MATCH_SELECT_TYPE = 41
    MATCH_TEAM1_P1 = 42
    MATCH_TEAM1_P2 = 43
    MATCH_TEAM2_P1 = 44
    MATCH_TEAM2_P2 = 45
    MATCH_RESULT = 46
    MATCH_CONTINUE = 47
    
    # Match editing (for league owner)
    EDIT_MATCH_RESULT = 50


# Messages
class Messages:
    """Bot messages"""
    
    WELCOME = """
🎮 سلام {name}! به ربات مسابقات فیفا خوش اومدی! ⚽

با این ربات می‌تونی:
• لیگ شخصی خودت رو بسازی
• به لیگ دوستات بپیوندی
• نتایج مسابقات رو ثبت کنی (1v1، 2v2، 1v2، 2v1)
• آمار کامل و نتایج رو ببینی
• جدول لیگ و رتبه‌بندی رو مشاهده کنی

از منوی زیر استفاده کن 👇
"""
    
    REGISTRATION_PROMPT = """
👤 ثبت نام در ربات

لطفاً نام خودت رو وارد کن:
(این نام در مسابقات نمایش داده میشه)
"""
    
    REGISTRATION_SUCCESS = "✅ ثبت نام با موفقیت انجام شد!\n\nاز منوی زیر استفاده کن 👇"
    
    CREATE_LEAGUE_PROMPT = """
➕ ایجاد لیگ جدید

نام لیگ رو وارد کن:
(مثلاً: لیگ دوستان، لیگ دفتر، و...)
"""
    
    LEAGUE_CREATED = """
✅ لیگ با موفقیت ساخته شد!

🏆 نام لیگ: {name}
🔑 کد دعوت: `{code}`

این کد رو با دوستات به اشتراک بذار تا به لیگ بپیوندن!
"""
    
    JOIN_LEAGUE_PROMPT = """
🔗 پیوستن به لیگ

کد دعوت لیگ رو وارد کن:
"""
    
    HELP = """
📖 راهنمای ربات فیفا

🎯 چطور استفاده کنم؟

1️⃣ **ایجاد لیگ:**
از منو "ایجاد لیگ جدید" رو انتخاب کن
نام لیگ رو وارد کن
کد دعوت رو با دوستات به اشتراک بذار

2️⃣ **پیوستن به لیگ:**
از منو "پیوستن به لیگ" رو انتخاب کن
کد دعوت رو وارد کن

3️⃣ **ثبت مسابقه:**
لیگ مورد نظر رو انتخاب کن
"ثبت مسابقه" رو بزن
نوع مسابقه رو انتخاب کن (1v1، 2v2، 1v2، 2v1)
بازیکنان و نتیجه رو وارد کن

4️⃣ **مشاهده آمار:**
در منوی لیگ می‌تونی:
• آمار خودت رو ببینی
• جدول لیگ رو مشاهده کنی
• مسابقات اخیر رو ببینی

💡 نکات:
• می‌تونی عضو چند لیگ مختلف باشی
• هر لیگ آمار جداگانه‌ای داره
• فقط می‌تونی اسم خودت رو ویرایش کنی
"""

