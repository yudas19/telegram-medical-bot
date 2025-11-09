import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
from groq import Groq

# Load environment variables
load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    welcome_text = """
🤖 Selamat datang di pmikBot!

Saya adalah asisten medis AI yang siap membantu dengan:
• Kode ICD-10 & ICD-9
• INA-CBGS & IDRG  
• Informasi kesehatan umum

Cara pakai:
• Private Chat: Langsung tanya saja
• Di grup: 
  - /pmik [pertanyaan]
  - Atau mention @pmikBot [pertanyaan]

Contoh:
/pmik apa ICD-10 untuk diabetes?
/pmik jelaskan tentang INA-CBGS
@pmikBot kode ICD-9 untuk pneumonia

Semoga membantu! 😊"""
    
    await update.message.reply_text(welcome_text)  # HAPUS parse_mode

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    help_text = """
📖 Bantuan pmikBot

Commands:
/start - Memulai bot
/help - Menampilkan bantuan ini
/pmik - Tanya pertanyaan medis

Cara penggunaan:
• Private Chat: Langsung ketik pertanyaan
• Grup: 
  - /pmik [pertanyaan]
  - Atau mention @pmikBot [pertanyaan]

Contoh:
/pmik ICD-10 untuk hipertensi
/pmik kode INA-CBGS untuk USG
/pmik perbedaan ICD-9 dan ICD-10

Fitur:
• Kode diagnosis & prosedur
• Informasi tarif INA-CBGS
• Klasifikasi penyakit
• Edukasi kesehatan"""
    
    await update.message.reply_text(help_text)  # HAPUS parse_mode

async def pmik_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle command /pmik [pertanyaan]"""
    chat_id = update.message.chat_id
    
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    
    if not context.args:
        help_text = """
🤖 Cara menggunakan /pmik:

/pmik [pertanyaan]

Contoh:
/pmik apa kode ICD-10 untuk hipertensi?
/pmik jelaskan tentang INA-CBGS
/pmik kode ICD-9 untuk appendicitis

Saya siap membantu dengan ICD-10, ICD-9, INA-CBGS, IDRG, dan informasi kesehatan lainnya! 😊
"""
        await update.message.reply_text(help_text)  # HAPUS parse_mode
        return
    
    user_question = " ".join(context.args)
    
    try:
        response = call_groq(user_question)
        await update.message.reply_text(response)  # HAPUS parse_mode
    except Exception as e:
        await update.message.reply_text(f"❌ Maaf, terjadi error: {str(e)}")

async def handle_private_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle pesan di chat private"""
    user_message = update.message.text
    chat_id = update.message.chat_id
    
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    
    try:
        response = call_groq(user_message)
        await update.message.reply_text(response)  # HAPUS parse_mode
    except Exception as e:
        await update.message.reply_text(f"❌ Maaf, terjadi error: {str(e)}")

async def handle_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle pesan di grup - hanya merespon jika di-mention"""
    bot_username = context.bot.username
    message_text = update.message.text or ""
    
    if f"@{bot_username}" in message_text:
        chat_id = update.message.chat_id
        await context.bot.send_chat_action(chat_id=chat_id, action="typing")
        
        user_message = message_text.replace(f"@{bot_username}", "").strip()
        
        if not user_message:
            user_message = "Halo! Ada yang bisa saya bantu?"
        
        try:
            response = call_groq(user_message)
            await update.message.reply_text(
                response, 
                reply_to_message_id=update.message.message_id
                # HAPUS parse_mode
            )
        except Exception as e:
            await update.message.reply_text(
                f"❌ Maaf, terjadi error: {str(e)}", 
                reply_to_message_id=update.message.message_id
            )

def call_groq(question: str) -> str:
    """Panggil Groq API sebagai pengganti DeepSeek"""
    client = Groq(api_key=GROQ_API_KEY)
    
    system_prompt = """Anda adalah pmikBot - asisten medis ahli untuk ICD-10, ICD-9, INA-CBGS, dan IDRG.

Tugas Anda:
1. Jawab pertanyaan tentang kode diagnosis dan prosedur
2. Bantu dengan klasifikasi penyakit sesuai ICD
3. Jelaskan tentang INA-CBGS dan IDRG
4. Berikan informasi kesehatan umum

Aturan:
- Gunakan bahasa Indonesia yang jelas dan profesional
- Berikan jawaban akurat berdasarkan standar medis
- Jika tidak tahu, jangan menebak - katakan tidak tahu
- Sertakan kode yang relevan dalam jawaban
- JANGAN gunakan format Markdown (**, __, dll)
- Gunakan format plain text dengan rapi
- Tetap sopan dan helpful

Format jawaban yang diharapkan:
- Kode ICD-10: [kode] - [deskripsi]
- Kode ICD-9: [kode] - [deskripsi] 
- INA-CBGS: [kode] - [prosedur] - [tarif]
- IDRG: [kode] - [kategori]"""

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": question
                }
            ],
            model="llama-3.1-8b-instant",  # ⚡
            temperature=0.3,
            max_tokens=2000,
            top_p=0.9
        )
        
        return chat_completion.choices[0].message.content
        
    except Exception as e:
        return f"❌ Error AI: {str(e)}"

def main():
    if not TELEGRAM_TOKEN or not GROQ_API_KEY:
        print("ERROR: Token tidak ditemukan. Pastikan file .env sudah diisi!")
        return
    
    # Create application
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Add handlers - PRIORITAS: Command dulu
    application.add_handler(CommandHandler("pmik", pmik_command))
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    
    # Message handlers
    application.add_handler(MessageHandler(
        filters.TEXT & filters.ChatType.PRIVATE & ~filters.COMMAND, 
        handle_private_message
    ))
    application.add_handler(MessageHandler(
        filters.TEXT & filters.ChatType.GROUPS & ~filters.COMMAND, 
        handle_group_message
    ))
    
    print("🤖 pmikBot dengan Groq AI sedang berjalan...")
    print("✅ Command /pmik sudah aktif")
    print("🚀 Groq AI: llama-3.1-8b-instant")  # ⚡ 
    print("⏹️ Tekan Ctrl+C untuk menghentikan")
    
    application.run_polling()

if __name__ == "__main__":
    main()