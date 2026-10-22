from pyrogram import Client, idle
from pyromod import Client as modClient
from config import *

def user_session():
    try:
        user = Client(
            "Luffy",
            API_ID,
            API_HASH,
            session_string=SESSION_STRING,
        )
        return user
    except:
        user = None
    return user

class Zoro(Client):
    def __init__(self):
        self.bot: modClient = modClient(
            "Zoro",
            API_ID,
            API_HASH,
            plugins=dict(root="plugins"),
            bot_token=BOT_TOKEN
        )
        self.user: Client = Client(
            "Luffy",
            API_ID,
            API_HASH,
            session_string=SESSION_STRING,
        )

    async def start_bot(self):
        await self.bot.start()
        print(f"@{self.bot.me.username} is alive now!")
    # try:
    #     async def start_user(self):
    #         await self.user.start()
    #         print("User bot is alive now")
    #         me = await marimo.user.get_me()
    #         print(f"✅ ID: {me.id}")
    #         print(f"👤 Username: @{me.username}" if me.username else "Username: None")
    #         print(f"📛 First Name: {me.first_name or ''}")
    #         print(f"💬 Full Name: {me.first_name} {me.last_name or ''}".strip())
    # except:
    #     print("SESSION FAILED TO CONNECT PLEASE IGNORE IF NOT NEEDED")

    async def stop(self):
        await self.bot.stop()
        try: await self.user.stop()
        except: print()
        print("Bot is dead now")

    async def start_up(self):
        await self.start_bot()
        # try:
        #     await self.start_user()
        # except Exception as e:
        #     print(f"An error occurred while starting the userbot: {e}")
        await idle()


marimo = Zoro()
