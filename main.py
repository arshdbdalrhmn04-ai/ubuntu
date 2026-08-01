import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
import json
import threading
from flask import Flask

# --- 1. إعداد السيرفر الصغير (لإبقاء البوت يعمل 24/7 على Railway) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Communication Bot is Running 24/7!"

def run_server():
    port = int(os.environ.get('PORT', 3001))
    app.run(host='0.0.0.0', port=port)

threading.Thread(target=run_server, daemon=True).start()

# --- 2. الإعدادات والتوكن ---
TOKEN = "8682617060:AAHj0fIhrG7yc9Kaju2OGLq0OYerIP5k1AQ"
ADMIN_ID = 5605856461  # آيدي الأدمن (أنت)

bot = telebot.TeleBot(TOKEN)

# --- 3. قاعدة بيانات بسيطة للمستخدمين وتتبع الرسائل ---
DB_FILE = "bot_data.json"
data_lock = threading.Lock()

def load_data():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except:
                return {"users": [], "msg_map": {}}
    return {"users": [], "msg_map": {}}

def save_data(data):
    with data_lock:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

db = load_data()

# --- 4. الترحيب (واجهة التطبيق المصغر) ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    
    # خزن المستخدم ببيانات البوت حتى تكدر تدزله إذاعة بعدين
    if user_id not in db["users"]:
        db["users"].append(user_id)
        save_data(db)

    # إذا الأدمن داس ستارت
    if user_id == ADMIN_ID:
        bot.reply_to(message, f"👑 **أهلاً بيك ارشد المطور!**\n\n"
                              f"أنت الأدمن، أي رسالة توصلني راح أدزها إلك هنا.\n"
                              f"💡 **طريقة الرد:** بس سوي (Reply) للرسالة اللي توصلك وأني أوصلها للشخص.\n\n"
                              f"📊 **إحصائيات البوت:**\n"
                              f"عدد الأشخاص اللي راسلوك: {len(db['users'])} شخص.\n\n"
                              f"📢 **للإذاعة (إرسال رسالة للكل):**\n"
                              f"اكتب `/bc` وبعدها رسالتك.", parse_mode="Markdown")
        return

    # إذا مستخدم عادي داس ستارت
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📢 قناة التحديثات", url="https://t.me/FutureUWCstudents"))
    
    welcome_text = (
        "👋 **أهلاً بيك في بوت التواصل الرسمي!**\n\n"
        "هذا البوت يشتغل كـ (تطبيق مصغر) حتى تتواصل وياي مباشرة.\n\n"
        "✍️ **شلون تستخدمه؟**\n"
        "اكتب رسالتك، سؤالك، أو حتى دز (صورة/فيديو/بصمة) هنا، وراح توصلني فوراً وأرد عليك بأقرب وقت.\n\n"
        "دز رسالتك هسه... 📥"
    )
    bot.reply_to(message, welcome_text, parse_mode="Markdown", reply_markup=markup)

# --- 5. ميزة الإذاعة (للأدمن فقط) ---
@bot.message_handler(commands=['bc'], func=lambda m: m.chat.id == ADMIN_ID)
def broadcast_message(message):
    text = message.text.replace('/bc', '').strip()
    if not text:
        bot.reply_to(message, "⚠️ **طريقة الإذاعة:**\nاكتب `/bc` وبعدها الرسالة.\nمثال: `/bc السلام عليكم شباب`", parse_mode="Markdown")
        return
    
    bot.reply_to(message, "⏳ جاري إرسال الإذاعة للكل...")
    success_count = 0
    for u_id in db["users"]:
        try:
            bot.send_message(u_id, f"📢 **رسالة من الإدارة:**\n\n{text}", parse_mode="Markdown")
            success_count += 1
        except Exception:
            pass # يتجاهل اللي حاظرين البوت
            
    bot.reply_to(message, f"✅ **تم إرسال الإذاعة بنجاح إلى {success_count} شخص.**", parse_mode="Markdown")

# --- 6. استلام الردود من الأدمن (الرد على المستخدمين) ---
@bot.message_handler(func=lambda m: m.chat.id == ADMIN_ID and m.reply_to_message)
def handle_admin_reply(message):
    original_msg_id = str(message.reply_to_message.message_id)
    
    # فحص إذا الرسالة موجودة بالخريطة مال البوت
    if original_msg_id in db["msg_map"]:
        target_user_id = db["msg_map"][original_msg_id]
        try:
            # ينسخ رد الأدمن (سواء جان نص، صورة، بصمة) ويدزه للمستخدم
            bot.copy_message(target_user_id, ADMIN_ID, message.message_id)
            bot.reply_to(message, "✅ **تم إرسال ردك للمستخدم بنجاح.**", parse_mode="Markdown")
        except Exception as e:
            bot.reply_to(message, f"❌ ما كدرت أدز الرد، يجوز الشخص حظر البوت.")
    else:
        bot.reply_to(message, "⚠️ عذراً، ما كدرت أتعرف على صاحب هاي الرسالة (يجوز قديمة أو ما محفوظة بالبيانات).")

# --- 7. استلام الرسائل من المستخدمين (تحويلها للأدمن) ---
@bot.message_handler(func=lambda m: m.chat.id != ADMIN_ID, content_types=['text', 'photo', 'video', 'document', 'voice', 'audio', 'sticker'])
def handle_user_message(message):
    user_id = message.from_user.id
    username = f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name

    try:
        # 1. رسالة تعريفية للأدمن حتى يعرف منو دزها
        Info_msg = bot.send_message(ADMIN_ID, f"📩 رسالة جديدة من: {username}\nآيدي: {user_id}")
        # 2. نسخ الرسالة الفعلية (المحتوى) للأدمن
        copied_msg = bot.copy_message(ADMIN_ID, message.chat.id, message.message_id)
        
        # 3. خزن معرف الرسالة المنسوخة حتى الأدمن يكدر يرد عليها
        db["msg_map"][str(copied_msg.message_id)] = user_id
        save_data(db)
        
        # 4. تأكيد الاستلام للمستخدم
        bot.reply_to(message, "✅ **وصلت رسالتك!**\nانتظر الرد قريباً...", parse_mode="Markdown")
        except Exception as e:
        bot.reply_to(message, "❌ صار خلل فني وما كدرت أوصل رسالتك، جرب بعدين.")

# --- 8. تشغيل البوت ---
print("Communication Bot is running perfectly...")
bot.infinity_polling(timeout=60, long_polling_timeout=60)
