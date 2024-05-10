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

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    async def list_users(self, ctx: commands.Context):
        users = await db.User.all()
        msg = ""
        for db_user in users:
            user = self.bot.get_user(db_user.user_id)
            msg += f"{user or 'not cached'}: {db_user}\n"
        await ctx.send(msg)
