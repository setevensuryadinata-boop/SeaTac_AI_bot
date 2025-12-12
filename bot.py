import telebot, json, time, threading
from config import BOT_TOKEN, OWNER
bot = telebot.TeleBot(BOT_TOKEN)

# LOAD DATABASE
def load_data():
    with open("data.json","r") as f:
        return json.load(f)

def save_data(data):
    with open("data.json","w") as f:
        json.dump(data, f, indent=4)

data = load_data()

# CEK LISENSI USER
def cek_user(user_id):
    data = load_data()
    return str(user_id) in data["users"]

# =============================
# SISTEM KEY UNTUK JUALAN
# =============================
@bot.message_handler(commands=['redeem'])
def redeem(msg):
    args = msg.text.split()
    if len(args) < 2:
        return bot.reply_to(msg, "Gunakan: /redeem <KEY>")

    key = args[1]
    data = load_data()

    if key in data["keys"] and data["keys"][key] == True:
        data["users"][msg.from_user.id] = True
        data["keys"][key] = False
        save_data(data)
        bot.reply_to(msg, "KEY berhasil dipakai! 🎉 Kamu sekarang pengguna premium.")
    else:
        bot.reply_to(msg, "KEY tidak valid ❌ atau sudah dipakai orang lain.")

# =============================
# AUTO BALAS
# =============================
@bot.message_handler(func=lambda m: True)
def commands(msg):
    text = msg.text.lower()

    if not cek_user(msg.from_user.id):
        return bot.reply_to(msg, "Kamu belum punya akses premium.\nGunakan: /redeem <KEY>")

    if text == ".p":
        bot.reply_to(msg, "Hadir bos 😎🔥")

    if text == ".menu":
        bot.reply_to(msg, """
📌 *Menu SeaTac_AI Premium*
• .p – cek bot
• /spam <detik> <pesan>
• /kick (reply)
• /rename <nama baru>
• /ai <pertanyaan>
        """)

# =============================
# AUTO SPAM PER DETIK
# =============================
def spam(group_id, text, delay):
    while True:
        bot.send_message(group_id, text)
        time.sleep(delay)

@bot.message_handler(commands=['spam'])
def spam_cmd(msg):
    args = msg.text.split(" ", 2)
    
    if len(args) < 3:
        return bot.reply_to(msg, "Gunakan: /spam <detik> <pesan>")

    delay = int(args[1])    # detik
    text = args[2]
    group_id = msg.chat.id

    threading.Thread(target=spam, args=(group_id, text, delay)).start()
    bot.reply_to(msg, "Spam dimulai! 🔥")

# =============================
# KICK MEMBER
# =============================
@bot.message_handler(commands=['kick'])
def kick_command(msg):
    if not msg.reply_to_message:
        return bot.reply_to(msg, "Reply pesan orang yang mau di-kick.")

    user_id = msg.reply_to_message.from_user.id
    bot.kick_chat_member(msg.chat.id, user_id)
    bot.reply_to(msg, "User berhasil di-kick! 🚫")

# =============================
# GANTI NAMA GRUP
# =============================
@bot.message_handler(commands=['rename'])
def rename(msg):
    new_name = msg.text.replace("/rename ", "")
    bot.set_chat_title(msg.chat.id, new_name)
    bot.reply_to(msg, "Nama grup berhasil diganti! 🔄")

# =============================
# RUN
# =============================
bot.infinity_polling()