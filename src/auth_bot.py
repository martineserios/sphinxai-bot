# import libraries
from typing import Dict
import json
import os
from loguru import logger
from config import *
import pyrebase 
from urllib.parse import quote

############################
# Monkey patch pyrebase: replace quote function in pyrebase to workaround a bug.
# See https://github.com/thisbejim/Pyrebase/issues/294.
pyrebase.pyrebase.quote = lambda s, safe=None: s

# Monkey patch pyrebase: the Storage.get_url method does need quoting :|
def get_url(self, token=None):
    path = self.path
    self.path = None
    if path.startswith('/'):
        path = path[1:]
    if token:
        return "{0}/o/{1}?alt=media&token={2}".format(self.storage_bucket, quote(path, safe=''), token)
    return "{0}/o/{1}?alt=media".format(self.storage_bucket, quote(path, safe=''))

pyrebase.pyrebase.Storage.get_url = lambda self, token=None: \
    get_url(self, token)
#############################

from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
)
from telegram import (
    Update,
)

# # global vars
# USER_TOKEN = ' '
# MAIL, PASS, SIGN_IN = range(3)
# POSITION = ""
# # USER and collection map
# USER_SHEET_MAP = {
#     'martineserios': 'MARINA'
#     }

# # firebase config
# with open("/app/fb_config.json") as jsonfile:
#     # `json.loads` parses a string in json format
#     config_info = json.load(jsonfile)
#     FB_CONFIG = config_info['FB_CONFIG']


# firebase init
firebase = pyrebase.initialize_app(FB_CONFIG)
storage = firebase.storage()
auth = firebase.auth()

from db import dbManager
db_manager = dbManager()




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
    logger.info("file_id: " + str(file_id))
    file = context.bot.getFile(file_id)

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


def get_latest(update, context):
    user_id = update['message']['chat']['id']
    logger.info(user_id)
    table = USER_SHEET_MAP[user_id]
    logger.info(table)

    data = db_manager.db.child('1-baN5lUPSQnLS3NdHV86EYFlrn_FZkyvjIfalsTmrdM').child(table).get()
    logger.info([i for i in data.val()])

    _data = [j for j in data.val()]
    sorted_data = sorted(_data, key = lambda x:x['FECHA'], reverse=True)[0]

    return sorted_data



# def query_handler(update, context):
def get_latest_elo(update, context):
    sorted_data = get_latest(update, context)

    elo = sorted_data['ELO']

    update.message.reply_text(f'Tu ELO es: {elo}')  


# def query_handler(update, context):
def get_latest_vision_perif_error_td(update, context):
    sorted_data = get_latest(update, context)

    error = sorted_data['errores_td']

    update.message.reply_text(f'Tu error en el último test de visión periférica fue: {error}')


# def query_handler(update, context):
def get_latest_vision_perif_error_vista(update, context):
    sorted_data = get_latest(update, context)

    error = sorted_data['errores_vista']

    update.message.reply_text(f'El sector dónde más miraste fue : {error}')


def get_latest_tiempos(update, context):
    sorted_data = get_latest(update, context)

    tiempo_lvp = sorted_data['logical_tiempo_lvp']
    tiempo_cvp = sorted_data['creative_tiempo_cvp']

    update.message.reply_text(f'El tiempo del test de lógica fue {tiempo_lvp}seg y el del test de creatividad {tiempo_cvp}seg.')


def get_latest_repeticion(update, context):
    sorted_data = get_latest(update, context)

    repite = sorted_data['repite_fila']

    update.message.reply_text(f'{repite} repite fila.')


def get_latest_resistenccia(update, context):
    sorted_data = get_latest(update, context)

    map_values = {
        "0": u"\U0001F7E2", #green
        "1": u'\U0001F7E2',
        "2": u'\U0001F7E2',
        "3": u'\U0001F7E1', #yellow
        "4": u'\U0001F7E1',
        "5": u'\U0001F7E1',
        "6": u'\U0001F534', #red
        "7": u'\U0001F534',
        "8": u'\U0001F534',
        "9": u'\U0001F534'	
    }
    
    cuadrantes = ["a1", "a2", "a3", "b1", "b2", "b3", "c1", "c2", "c3"]

    initial_string = 'resistencia_ocular_pestaneo_x_cuadrante'
    cuadrante_dict = {cuadrante: map_values[sorted_data[f'{initial_string}_{cuadrante}']] for cuadrante in cuadrantes}

    [update.message.reply_text( f'{cuadrante.upper()}: {cuadrante_dict[cuadrante]}') for cuadrante in cuadrantes]

def get_latest_resistenccia(update, context):
    map_values = {
        "0": u"\U0001F7E2", #green
        "1": u'\U0001F7E2',
        "2": u'\U0001F7E2',
        "3": u'\U0001F7E1', #yellow
        "4": u'\U0001F7E1',
        "5": u'\U0001F7E1',
        "6": u'\U0001F534', #red
        "7": u'\U0001F534',
        "8": u'\U0001F534',
        "9": u'\U0001F534'	
    }

    user_id = update['message']['chat']['id']
    logger.info(user_id)
    table = USER_SHEET_MAP[user_id]
    logger.info(table)

    data = db_manager.db.child('1-baN5lUPSQnLS3NdHV86EYFlrn_FZkyvjIfalsTmrdM').child(table).get()
    logger.info([i for i in data.val()])

    _data = [j for j in data.val()]
    sorted_data = sorted(_data, key = lambda x:x['FECHA'], reverse=True)

    
    cuadrantes = ["a1", "a2", "a3", "b1", "b2", "b3", "c1", "c2", "c3"]

    initial_string = 'resistencia_ocular_pestaneo_x_cuadrante'
    cuadrante_dict = {cuadrante: map_values[sorted_data[f'{initial_string}_{cuadrante}']] for tests in sorted_data for cuadrante in tests}

    logger.info(cuadrante_dict)
    [update.message.reply_text( f'{cuadrante.upper()}: {cuadrante_dict[cuadrante]}') for cuadrante in cuadrantes]



def get_by_position(update, context: CallbackContext) -> str:
    user_id = update['message']['chat']['id']
    
    logger.info(f'The user {user_id} is querying the database to get its players by position ')

    # metric = db.child('1-baN5lUPSQnLS3NdHV86EYFlrn_FZkyvjIfalsTmrdM').child('LOS ANDES').order_by_child('posicion').get()
    # logger.info(f'ELO: {metric}')
    data = db_manager.db.child('1-baN5lUPSQnLS3NdHV86EYFlrn_FZkyvjIfalsTmrdM').child('LOS ANDES').order_by_child('POSICION').get()

    posiciones = set(val for sublist in [j['POSICION'].split(', ') for i,j in data.val().items()] for val in sublist)

    update.message.reply_text(f"Indique la posición: {posiciones}")

    return POSITION


def position_insert(update: Update, context: CallbackContext) -> str:
    text = update.message.text
    POSITION = text
    logger.info(text)
    # POSITION  = 'arquero'
    logger.info(POSITION)

    players = [i for i,j in db_manager.db.child('1-baN5lUPSQnLS3NdHV86EYFlrn_FZkyvjIfalsTmrdM').child('LOS ANDES').order_by_child('POSICION').equal_to(POSITION).get().val().items()]

    update.message.reply_text(f'{players}')


def main() -> None:
    TOKEN = os.environ['TOKEN']
    # Create the Updater and pass it your bot's token.
    updater = Updater(TOKEN, use_context=True)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Add conversation handler with the states CHOOSING, TYPING_CHOICE and TYPING_REPLY
    conv_handler_start = ConversationHandler(
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
        fallbacks=[MessageHandler(Filters.regex('^Done'), error)],
    )

    conv_handler_por_posicion = ConversationHandler(
        entry_points=[CommandHandler('porPosicion', get_by_position)],
        states={
            POSITION: [
                MessageHandler(
                    Filters.text, position_insert
                )
            ]
        },
        fallbacks=[MessageHandler(Filters.regex('^Done'), error)],
    )    

    dispatcher.add_handler(conv_handler_start)
    dispatcher.add_handler(conv_handler_por_posicion)
    dispatcher.add_handler(CommandHandler("help", help))
    dispatcher.add_handler(CommandHandler("token", token))
    dispatcher.add_handler(CommandHandler("ELO", get_latest_elo))
    dispatcher.add_handler(CommandHandler("DondeTengoMasErrores", get_latest_vision_perif_error_td))
    dispatcher.add_handler(CommandHandler("DondeMiroMAs", get_latest_vision_perif_error_vista))
    dispatcher.add_handler(CommandHandler("MisTiempos", get_latest_tiempos))
    dispatcher.add_handler(CommandHandler("RepiteFila", get_latest_repeticion))
    dispatcher.add_handler(CommandHandler("DondeTengoMasDificultades", get_latest_resistenccia))


    # dispatcher.add_handler(CommandHandler("porPosicion", get_by_position))
    # conv_handler = ConversationHandler(
    # entry_points=[CommandHandler('porPosicion', get_by_posiion)],
    # states={
    #     MAIL: [
    #         MessageHandler(
    #             Filters.regex('^(\w|\.|\_|\-)+[@](\w|\_|\-|\.)+[.]\w{2,3}$'), mail_insert
    #         )
    #     ],
    #     PASS: [
    #         MessageHandler(
    #             Filters.text, pass_insert
    #         )
    #     ]
    # },
    # fallbacks=[MessageHandler(Filters.regex('^Done$'), error)],
    # )

    # add handler for files
    # dispatcher.add_handler(MessageHandler(Filters.video, video_handler))
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