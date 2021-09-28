# import libs
import json

# global vars
USER_TOKEN = ' '
MAIL, PASS, SIGN_IN = range(3)
POSITION = ""
# USER and collection map
USER_SHEET_MAP = {
    710037683 : 'MARINA'
    }

# firebase config
with open("/app/fb_config.json") as jsonfile:
    # `json.loads` parses a string in json format
    config_info = json.load(jsonfile)
    FB_CONFIG = config_info['FB_CONFIG']
