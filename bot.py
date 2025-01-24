import logging
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, CallbackQueryHandler

# Configura el logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Token de tu bot de Telegram
TOKEN = 'TU_TOKEN_DE_TELEGRAM_BOT'

# Función para manejar el comando /start
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('¡Hola! Envíame el enlace de un video de YouTube y te enviaré la música.')

# Función para manejar el enlace de YouTube
def handle_youtube_link(update: Update, context: CallbackContext) -> None:
    # Obtener el enlace de YouTube del mensaje
    youtube_url = update.message.text

    # Verificar si el enlace es válido
    if "youtube.com/watch?v=" not in youtube_url:
        update.message.reply_text("Por favor, envía un enlace válido de YouTube.")
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
            update.message.reply_text("Elige la calidad del audio:", reply_markup=reply_markup)
        else:
            update.message.reply_text("No se pudo obtener la música del enlace proporcionado.")
    else:
        update.message.reply_text("Error al conectarse con la API.")

# Función para manejar la selección de calidad
def handle_quality_selection(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    # Obtener la calidad seleccionada
    quality = query.data.replace("quality_", "")

    # Obtener el enlace de YouTube guardado en el contexto
    youtube_url = context.user_data.get('youtube_url')
    if not youtube_url:
        query.edit_message_text("Error: No se encontró el enlace de YouTube.")
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
                    query.edit_message_text(f"Descargando {title} en {quality}...")
                    context.bot.send_audio(chat_id=query.message.chat_id, audio=audio_response.content, title=title)
                else:
                    query.edit_message_text("No se pudo descargar el archivo de audio.")
            else:
                query.edit_message_text(f"No se encontró la calidad {quality}.")
        else:
            query.edit_message_text("No se pudo obtener la música del enlace proporcionado.")
    else:
        query.edit_message_text("Error al conectarse con la API.")

def main() -> None:
    # Crear el Updater y pasarle el token de tu bot
    updater = Updater(TOKEN)

    # Obtener el dispatcher para registrar los handlers
    dispatcher = updater.dispatcher

    # Registrar los comandos y manejadores
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("download", handle_youtube_link))
    dispatcher.add_handler(CallbackQueryHandler(handle_quality_selection))

    # Manejar enlaces de YouTube enviados por el usuario
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_youtube_link))

    # Iniciar el bot
    updater.start_polling()

    # Mantener el bot en ejecución hasta que se presione Ctrl+C
    updater.idle()

if __name__ == '__main__':
    main()
