import telebot
from telebot import types

# ضع التوكن والـ ID الخاص بك هنا
TOKEN = "8809789398:AAHVRsx94U3zlhMesALWMXiMBxJL51b9q64"
ADMIN_ID = 8804197607  # استبدل الرقم بـ ID حسابك

bot = telebot.TeleBot(TOKEN)

data = {
    "hierarchy": {"main": []},
    "parents": {},
    "contents": {},
    "users": set(),
    "banned": set(),
    "muted": set(),
    "chat_locked": False
}

admin_states = {}
user_current_menu = {}

def get_menu(user_id, menu_name):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = data["hierarchy"].get(menu_name, [])
    
    for btn in buttons:
        markup.add(types.KeyboardButton(btn))
    
    if user_id == ADMIN_ID:
        markup.add("➕ إضافة مجلد", "➕ إضافة زر محتوى")
        markup.add("🗑 حذف زر من هنا")
        
        lock_status = "🔓 فتح الدردشة" if data["chat_locked"] else "🔒 قفل الدردشة"
        markup.add(lock_status)
        markup.add("🔊 فك الكتم", "🔇 كتم عضو")
        markup.add("✅ فك الطرد", "🚫 طرد عضو")

    if menu_name != "main":
        markup.add("🔙 رجوع")
        
    return markup

def cancel_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("❌ إلغاء")
    return markup

@bot.message_handler(commands=['start'])
def start_cmd(message):
    user_id = message.from_user.id
    data["users"].add(user_id)
    user_current_menu[user_id] = "main"
    admin_states[user_id] = None
    
    bot.send_message(
        user_id, 
        f"أهلاً بك يا {message.from_user.first_name} في البوت!", 
        reply_markup=get_menu(user_id, "main")
    )

@bot.message_handler(func=lambda m: True, content_types=['text', 'photo', 'document', 'audio', 'voice', 'video'])
def main_handler(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    text = message.text if message.text else ""
    is_admin = (user_id == ADMIN_ID)
    
    data["users"].add(user_id)
    if user_id in data["banned"]:
        return

    current_menu = user_current_menu.get(user_id, "main")

    if text == "❌ إلغاء":
        admin_states[user_id] = None
        bot.send_message(chat_id, "تم إلغاء العملية.", reply_markup=get_menu(user_id, current_menu))
        return

    # --- أزرار الإدارة والأدمن ---
    if is_admin:
        # 1. إضافة مجلد
        if text == "➕ إضافة مجلد":
            admin_states[user_id] = "wait_folder_name"
            bot.send_message(chat_id, "أرسل اسم المجلد الجديد:", reply_markup=cancel_menu())
            return
            
        if admin_states.get(user_id) == "wait_folder_name":
            data["hierarchy"][current_menu].append(text)
            data["hierarchy"][text] = []
            data["parents"][text] = current_menu
            admin_states[user_id] = None
            bot.send_message(chat_id, f"✅ تم إنشاء المجلد '{text}'", reply_markup=get_menu(user_id, current_menu))
            return

        # 2. إضافة زر محتوى
        if text == "➕ إضافة زر محتوى":
            admin_states[user_id] = "wait_btn_name"
            bot.send_message(chat_id, "أرسل اسم الزر الجديد:", reply_markup=cancel_menu())
            return

        if admin_states.get(user_id) == "wait_btn_name":
            admin_states[user_id] = f"wait_btn_content:{text}"
            bot.send_message(chat_id, f"الآن أرسل الملف أو نص الرسالة للزر '{text}':", reply_markup=cancel_menu())
            return

        if str(admin_states.get(user_id)).startswith("wait_btn_content:"):
            btn_name = admin_states[user_id].split("wait_btn_content:")[1]
            data["hierarchy"][current_menu].append(btn_name)
            data["contents"][btn_name] = {"chat_id": chat_id, "msg_id": message.message_id}
            admin_states[user_id] = None
            bot.send_message(chat_id, f"✅ تم حفظ المحتوى داخل زر '{btn_name}'", reply_markup=get_menu(user_id, current_menu))
            return

        # 3. حذف زر
        if text == "🗑 حذف زر من هنا":
            admin_states[user_id] = "wait_del_btn_name"
            bot.send_message(chat_id, "أرسل اسم الزر الذي تريد حذفه:", reply_markup=cancel_menu())
            return

        if admin_states.get(user_id) == "wait_del_btn_name":
            if text in data["hierarchy"].get(current_menu, []):
                data["hierarchy"][current_menu].remove(text)
                if text in data["contents"]:
                    del data["contents"][text]
                bot.send_message(chat_id, "✅ تم الحذف بنجاح.", reply_markup=get_menu(user_id, current_menu))
            else:
                bot.send_message(chat_id, "لم يتم العثور على الزر.", reply_markup=get_menu(user_id, current_menu))
            admin_states[user_id] = None
            return

        # 4. قفل وفتح الدردشة
        if text in ["🔒 قفل الدردشة", "🔓 فتح الدردشة"]:
            data["chat_locked"] = not data["chat_locked"]
            status = "مغلقة 🔒" if data["chat_locked"] else "مفتوحة 🔓"
            bot.send_message(chat_id, f"تم تغيير حالة الدردشة إلى: {status}", reply_markup=get_menu(user_id, current_menu))
            return

        # 5. كتم عضو
        if text == "🔇 كتم عضو":
            admin_states[user_id] = "wait_mute_id"
            bot.send_message(chat_id, "أرسل ID العضو المراد كتمه:", reply_markup=cancel_menu())
            return

        if admin_states.get(user_id) == "wait_mute_id":
            if text.isdigit():
                target_id = int(text)
                data["muted"].add(target_id)
                bot.send_message(chat_id, f"✅ تم كتم العضو `{target_id}` بنجاح.", parse_mode="Markdown", reply_markup=get_menu(user_id, current_menu))
            else:
                bot.send_message(chat_id, "❌ يرجى إرسال ID صحيح (أرقام فقط).", reply_markup=get_menu(user_id, current_menu))
            admin_states[user_id] = None
            return

        # 6. فك الكتم
        if text == "🔊 فك الكتم":
            admin_states[user_id] = "wait_unmute_id"
            bot.send_message(chat_id, "أرسل ID العضو المراد فك الكتم عنه:", reply_markup=cancel_menu())
            return

        if admin_states.get(user_id) == "wait_unmute_id":
            if text.isdigit():
                target_id = int(text)
                data["muted"].discard(target_id)
                bot.send_message(chat_id, f"✅ تم فك الكتم عن العضو `{target_id}`.", parse_mode="Markdown", reply_markup=get_menu(user_id, current_menu))
            else:
                bot.send_message(chat_id, "❌ يرجى إرسال ID صحيح.", reply_markup=get_menu(user_id, current_menu))
            admin_states[user_id] = None
            return

        # 7. طرد/حظر عضو
        if text == "🚫 طرد عضو":
            admin_states[user_id] = "wait_ban_id"
            bot.send_message(chat_id, "أرسل ID العضو المراد طرده وحظره:", reply_markup=cancel_menu())
            return

        if admin_states.get(user_id) == "wait_ban_id":
            if text.isdigit():
                target_id = int(text)
                data["banned"].add(target_id)
                bot.send_message(chat_id, f"✅ تم طرد وحظر العضو `{target_id}`.", parse_mode="Markdown", reply_markup=get_menu(user_id, current_menu))
            else:
                bot.send_message(chat_id, "❌ يرجى إرسال ID صحيح.", reply_markup=get_menu(user_id, current_menu))
            admin_states[user_id] = None
            return

        # 8. فك الطرد/الحظر
        if text == "✅ فك الطرد":
            admin_states[user_id] = "wait_unban_id"
            bot.send_message(chat_id, "أرسل ID العضو المراد فك الحظر عنه:", reply_markup=cancel_menu())
            return

        if admin_states.get(user_id) == "wait_unban_id":
            if text.isdigit():
                target_id = int(text)
                data["banned"].discard(target_id)
                bot.send_message(chat_id, f"✅ تم فك الحظر عن العضو `{target_id}`.", parse_mode="Markdown", reply_markup=get_menu(user_id, current_menu))
            else:
                bot.send_message(chat_id, "❌ يرجى إرسال ID صحيح.", reply_markup=get_menu(user_id, current_menu))
            admin_states[user_id] = None
            return

    # --- التصفح والضغط على الأزرار للمستخدمين ---
    if text == "🔙 رجوع" and current_menu != "main":
        parent = data["parents"].get(current_menu, "main")
        user_current_menu[user_id] = parent
        bot.send_message(chat_id, "تم الرجوع.", reply_markup=get_menu(user_id, parent))
        return

    if text in data["hierarchy"].get(current_menu, []):
        if text in data["hierarchy"]:
            user_current_menu[user_id] = text
            bot.send_message(chat_id, f"📂 دخلت إلى: {text}", reply_markup=get_menu(user_id, text))
        elif text in data["contents"]:
            btn_data = data["contents"][text]
            bot.copy_message(chat_id, btn_data["chat_id"], btn_data["msg_id"])
        return

    # قائمة الأزرار الخاصة بالإدارة لمنع إعادة توجيهها للدردشة الجماعية
    admin_buttons = [
        "➕ إضافة مجلد", "➕ إضافة زر محتوى", "🗑 حذف زر من هنا",
        "🔒 قفل الدردشة", "🔓 فتح الدردشة", "🔇 كتم عضو",
        "🔊 فك الكتم", "🚫 طرد عضو", "✅ فك الطرد", "❌ إلغاء"
    ]

    # --- الدردشة الجماعية بين الأعضاء ---
    if admin_states.get(user_id) is None and text not in admin_buttons:
        if not is_admin:
            if data["chat_locked"]:
                bot.send_message(chat_id, "🔒 الدردشة مغلقة حالياً من قبل الإدارة.")
                return
            if user_id in data["muted"]:
                bot.send_message(chat_id, "🔇 أنت مكتوم ولا يمكنك المشاركة في الدردشة.")
                return

        sender_name = message.from_user.first_name
        for u_id in list(data["users"]):
            if u_id != user_id and u_id not in data["banned"]:
                try:
                    if message.content_type == 'text':
                        bot.send_message(u_id, f"💬 {sender_name} (`{user_id}`):\n{text}", parse_mode="Markdown")
                    else:
                        bot.send_message(u_id, f"📎 {sender_name} (`{user_id}`) أرسل ملفاً:", parse_mode="Markdown")
                        bot.copy_message(u_id, chat_id, message.message_id)
                except Exception:
                    pass

print("البوت يعمل بنجاح...")
bot.infinity_polling()
