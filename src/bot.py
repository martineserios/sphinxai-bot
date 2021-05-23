#!/usr/bin/env python

from __future__ import print_function
import os
import pickle
import telegram
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters
from googleapiclient.http import MediaFileUpload
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

from loguru import logger


def getCreds():
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    creds = None
    SCOPES = 'https://www.googleapis.com/auth/drive'

    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return creds

def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Upload files here.")


def file_uploader(filename, update, context):
    """handles the uploaded files"""

    service = build('drive', 'v3', credentials=getCreds(),cache_discovery=False)

    metadata = {'name': filename}
    media = MediaFileUpload(filename, chunksize=1024 * 1024,  resumable=True)#mimetype=doc.mime_type,
    request = service.files().create(body=metadata,
                                media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
    if status:
        print( "Uploaded %d%%." % int(status.progress() * 100))

    context.bot.send_message(chat_id=update.effective_chat.id, text="✅ File uploaded!")


def video_handler(update, context):
    file_id = update.message.video.file_id
    file = context.bot.getFile(file_id)
    print ("file_id: " + str(file_id))
    filename = f'{file_id}.mp4'
    file.download(f'/temp_media/{filename}')

    file_uploader(filename, update, context)



def photo_handler(update, context):
    file_id = update.message.photo[2]['file_id']
    file = context.bot.getFile(file_id)
    print ("file_id: " + str(file_id))
    filename = f'{file_id}.jpg'
    file.download(f'/temp_media/{filename}')

    file_uploader(filename, update, context)


def silentremove(filename):
    try:
        os.remove(filename)
    except OSError:
        pass

def error(bot, update, error):
    logger.warning('Update "%s" caused error "%s"', update, error)

def main():
    TOKEN = os.environ['TOKEN']
    updater = Updater(TOKEN,use_context=True)
    dispatcher = updater.dispatcher
    updater.dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(MessageHandler(Filters.video, video_handler))
    dispatcher.add_handler(MessageHandler(Filters.photo, photo_handler))
    # add an handler for errors
    dispatcher.add_error_handler(error)
    updater.start_polling()

if __name__ == '__main__':
    main()

















# # loading libraries
# import os
# import logging

# from telegram import bot
# from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
# import pyrebase

# # firebase config
# FB_CONFIG = {
#     'apiKey': "AIzaSyDkWhwdysVn-ad4a593x8btqsoLF8xIr8I",
#     'authDomain': "sphinxai.firebaseapp.com",
#     'projectId': "sphinxai",
#     'storageBucket': "sphinxai.appspot.com",
#     'messagingSenderId': "642635082133",
#     'appId': "1:642635082133:web:346902227bd04b3746ee9c",
#     'measurementId': "G-HXG4SLT1JF"
# }

# firebase = pyrebase.initialize_app(FB_CONFIG)
# storage = firebase.storage()


# # Enable logging
# logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#                     level=logging.INFO)

# logger = logging.getLogger(__name__)

# # function to handle the /start command
# def start(update, context):
#     update.message.reply_text('no jodas pablito')
#     os.mkdir(f'media/{update.message.from_user.username}')

# # function to handle the /help command
# def help(update, context):
#     update.message.reply_text('help command received')

# # function to handle errors occured in the dispatcher 
# def error(update, context):
#     """Log Errors caused by Updates."""
#     logger.warning('Update "%s" caused error "%s"', update, context.error)

# # function to handle normal text 
# def text_handler(update, context):
#     text_received = update.message.text
#     update.message.reply_text(f'did you said "{text_received}" ?')

# def video_handler(update, context):
#     file_id = update.message.video.file_id
#     file = context.bot.getFile(file_id)
#     print ("file_id: " + str(file_id))

#     file.download(f'media/{update.message.from_user.username}/{file_id}.mp4')
#     storage.child(f'media/{update.message.from_user.username}/{file_id}.mp4')\
#         .put(f'media/{update.message.from_user.username}/{file_id}.mp4')


# def photo_handler(update, context):
#     file_id = update.message.photo[0]['file_id']
#     file = context.bot.getFile(file_id)
#     print ("file_id: " + str(update.message.photo[0]['file_id']))

#     file.download(f'media/{update.message.from_user.username}/{file_id}.jpg')
#     storage.child(f'media/{update.message.from_user.username}/{file_id}.jpg')\
#         .put(f'media/{update.message.from_user.username}/{file_id}.jpg')


# def main():
#     TOKEN = os.environ['TOKEN']

#     # create the updater, that will automatically create also a dispatcher and a queue to 
#     # make them dialoge
#     updater = Updater(TOKEN, use_context=True)
#     dispatcher = updater.dispatcher

#     # add handlers for start and help commands
#     dispatcher.add_handler(CommandHandler("start", start))
#     dispatcher.add_handler(CommandHandler("help", help))
    
#     # add handler for files
#     dispatcher.add_handler(MessageHandler(Filters.video, video_handler))
#     dispatcher.add_handler(MessageHandler(Filters.photo, photo_handler))

#     # add an handler for normal text (not commands)
#     dispatcher.add_handler(MessageHandler(Filters.text, text_handler))

#     # add an handler for errors
#     dispatcher.add_error_handler(error)

#     # start your shiny new bot
#     updater.start_polling()

#     # run the bot until Ctrl-C
#     updater.idle()

# if __name__ == '__main__':
#     main()