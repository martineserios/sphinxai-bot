# import libs
import pyrebase
from config import FB_CONFIG

class dbManager():
    
    def __init__(self) -> None:
        self.firebase = pyrebase.initialize_app(FB_CONFIG)
        self.db = self.firebase.database()

        