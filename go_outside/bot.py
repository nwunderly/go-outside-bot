import asyncio
import datetime
import signal

import disnake
from disnake.ext import commands
from loguru import logger

from go_outside.settings import Settings
from go_outside.utils import db


async def prefix(bot: "GoOutside", message: disnake.Message, only_guild_prefix=False):
    """Get the prefix(es) for a guild. This is used by the bot internally,
    but can be called with only_guild_prefixes=True to remove mention prefix."""
    default = Settings.prefix
    if not message.guild:
        return commands.when_mentioned(bot, message) + [default]
    config = await db.get_config(message.guild.id)
    if config:
        p = config.prefix
    else:
        p = default
    if only_guild_prefix:
        return p
    else:
        return commands.when_mentioned(bot, message) + [p]


class GoOutside(commands.AutoShardedBot):
    def __init__(self, token: str, db_url: str):
        super().__init__(
            command_prefix=Settings.prefix,
            case_insensitive=True,
            description=Settings.description,
            help_command=Settings.help_command,
            intents=Settings.intents,
            allowed_mentions=Settings.allowed_mentions,
            activity=Settings.activity,
        )
        self.__token = token
        self.__db_url = db_url
        self.started_at = datetime.datetime.now()

    async def on_ready(self):
        logger.info(f"Logged in as {self.user}.")

    def run(self):
        """Custom run method, automatically passes token."""
        super().run(self.__token)

    async def start(self, *args, **kwargs):
        """Custom start method, handles async setup before login."""
        try:
            self.loop.remove_signal_handler(signal.SIGINT)
            self.loop.add_signal_handler(
                signal.SIGINT, lambda: asyncio.create_task(self.close())
            )
        except NotImplementedError:
            pass

        logger.info("Running bot setup.")
        await self.setup()

        logger.info("Running cog setup.")
        for name, cog in self.cogs.items():
            try:
                await cog.setup()
            except AttributeError:
                pass

        logger.info("Setup complete. Logging in.")
        await super().start(*args, **kwargs)

    async def close(self, exit_code=0):
        self._exit_code = exit_code

        logger.info("Running bot cleanup.")
        await self.cleanup()

        logger.info("Running cog cleanup.")
        for name, cog in self.cogs.items():
            try:
                await cog.cleanup()
            except AttributeError:
                pass

        logger.info("Closing connection to discord.")
        await super().close()

    def load_cogs(self, cog_names: list[str]):
        """Load cogs from a list of names."""
        logger.info("Loading cogs.")
        for cog in cog_names:
            try:
                self.load_extension(cog)
                logger.debug(f"Loaded {cog}.")
            except:
                logger.exception(f"Failed to load extension {cog}.")

    async def setup(self):
        """Called when bot is started, before login.
        Use this for any async tasks to be performed before the bot starts.
        (THE BOT WILL NOT BE LOGGED IN WHEN THIS IS CALLED)
        """
        await db.init(self.__db_url)
        self.load_cogs(Settings.cogs)

    async def cleanup(self):
        """Called when bot is closed, before logging out.
        Use this for any async tasks to be performed before the bot exits.
        """
        await db.Tortoise.close_connections()

    async def prefix(self, message: disnake.Message):
        """Gets the bot's prefix for a message in a guild. Does not include mention prefix."""
        return await prefix(self, message, only_guild_prefix=True)
