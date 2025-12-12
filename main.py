from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Updater, CommandHandler, CallbackContext, ConversationHandler,
    MessageHandler, Filters, CallbackQueryHandler
)
import sqlite3
import json
from datetime import datetime, timedelta
import random
import string
import time

# --------------------------
# GANTI DENGAN DATA KAMU!
# --------------------------
TOKEN ="8445412808:AAEpS-l0xRyD-WH_t29nLURBc-DhPU5M3Ds"
ADMIN_USER_ID = 7340467332 
REKENING = "DANA 089523774538 " 

# Konfigurasi
HARGA_KUNCI = {"sehari":10000, "seminggu":50000, "sebulan":150000}

# State untuk alur percakapan
PILIH_DURASI, INPUT_KODE, PESAN_JADWAL, GRUP_JADWAL, JAM_JADWAL = range(5)

# --------------------------
# INISIALISASI DATABASE
# --------------------------
def init_db():
    conn = sqlite3.connect('bot_db.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS kunci
                 (user_id INTEGER PRIMARY KEY, status TEXT, masa_berlaku DATETIME, 
                  kode_aktifasi TEXT, durasi_key TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS jadwal
                 (jadwal_id TEXT PRIMARY KEY, user_id INTEGER, pesan TEXT, 
                  grup_tujuan TEXT, jam_tertentu TEXT, grup_terhenti TEXT)''')
    conn.commit()
    conn.close()
init_db()

# --------------------------
# FUNGSI BANTU
# --------------------------
def generate_kode():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

def cek_kunci_aktif(user_id):
    conn = sqlite3.connect('bot_db.db')
    c = conn.cursor()
    c.execute("SELECT status, masa_berlaku FROM kunci WHERE user_id=?", (user_id,))
    data = c.fetchone()
    conn.close()
    if not data:
        return False
    status, masa_berlaku = data
    if status == "aktif" and datetime.strptime(masa_berlaku, "%Y-%m-%d %H:%M:%S") > datetime.now():
        return True
    return False

def cek_admin(user_id):
    return user_id == ADMIN_USER_ID

# --------------------------
# MENU & KEYBOARD
# --------------------------
def menu_utama():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛒 Beli Kunci", callback_data='beli')],
        [InlineKeyboardButton("✅ Cek Kunci", callback_data='cek')],
        [InlineKeyboardButton("📨 Atur Pesan Otomatis", callback_data='atur_pesan')],
        [InlineKeyboardButton("❓ Bantuan", callback_data='bantuan')]
    ])

# --------------------------
# PENANGANAN TOMBOL MENU
# --------------------------
def handle_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    if query.data == 'menu_utama':
        query.edit_message_text(
            text="<b>📋 MENU BOT KEREN</b>\n\nPilih opsi di bawah:",
            parse_mode="HTML",
            reply_markup=menu_utama()
        )

    elif query.data == 'beli':
        query.edit_message_text(
            text="<b>💸 PEMBELIAN KUNCI</b>\n\nPilih durasi:",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("1 Hari • Rp10.000", callback_data='durasi_sehari')],
                [InlineKeyboardButton("1 Minggu • Rp50.000", callback_data='durasi_seminggu')],
                [InlineKeyboardButton("1 Bulan • Rp150.000", callback_data='durasi_sebulan')],
                [InlineKeyboardButton("⬅️ Kembali", callback_data='menu_utama')]
            ])
        )

    elif query.data.startswith('durasi_'):
        durasi = query.data.split('_')[1]
        total = HARGA_KUNCI[durasi]
        context.user_data['durasi'] = durasi
        context.user_data['total'] = total

        query.edit_message_text(
            text=f"<b>📅 DETAIL PEMBELIAN</b>\n• Durasi: {durasi.capitalize()}\n• Total: Rp{total:,}\n\nTransfer ke: {REKENING}\nKlik 'Lanjut' untuk dapat kode!",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Lanjut", callback_data='lanjut_beli')],
                [InlineKeyboardButton("❌ Batal", callback_data='menu_utama')]
            ])
        )

    elif query.data == 'lanjut_beli':
        user_id = query.from_user.id
        durasi = context.user_data['durasi']
        total = context.user_data['total']
        kode = generate_kode()

        conn = sqlite3.connect('bot_db.db')
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO kunci VALUES (?, ?, ?, ?, ?)", 
                  (user_id, "menunggu", None, kode, durasi))
        c.execute("UPDATE kunci SET kode_aktifasi=?, durasi_key=? WHERE user_id=?", 
                  (kode, durasi, user_id))
        conn.commit()
        conn.close()

        query.edit_message_text(
            text=f"<b>✅ BERHASIL!</b>\n• ID Transaksi: TRX{datetime.now().strftime('%Y%m%d')}\n• Kode Aktifasi: <code>{kode}</code>\n\nKirim bukti transfer ke admin untuk aktifkan!",
            parse_mode="HTML",
            reply_markup=menu_utama()
        )

    elif query.data == 'cek':
        user_id = query.from_user.id
        if cek_kunci_aktif(user_id):
            pesan = "<b>✅ KUNCI AKTIF!</b>\nNikmati semua fitur!"
        else:
            pesan = "<b>❌ KUNCI TIDAK AKTIF</b>\nBeli atau aktifkan kode terlebih dahulu!"
        query.edit_message_text(text=pesan, parse_mode="HTML", reply_markup=menu_utama())

    elif query.data == 'atur_pesan':
        if cek_kunci_aktif(query.from_user.id):
            query.edit_message_text(
                text="<b>📨 MASUKKAN PESAN</b>\nTulis pesan yang ingin kamu kirim otomatis:",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Batal", callback_data='menu_utama')]])
            )
            global current_jadwal_user
            current_jadwal_user = query.from_user.id
        else:
            query.edit_message_text(
                text="<b>❌ BUTUH KUNCI AKTIF!</b>",
                parse_mode="HTML",
                reply_markup=menu_utama()
            )

    elif query.data == 'bantuan':
        query.edit_message_text(
            text="<b>❓ BANTUAN</b>\n• /start → Buka menu\n• /menu → Buka menu\n• /aktifkan_kunci → Aktifkan kode\n• /admin_menu → Menu admin (hanya pemilik)",
            parse_mode="HTML",
            reply_markup=menu_utama()
        )

# --------------------------
# PERINTAH BOT UMUM
# --------------------------
current_jadwal_user = None

def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    conn = sqlite3.connect('bot_db.db')
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO kunci VALUES (?, ?, ?, ?, ?)", 
              (user_id, "menunggu", None, None, None))
    conn.commit()
    conn.close()

    update.message.reply_text(
        text="<b>👋 HALO! SELAMAT DATANG!</b>\nBot ini bisa kirim pesan otomatis ke grup tanpa admin!",
        parse_mode="HTML",
        reply_markup=menu_utama()
    )

def menu(update: Update, context: CallbackContext):
    start(update, context)

def aktifkan_kunci(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("<b>🔑 MASUKKAN KODE AKTIFASI</b>", parse_mode="HTML")
    return INPUT_KODE

def proses_kode(update: Update, context: CallbackContext) -> int:
    kode = update.message.text.upper()
    user_id = update.effective_user.id

    conn = sqlite3.connect('bot_db.db')
    c = conn.cursor()
    c.execute("SELECT status, durasi_key FROM kunci WHERE kode_aktifasi=?", (kode,))
    data = c.fetchone()

    if data and data[0] in ["siap", "menunggu"]:
        status_kode, durasi_key = data

        if durasi_key == 'sehari':
            masa_berlaku = datetime.now() + timedelta(days=1)
        elif durasi_key == 'seminggu':
            masa_berlaku = datetime.now() + timedelta(weeks=1)
        elif durasi_key == 'sebulan':
            masa_berlaku = datetime.now() + timedelta(days=30)
        else:
            masa_berlaku = datetime.now() + timedelta(days=30)

        c.execute("UPDATE kunci SET status='aktif', masa_berlaku=?, user_id=? WHERE kode_aktifasi=?",
                  (masa_berlaku.strftime("%Y-%m-%d %H:%M:%S"), user_id, kode))
        conn.commit()
        pesan = f"<b>🎉 KUNCI BERHASIL DIAKTIFKAN!</b>\n• Durasi: {durasi_key.capitalize()}\n• Masa Berlaku: {masa_berlaku.strftime('%d-%m-%Y %H:%M')}"
    else:
        pesan = "<b>❌ KODE SALAH ATAU SUDAH DIGUNAKAN!</b>"

    conn.close()
    update.message.reply_text(pesan, parse_mode="HTML", reply_markup=menu_utama())
    return ConversationHandler.END

def proses_pesan(update: Update, context: CallbackContext):
    global current_jadwal_user
    if update.effective_user.id != current_jadwal_user:
        return
    context.user_data['pesan'] = update.message.text
    update.message.reply_text("<b>📝 MASUKKAN ID GRUP</b>\nContoh: 1234567890 (pisahkan koma jika banyak)", parse_mode="HTML")
    current_jadwal_user = 'grup'

def proses_grup(update: Update, context: CallbackContext):
    global current_jadwal_user
    if current_jadwal_user != 'grup':
        return
    context.user_data['grup'] = update.message.text
    update.message.reply_text("<b>⏰ MASUKKAN JAM</b>\nContoh: 08:00,17:00", parse_mode="HTML")
    current_jadwal_user = 'jam'

def proses_jam(update: Update, context: CallbackContext):
    global current_jadwal_user
    if current_jadwal_user != 'jam':
        return
    jam = update.message.text
    pesan = context.user_data['pesan']
    grup = context.user_data['grup']
    user_id = update.effective_user.id
    jadwal_id = f"JAD{datetime.now().strftime('%Y%m%d%H%M%S')}"

    conn = sqlite3.connect('bot_db.db')
    c = conn.cursor()
    c.execute("INSERT INTO jadwal VALUES (?, ?, ?, ?, ?, ?)", 
              (jadwal_id, user_id, pesan, grup, jam, "[]"))
    conn.commit()
    conn.close()

    update.message.reply_text(f"<b>✅ JADWAL DIBUAT! ID: {jadwal_id}</b>", parse_mode="HTML", reply_markup=menu_utama())
    current_jadwal_user = None

# --------------------------
# PERINTAH ADMIN: BUAT KEY SENDIRI
# --------------------------
def admin_menu(update: Update, context: CallbackContext) -> None:
    if not cek_admin(update.effective_user.id):
        update.message.reply_text("<b>❌ HANYA ADMIN YANG BISA AKSES!</b>", parse_mode="HTML")
        return

    update.message.reply_text(
        text="<b>🔐 MENU ADMIN: BUAT KEY</b>\n\nGunakan perintah:\n<code>/buat_key [durasi] [kode_opsional]</code>\n\nContoh:\n- /buat_key sehari MYKEY123\n- /buat_key seminggu\n- /buat_key sebulan BOTKU123",
        parse_mode="HTML"
    )

def buat_key(update: Update, context: CallbackContext) -> None:
    if not cek_admin(update.effective_user.id):
        update.message.reply_text("<b>❌ HANYA ADMIN YANG BISA AKSES!</b>", parse_mode="HTML")
        return

    if len(context.args) < 1:
        update.message.reply_text("<b>⚠️ CARA PENGGUNAAN:</b>\n<code>/buat_key [durasi] [kode_opsional]</code>", parse_mode="HTML")
        return

    durasi = context.args[0].lower()
    if durasi not in HARGA_KUNCI.keys():
        update.message.reply_text("<b>❌ DURASI SALAH!</b>\nPilih: sehari, seminggu, sebulan", parse_mode="HTML")
        return

    if len(context.args) >= 2:
        kode = context.args[1].upper()
    else:
        kode = generate_kode()

    conn = sqlite3.connect('bot_db.db')
    c = conn.cursor()
    c.execute("SELECT kode_aktifasi FROM kunci WHERE kode_aktifasi=?", (kode,))
    if c.fetchone():
        update.message.reply_text(f"<b>❌ KODE {kode} SUDAH ADA!</b> Gunakan kode lain.", parse_mode="HTML")
        conn.close()
        return

    c.execute("INSERT OR IGNORE INTO kunci (kode_aktifasi, status, durasi_key) VALUES (?, ?, ?)", 
              (kode, "siap", durasi))
    conn.commit()
    conn.close()

    update.message.reply_text(
        text=f"<b>✅ KEY BERHASIL DIBUAT!</b>\n\n• Kode: <code>{kode}</code>\n• Durasi: {durasi.capitalize()}\n• Status: Siap pakai",
        parse_mode="HTML"
    )

# --------------------------
# JALANKAN JADWAL PESAN
# --------------------------
def jalankan_jadwal(updater):
    while True:
        now = datetime.now().strftime("%H:%M")
        conn = sqlite3.connect('bot_db.db')
        c = conn.cursor()
        c.execute("SELECT * FROM jadwal")
        jadwals = c.fetchall()
        conn.close()

        for jadwal in jadwals:
            jadwal_id, user_id, pesan, grup, jam, terhenti = jadwal
            if now in jam.split(',') and cek_kunci_aktif(user_id):
                for g in grup.split(','):
                    if g not in json.loads(terhenti):
                        try:
                            updater.bot.send_message(chat_id=int(g), text=f"<b>📢 PESAN OTOMATIS</b>\n\n{pesan}", parse_mode="HTML")
                        except:
                            pass
        time.sleep(60)

# --------------------------
# MAIN PROGRAM
# --------------------------
def main():
    updater = Updater(TOKEN)
    dp = updater.dispatcher

    # Handler perintah umum
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("menu", menu))
    dp.add_handler(CommandHandler("aktifkan_kunci", aktifkan_kunci))

    # Handler admin
    dp.add_handler(CommandHandler("admin_menu", admin_menu))
    dp.add_handler(CommandHandler("buat_key", buat_key))

    # Handler konversasi aktifkan kode
    dp.add_handler(ConversationHandler(
        entry_points=[CommandHandler("aktifkan_kunci", aktifkan_kunci)],
        states={INPUT_KODE: [MessageHandler(Filters.text, proses_kode)]},
        fallbacks=[]
    ))

    # Handler callback tombol menu
    dp.add_handler(CallbackQueryHandler(handle_callback))

    # Handler proses jadwal pesan
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, proses_pesan))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, proses_grup))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, proses_jam))

    # Jalankan jadwal pesan di background
    import threading
    threading.Thread(target=jalankan_jadwal, args=(updater,), daemon=True).start()

    # Jalankan bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()