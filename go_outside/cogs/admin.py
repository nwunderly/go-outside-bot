import datetime
import time
import typing

import disnake
from disnake.ext import commands
from loguru import logger

from go_outside.settings import Settings
from go_outside.utils import db


class Admin(commands.Cog):
    """Administration commands."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def list_users(self, ctx):
        pass
