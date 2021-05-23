# import libraries
from typing import Dict
import json
import os
import ast
from loguru import logger
import pyrebase
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
)
from telegram import (
    ReplyKeyboardMarkup,
    Update,
    ReplyKeyboardRemove
)

# global vars
USER_TOKEN = ' '
MAIL, PASS, SIGN_IN = range(3)

# firebase config
with open("fb_config.json") as jsonfile:
    # `json.loads` parses a string in json format
    config_info = json.load(jsonfile)
    FB_CONFIG = config_info['FB_CONFIG']


# firebase init
firebase = pyrebase.initialize_app(FB_CONFIG)
storage = firebase.storage()
auth = firebase.auth()


## Telegram commands
def start(update: Update, _: CallbackContext) -> int:
    update.message.reply_text(
        "Hola! Soy el bot de SphinxAI. Ingresa tu mail."
    )
    logger.info(MAIL) 
    return MAIL

def token(update:Update, context:CallbackContext):
    update.message.reply_text(f'{USER_TOKEN}')    

# function to handle the /help command
def help(update, context):
    update.message.reply_text('help command received')


## util functions
def facts_to_str(user_data: Dict[str, str]) -> str:
    facts = list()

    for key, value in user_data.items():
        facts.append(f'{key} - {value}')

    return "\n".join(facts).join(['\n', '\n'])

def mail_insert(update: Update, context: CallbackContext) -> int:
    text = update.message.text
    context.user_data['email'] = text
    update.message.reply_text(f'Tu mail es {text.lower()}. Ahora escribí la contraseña que te comparitmos')
    logger.info(text)
    return PASS


def pass_insert(update: Update, context: CallbackContext) -> int:
    text = update.message.text
    context.user_data['pass'] = text
    logger.info(text)
    return sign_in(update, context)


def sign_in(update, context):
    global USER_TOKEN

    # user data
    email = context.user_data['email']  
    password = context.user_data['pass']

    # Log the user in
    try:
        user = auth.sign_in_with_email_and_password(email, password)
        USER_TOKEN = user['idToken']

        update.message.reply_text(f'no jodas pablito: {USER_TOKEN}')

        # os.mkdir(f'media/{update.message.from_user.username}')
        return ConversationHandler.END
    except:
        update.message.reply_text(f'La contraseña es incorrecta. Intenta nuevamente.')

def silentremove(filename):
    try:
        os.remove(filename)
    except OSError:
        pass


# function to handle errors occured in the dispatcher 
def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning(f'Update "{update}" caused error "{context.error}"')


# function to handle normal text 
def text_handler(update, context):
    text_received = update.message.text
    update.message.reply_text(f'did you said "{text_received}" ?')


def video_handler(update, context):
    file_id = update.message.video.file_id
    file = context.bot.getFile(file_id)
    logger.info("file_id: " + str(file_id))

    dest_path = f'{file_id}.mp4'

    file.download(dest_path)
    logger.info(f"file {str(file_id)[:5]} stored locally.")
    
    storage.child(dest_path).\
        put(dest_path, USER_TOKEN)
    logger.info(f"file {str(file_id)[:5]} uploaded.")

    silentremove(dest_path)
    logger.info(f"file {str(file_id)[:5]} removed from local dir.")


def photo_handler(update, context):
    from io import BytesIO
    file_id = update.message.photo[-1]['file_id']
    file = context.bot.getFile(file_id)
    f =  BytesIO(file.download_as_bytearray())
    logger.info("file_id: " + str(file_id))

    dest_path = f'{file_id}.jpg'

    file.download(dest_path)
    logger.info(f"file {str(file_id)[:5]} stored locally.")
    
    storage.child(dest_path).\
        put(dest_path, USER_TOKEN)
    logger.info(f"file {str(file_id)[:5]} uploaded.")

    silentremove(dest_path)
    logger.info(f"file {str(file_id)[:5]} removed from local dir.")




def main() -> None:
    TOKEN = os.environ['TOKEN']
    # Create the Updater and pass it your bot's token.
    updater = Updater(TOKEN, use_context=True)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Add conversation handler with the states CHOOSING, TYPING_CHOICE and TYPING_REPLY
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            MAIL: [
                MessageHandler(
                    Filters.regex('^(\w|\.|\_|\-)+[@](\w|\_|\-|\.)+[.]\w{2,3}$'), mail_insert
                )
            ],
            PASS: [
                MessageHandler(
                    Filters.text, pass_insert
                )
            ]
        },
        fallbacks=[MessageHandler(Filters.regex('^Done$'), error)],
    )

    dispatcher.add_handler(conv_handler)
    dispatcher.add_handler(CommandHandler("help", help))
    dispatcher.add_handler(CommandHandler("token", token))

    # add handler for files
    dispatcher.add_handler(MessageHandler(Filters.video, video_handler))
    dispatcher.add_handler(MessageHandler(Filters.photo, photo_handler))

    # add an handler for normal text (not commands)
    dispatcher.add_handler(MessageHandler(Filters.text, text_handler))

    # add an handler for errors
    dispatcher.add_error_handler(error)

    # start your shiny new bot
    updater.start_polling()

    # run the bot until Ctrl-C
    updater.idle()


if __name__ == '__main__':
    main()