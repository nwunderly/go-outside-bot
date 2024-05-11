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
        db_users = await db.User.all()
        if not db_users:
            await ctx.send("Database is empty.")
            return
        msg = ""
        for db_user in db_users:
            user = self.bot.get_user(db_user.user_id)
            msg += (
                f"{db_user.user_id} ({user or 'not cached'}): points={db_user.points}\n"
            )
        await ctx.send(msg)


def setup(bot: commands.Bot):
    bot.add_cog(Admin(bot))
