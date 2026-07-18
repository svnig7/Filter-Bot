import logging
import logging.config
import os
import traceback

from aiohttp import web
from pyrogram import Client, __version__, types
from pyrogram.raw.all import layer

from database.ia_filterdb import Media
from database.users_chats_db import db
from info import SESSION, API_ID, API_HASH, BOT_TOKEN, LOG_STR
from utils import temp

from typing import Union, Optional, AsyncGenerator

# ================= Logging =================

logging.config.fileConfig("logging.conf")
logging.getLogger().setLevel(logging.INFO)
logging.getLogger("pyrogram").setLevel(logging.ERROR)

# ================= Web Server =================

PORT = int(os.environ.get("PORT", 8080))


async def home(request):
    return web.Response(
        text="Bot is running!",
        content_type="text/plain"
    )


async def start_web_server():
    app = web.Application()
    app.router.add_get("/", home)

    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, host="0.0.0.0", port=PORT)
    await site.start()

    logging.info(f"Web server started on port {PORT}")


# ================= Bot =================

class Bot(Client):

    def __init__(self):
        super().__init__(
            name=SESSION,
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            workers=50,
            plugins={"root": "plugins"},
            sleep_threshold=5,
        )

    async def start(self):
        b_users, b_chats = await db.get_banned()

        temp.BANNED_USERS = b_users
        temp.BANNED_CHATS = b_chats

        await super().start()
        await Media.ensure_indexes()

        me = await self.get_me()

        temp.ME = me.id
        temp.U_NAME = me.username
        temp.B_NAME = me.first_name

        self.username = "@" + me.username

        logging.info(
            f"{me.first_name} with Pyrogram v{__version__} "
            f"(Layer {layer}) started on {me.username}."
        )

        logging.info(LOG_STR)

        # Start HTTP server
        await start_web_server()

    async def stop(self, *args):
        await super().stop()
        logging.info("Bot stopped. Bye.")

    async def iter_messages(
        self,
        chat_id: Union[int, str],
        limit: int,
        offset: int = 0,
    ) -> Optional[AsyncGenerator["types.Message", None]]:

        current = offset

        while True:
            new_diff = min(200, limit - current)

            if new_diff <= 0:
                return

            messages = await self.get_messages(
                chat_id,
                list(range(current, current + new_diff + 1))
            )

            for message in messages:
                yield message
                current += 1


# ================= Run Bot =================

app = Bot()

try:
    app.run()
except Exception:
    traceback.print_exc()
