import logging
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackContext, CallbackQueryHandler, MessageHandler, filters

# Configura el logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Token de tu bot de Telegram
TOKEN = 'TU_TOKEN_DE_TELEGRAM_BOT'

# Función para manejar el comando /start
async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('¡Hola! Envíame el enlace de un video de YouTube y te enviaré la música.')

# Función para manejar el enlace de YouTube
async def handle_youtube_link(update: Update, context: CallbackContext) -> None:
    # Obtener el enlace de YouTube del mensaje
    youtube_url = update.message.text

    # Verificar si el enlace es válido
    if "youtube.com/watch?v=" not in youtube_url:
        await update.message.reply_text("Por favor, envía un enlace válido de YouTube.")
        return

    # Guardar el enlace en el contexto para usarlo después
    context.user_data['youtube_url'] = youtube_url

    # Llamar a la API para obtener las opciones de calidad
    api_url = f"https://api.agatz.xyz/api/ytmp3?url={youtube_url}"
    response = requests.get(api_url)

    if response.status_code == 200:
        data = response.json()
        if data["status"] == 200:
            # Crear botones para cada calidad disponible
            keyboard = []
            for audio in data["data"]:
                quality = audio["quality"]
                callback_data = f"quality_{quality}"
                keyboard.append([InlineKeyboardButton(quality, callback_data=callback_data)])

            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text("Elige la calidad del audio:", reply_markup=reply_markup)
        else:
            await update.message.reply_text("No se pudo obtener la música del enlace proporcionado.")
    else:
        await update.message.reply_text("Error al conectarse con la API.")

# Función para manejar la selección de calidad
async def handle_quality_selection(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    # Obtener la calidad seleccionada
    quality = query.data.replace("quality_", "")

    # Obtener el enlace de YouTube guardado en el contexto
    youtube_url = context.user_data.get('youtube_url')
    if not youtube_url:
        await query.edit_message_text("Error: No se encontró el enlace de YouTube.")
        return

    # Llamar a la API para obtener el enlace de descarga
    api_url = f"https://api.agatz.xyz/api/ytmp3?url={youtube_url}"
    response = requests.get(api_url)

    if response.status_code == 200:
        data = response.json()
        if data["status"] == 200:
            # Buscar el enlace de descarga para la calidad seleccionada
            download_url = None
            title = None
            for audio in data["data"]:
                if audio["quality"] == quality:
                    download_url = audio["downloadUrl"]
                    title = audio["title"]
                    break

            if download_url and title:
                # Descargar el archivo de audio
                audio_response = requests.get(download_url)
                if audio_response.status_code == 200:
                    # Enviar el archivo de audio al usuario
                    await query.edit_message_text(f"Descargando {title} en {quality}...")
                    await context.bot.send_audio(chat_id=query.message.chat_id, audio=audio_response.content, title=title)
                else:
                    await query.edit_message_text("No se pudo descargar el archivo de audio.")
            else:
                await query.edit_message_text(f"No se encontró la calidad {quality}.")
        else:
            await query.edit_message_text("No se pudo obtener la música del enlace proporcionado.")
    else:
        await query.edit_message_text("Error al conectarse con la API.")

def main() -> None:
    # Crear la aplicación
    application = ApplicationBuilder().token(TOKEN).build()

    # Registrar los comandos y manejadores
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("download", handle_youtube_link))
    application.add_handler(CallbackQueryHandler(handle_quality_selection))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_youtube_link))

    # Iniciar el bot
    application.run_polling()

if __name__ == '__main__':
    main()
