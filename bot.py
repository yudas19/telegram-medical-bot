import os
import requests # Tidak digunakan, tapi tidak masalah
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
import google.generativeai as genai # Import sudah benar

# Load environment variables
load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# --- HANDLERS TELEGRAM ---

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    welcome_text = """
🤖 Selamat datang di pmikBot!

Saya adalah asisten medis AI yang siap membantu dengan:
• Kode ICD-10 & Kode untuk Tindakan/Prosedur Medis ICD-9
• INA-CBGS & IDRG  
• dan Informasi kesehatan umum lainnya
*anda juga dapat bertanya seputar Berita Acara BPJS Kesehatan!*

Cara pakai:
• Di grup: 
  - /pmik [pertanyaan]
  - Atau mention saya @pmikBot [pertanyaan]

Contoh:
/pmik apa ICD-10 untuk diabetes?
/pmik jelaskan tentang INA-CBGS
@pmikBot kode tindakan ICD-9 untuk tonsilektomi

Semoga membantu! 😊"""
    
    await update.message.reply_text(welcome_text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    help_text = """
📖 Bantuan pmikBot

Commands:
/start - Memulai bot
/help - Menampilkan bantuan ini
/pmik - Tanya pertanyaan medis

Cara penggunaan:
• Grup: 
  - /pmik [pertanyaan]
  - Atau mention saya @pmikBot [pertanyaan]

Contoh:
/pmik ICD-10 untuk hipertensi
/pmik Kode Tindakan ICD-9 untuk Tonsilektomi
/pmik kode Gruping INA-CBGS untuk appendectomy dan tarifnya

Fitur:
• Kode diagnosis & prosedur
• Informasi tarif INA-CBGS
• Klasifikasi penyakit
• Edukasi kesehatan"""
    
    await update.message.reply_text(help_text)

async def pmik_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle command /pmik [pertanyaan]"""
    chat_id = update.message.chat_id
    
    # Menampilkan indikator "typing..."
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    
    if not context.args:
        # Jika /pmik tidak diikuti pertanyaan, berikan petunjuk
        help_text = """
🤖 Cara menggunakan /pmik:

/pmik [pertanyaan]

Contoh:
/pmik apa kode ICD-10 untuk limfoma?
/pmik jelaskan tentang INA-CBGS
/pmik kode tindakan ICD-9 untuk Pemecahan Batu Ginjal

Saya siap membantu dengan ICD-10, ICD-9, ICD O, INA-CBGS, IDRG, dan informasi kesehatan lainnya! 😊
"""
        await update.message.reply_text(help_text)
        return
    
    user_question = " ".join(context.args)
    
    try:
        response = call_gemini(user_question)
        await update.message.reply_text(response)
    except Exception as e:
        await update.message.reply_text(f"❌ Maaf, terjadi error: {str(e)}")

async def handle_private_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle pesan di chat private (merespon semua pesan teks)"""
    user_message = update.message.text
    chat_id = update.message.chat_id
    
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    
    try:
        response = call_gemini(user_message)
        await update.message.reply_text(response)
    except Exception as e:
        await update.message.reply_text(f"❌ Maaf, terjadi error: {str(e)}")

async def handle_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle pesan di grup - hanya merespon jika di-mention (@pmikBot)"""
    bot_username = context.bot.username
    message_text = update.message.text or ""
    
    if f"@{bot_username}" in message_text:
        chat_id = update.message.chat_id
        await context.bot.send_chat_action(chat_id=chat_id, action="typing")
        
        # Hapus mention dari pesan untuk mendapatkan pertanyaan bersih
        user_message = message_text.replace(f"@{bot_username}", "").strip()
        
        if not user_message:
            # Respon jika hanya mention tanpa pertanyaan
            user_message = "Halo! Ada yang bisa pmik bantu?"
        
        try:
            response = call_gemini(user_message)
            # Respon dengan me-reply pesan asli
            await update.message.reply_text(
                response, 
                reply_to_message_id=update.message.message_id
            )
        except Exception as e:
            await update.message.reply_text(
                f"❌ Maaf, terjadi error: {str(e)}", 
                reply_to_message_id=update.message.message_id
            )

# --- FUNGSI INTEGRASI GEMINI ---

def call_gemini(question: str) -> str:
    """Panggil Gemini 2.0 API untuk mendapatkan jawaban"""
    try:
        # Konfigurasi Gemini dengan API Key
        genai.configure(api_key=GEMINI_API_KEY)

        # Menggunakan model yang sudah teruji berhasil
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        # System Prompt yang sangat baik untuk menentukan persona AI
        system_prompt = """Anda adalah pmikBot - asisten medis ahli khusus untuk:
1. ICD-10-CM: Kode diagnosis penyakit (Contoh: I10 untuk Hipertensi)
2. ICD-9-CM: Kode prosedur/tindakan medis (Contoh: 38.7 untuk Eksisi vena)
3. ICD-O: Kode untuk tumor/kanker (Contoh: 8140/3 untuk Adenocarcinoma)
4. INA-CBGS: Pengelompokan kode diagnosis + prosedur + tarif
5. IDRG: Indonesian Diagnosis Related Groups (pengelompokan diagnosa 2025)

ATURAN PENTING:
- Untuk diagnosis: gunakan ICD-10-CM
- Untuk prosedur/tindakan: gunakan ICD-9-CM  
- Untuk tumor/kanker: gunakan ICD-O
- SELALU sertakan SUMBER referensi di setiap jawaban
- Format: [Kode] - [Deskripsi] - Sumber: [Referensi]
- Jika tidak tahu, jangan menebak, katakan "Maaf, saya belum memiliki data tersebut, Pak yuda akan mengupdate data saya."
- Gunakan bahasa Indonesia profesional, friendly dan mudah dimengerti
- Husus Untuk INA-CBGS, kamu bisa sertakan tarif rata-rata tarif Rumah Sakit yang ada di indonesia dalam Rupiah jika kamu tidak memiliki data pasti

CONTOH FORMAT JAWABAN:
• Kode Diagnosis nya: E11.9 - Diabetes mellitus, tipe 2 - Sumber: ICD-10-CM 2024
• Kode Prosedur: 47.01 - Laparoscopic appendectomy - Sumber: ICD-9-CM 2015
• Kode Tumor: 8140/3 - Adenocarcinoma - Sumber: ICD-O-3.2
• Kode INA-CBGS: A-01-01 - Medical check up dasar - Tarif: Rp 150.000
• Kode IDRG: DRG-001 - Penyakit infeksi tertentu"""

        # Gabungkan system prompt dengan pertanyaan user
        full_prompt = f"{system_prompt}\n\nPertanyaan user: {question}\n\nJawab dengan format di atas dan sertakan sumber referensi:"
        
        # Generation config yang bagus untuk jawaban medis faktual (rendah temperature)
        generation_config = {
            "temperature": 0.2, 
            "top_p": 0.8,
            "top_k": 40,
            "max_output_tokens": 2000,
        }
        
        # Safety settings - disesuaikan agar konten medis tidak terblokir
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]
        
        response = model.generate_content(
            full_prompt,
            generation_config=generation_config,
            safety_settings=safety_settings
        )
        
        return response.text
        
    except Exception as e:
        # Jika ada masalah pada API call (misal: API key salah, rate limit)
        return f"❌ Error AI: {str(e)}"

# --- FUNGSI UTAMA ---

def main():
    if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
        print("ERROR: Token tidak ditemukan. Pastikan file .env sudah diisi!")
        return
    
    # Buat instance Aplikasi
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Tambahkan Command Handlers
    application.add_handler(CommandHandler("pmik", pmik_command))
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    
    # Tambahkan Message Handlers
    # 1. Pesan Teks di Private Chat (tidak termasuk command)
    application.add_handler(MessageHandler(
        filters.TEXT & filters.ChatType.PRIVATE & ~filters.COMMAND, 
        handle_private_message
    ))
    # 2. Pesan Teks di Group Chat (tidak termasuk command, untuk cek mention)
    application.add_handler(MessageHandler(
        filters.TEXT & filters.ChatType.GROUPS & ~filters.COMMAND, 
        handle_group_message
    ))
    
    print("🤖 pmikBot dengan Gemini 2.0 Flash sedang berjalan...")
    print("✅ Command /pmik sudah aktif")
    print("🚀 Gemini AI: gemini-2.0-flash")
    print("⏹️ Tekan Ctrl+C untuk menghentikan")
    
    # Jalankan bot
    application.run_polling()

if __name__ == '__main__':
    main()