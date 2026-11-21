from os import getenv
from dotenv import load_dotenv
from pymongo import MongoClient

#Necessary Variables 
API_ID = int(getenv("API_ID", ))
API_HASH = getenv("API_HASH", "")
BOT_TOKEN = getenv("BOT_TOKEN", "") #Put your bot token here
CHANNEL = getenv("CHANNEL", "bot_list_hub") #Your public channel username without @ for force subscription.
MONGO = getenv("MONGO", "") #Put mongo db url here
#Optional Variables
OWNER_ID = int(getenv("OWNER_ID", 5446536405)) #Go to @ThunderrXbot and type /id and put that value here. 
FSUB = bool(getenv("FSUB", False)) #Set this True if you want to enable force subscription from users else set to False.
SESSION_STRING = ""
