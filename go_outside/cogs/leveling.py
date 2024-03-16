import datetime
import time
import typing

import disnake
from disnake.ext import commands
from loguru import logger

from go_outside.settings import Settings
from go_outside.utils import db


def to_unix(dt: datetime.datetime) -> float:
    return time.mktime(dt.timetuple())


def calculate_points(time_since: float) -> int:
    # TODO: decide how to scale points
    # points = (time_since // 3600) ** 2
    return int((time_since // Settings.Leveling.points_scaling) ** 2)


class Leveling(commands.Cog):
    """Leveling system commands."""

    def __init__(self, bot):
        self.bot = bot

        # # user_id: (action, timestamp)
        # self.last_action_cache: dict[int, tuple[str, float]] = {}
        # # user_id: duration
        # self.personal_best_cache: dict[int, int] = {}
        # # user_id: points
        # self.points_cache: dict[int, int] = {}

    async def process_action(self, user: disnake.Member, action: str, timestamp: float):
        """When we detect an action by a user, update cache and assign points."""
        timestamp_int: int = int(timestamp)

        # ignore bots
        if user.bot:
            return

        # ignore users who haven't opted in
        if user.id not in db.user_cache:
            return
            # logger.debug(
            #     f"adding user to cache | {user.id=} {user.name=} | {action=} {timestamp=}"
            # )
            # self.last_action_cache[user.id] = (action, timestamp)
            # self.points_cache[user.id] = 0
            # return

        db_user = db.user_cache[user.id]

        last_action_type = db_user.last_action_type
        last_action_timestamp = db_user.last_action_timestamp
        time_since = timestamp_int - last_action_timestamp
        points_to_add = calculate_points(time_since)

        new_points = db_user.points + points_to_add
        logger.debug(
            f"updating user | {user.id=} {user.name=} | {action=} {timestamp_int=} | {last_action_type=} {last_action_timestamp=} "
            f"| {time_since=} {points_to_add=} | {new_points=}"
        )

        # self.points_cache[user.id] += points_to_add
        # self.last_action_cache[user.id] = (action, timestamp_int)

        # TODO: don't update the database every time PLEASE GOD
        db_user.points = new_points
        db_user.last_action_type = last_action_type
        db_user.last_action_timestamp = last_action_timestamp

    async def process_presence(self, before: disnake.Member, after: disnake.Member):
        """Handle things like presence updates"""
        pass

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message):
        await self.process_action(
            message.author, "message_create", to_unix(message.created_at)
        )

    @commands.Cog.listener()
    async def on_message_edit(self, message: disnake.Message):
        await self.process_action(
            message.author, "message_edit", to_unix(message.created_at)
        )

    # @commands.Cog.listener()
    # async def on_message_delete(self, message: disnake.Message):
    #     await self.process_action(
    #         message.author, "message_delete", to_unix(message.created_at)
    #     )

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: disnake.Reaction, user: disnake.Member):
        await self.process_action(user, "reaction_add", time.time())

    @commands.Cog.listener()
    async def on_reaction_remove(self, reaction, user: disnake.Member):
        await self.process_action(user, "reaction_remove", time.time())

    @commands.Cog.listener()
    async def on_typing(self, channel, user: disnake.Member, when: datetime.datetime):
        await self.process_action(user, "typing", to_unix(when))

    @commands.Cog.listener()
    async def on_voice_state_update(self, user: disnake.Member, before, after):
        await self.process_action(user, "voice_state_update", time.time())

    @commands.Cog.listener()
    async def on_presence_update(self, before: disnake.Member, after: disnake.Member):
        await self.process_action(after, "presence_update", time.time())

    @commands.command()
    async def register(self, ctx: commands.Context):
        """Join the game!"""
        db_user = await db.User.create(
            user_id=ctx.author.id,
            last_action_type="message_create",
            last_action_timestamp=to_unix(ctx.message.created_at),
            personal_best=0,
            points=0,
        )
        db.user_cache[ctx.author.id] = db_user
        await ctx.send(
            f"Signup successful! Leave the game with `{Settings.prefix}unregister`."
        )

    @commands.command()
    async def unregister(self, ctx: commands.Context):
        """Delete your data from the bot and opt out of the game."""
        await db.User.filter(user_id=ctx.author.id).delete()
        del db.user_cache[ctx.author.id]
        await ctx.send("Successfully deleted your data from the bot.")

    @commands.command()
    async def rank(self, ctx: commands.Context, user: typing.Union[disnake.User, disnake.Member] = None):
        """View level information."""
        if not user:
            user = ctx.author

        prefix = await self.bot.prefix(ctx.message)

        if user.id not in db.user_cache:
            await ctx.send(f"You are not registered with the bot, use `{prefix}register` to register.")

        db_user = db.user_cache[user.id]
        points = db_user.points

        if user == ctx.author:
            await ctx.send(f"You have {points} points")
        else:
            await ctx.send(f"{user} has {points} points (estimated)")


def setup(bot):
    bot.add_cog(Leveling(bot))
