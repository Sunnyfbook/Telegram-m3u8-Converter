import subprocess
import os
from urllib.parse import urlparse
from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters, ConversationHandler
from telegram.constants import ParseMode

# User's Telegram bot token
TELEGRAM_BOT_TOKEN = '6795358263:AAE3FittU66qtJsI5b3gsM9U5F4KnFacBjc'

# Replace with your private channel ID (should start with -100)
CHANNEL_ID = -100123456789  # Replace this with your actual channel ID

# Conversation states
URL, TITLE = range(2)

def convert_m3u8_to_mp4(m3u8_url, output_file):
    command = [
        'ffmpeg',
        '-i', m3u8_url,
        '-c', 'copy',
        '-bsf:a', 'aac_adtstoasc',
        output_file
    ]
    subprocess.run(command, check=True)

def is_valid_m3u8_url(url):
    parsed_url = urlparse(url)
    path = parsed_url.path
    return path.endswith('.m3u8') or '.m3u8' in path

def generate_file_name(url):
    parsed_url = urlparse(url)
    path = parsed_url.path
    file_name = os.path.basename(path)
    name_without_extension = os.path.splitext(file_name)[0]
    return f"{name_without_extension}.mp4"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Send me a .m3u8 URL to begin the conversion process.')
    return URL

async def get_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    m3u8_url = update.message.text
    if not is_valid_m3u8_url(m3u8_url):
        await update.message.reply_text('Please send a valid .m3u8 URL.')
        return URL

    context.user_data['m3u8_url'] = m3u8_url
    await update.message.reply_text('Great! Now, please provide a title for this video.')
    return TITLE

async def get_title_and_process(update: Update, context: ContextTypes.DEFAULT_TYPE):
    title = update.message.text
    m3u8_url = context.user_data['m3u8_url']

    await update.message.reply_text('Converting .m3u8 to MP4 and sending to the private channel. This may take a while...')

    file_name = generate_file_name(m3u8_url)
    output_file = file_name

    try:
        convert_m3u8_to_mp4(m3u8_url, output_file)
        
        with open(output_file, 'rb') as video_file:
            caption = f"🎬 <b>{title}</b>\n\n" \
                      f"🚀 <i>Enjoy your video!</i>"

            sent_message = await context.bot.send_video(
                chat_id=CHANNEL_ID,
                video=InputFile(video_file, filename=file_name),
                caption=caption,
                parse_mode=ParseMode.HTML,
                supports_streaming=True
            )
        
        # Enable reactions for the sent message
        await context.bot.set_message_reaction(
            chat_id=CHANNEL_ID,
            message_id=sent_message.message_id,
            reaction=True  # This enables default reaction set
        )

        await update.message.reply_text(f'Video "{title}" has been sent to the private channel and reactions are enabled.')
        os.remove(output_file)
    except Exception as e:
        await update.message.reply_text(f'An error occurred: {str(e)}')

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Operation cancelled. Send me a new .m3u8 URL when you\'re ready.')
    return ConversationHandler.END

def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            URL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_url)],
            TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_title_and_process)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(conv_handler)

    application.run_polling()

if __name__ == '__main__':
    main()
