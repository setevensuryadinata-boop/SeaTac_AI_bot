import telebot

bot = telebot.TeleBot("8079414649:AAGhVgcM4hVCmvYZeVVVPKObed5SYCZupLc")

@bot.message_handler(commands=['start'])
def start(msg):
    bot.reply_to(msg, "Bot SeaTac_AI aktif! Siap membantu 😎")

@bot.message_handler(func=lambda m: True)
def echo(msg):
    bot.reply_to(msg, msg.text)

bot.infinity_polling()