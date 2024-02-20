import disnake
from disnake.ext import commands
from loguru import logger

from .settings import Settings


class GoOutside(commands.AutoShardedBot):
    def __init__(self, token: str):
        super().__init__(
            command_prefix=Settings.prefix,
            case_insensitive=True,
            description=Settings.description,
            help_command=Settings.help_command,
            intents=Settings.intents,
            allowed_mentions=Settings.allowed_mentions,
        )
        self.__token = token

    async def on_ready(self):
        logger.info(f"Logged in as {self.user}.")

    def run(self):
        super().run(self.__token)

    def load_cogs(self, cog_names):
        logger.info("Loading cogs.")
        for cog in cog_names:
            try:
                self.load_extension(cog)
                # await self.load_cog(cog)
                logger.debug(f"Loaded {cog}.")
            except:
                logger.exception(f"Failed to load extension {cog}.")
