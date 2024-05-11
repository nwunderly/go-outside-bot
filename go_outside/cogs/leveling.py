import datetime
import time
import typing

import disnake
from disnake.ext import commands
from loguru import logger

from go_outside.settings import Settings
from go_outside.utils import db


def to_unix(dt: datetime.datetime) -> float:
    """Convert a datetime object to a unix time int."""
    return time.mktime(dt.timetuple())


def calculate_points(time_since: float) -> int:
    """Calculation determining how many points to assign to a user after an event."""
    # TODO: decide how to scale points
    # points = (time_since // 3600) ** 2
    return int((time_since // Settings.Leveling.points_scaling) ** 2)


def calculate_level(points: int) -> int:
    """Calculation determining what level a user is based on their points."""
    # TODO make this configurable, decide how to scale level
    return int(points ** (1 / 4))


class Leveling(commands.Cog):
    """Leveling system commands."""

    def __init__(self, bot: commands.Bot):
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

        # # ignore users who haven't opted in
        # if user.id not in db.user_cache:
        #     return
        #     # logger.debug(
        #     #     f"adding user to cache | {user.id=} {user.name=} | {action=} {timestamp=}"
        #     # )
        #     # self.last_action_cache[user.id] = (action, timestamp)
        #     # self.points_cache[user.id] = 0
        #     # return

        db_user = await db.get_user(user.id)  # will be None if user hasn't opted in

        # ignore users who haven't opted in
        if db_user is None:
            return

        last_action_type = db_user.last_action_type
        last_action_timestamp = db_user.last_action_timestamp
        time_since = timestamp_int - last_action_timestamp
        points_to_add = calculate_points(time_since)

        new_points = db_user.points + points_to_add
        logger.debug(
            f"updating user "
            f"| {user.id=} {user.name=} "
            f"| {action=} {timestamp_int=} "
            f"| {last_action_type=} {last_action_timestamp=} "
            f"| {time_since=} {points_to_add=} "
            f"| {new_points=}"
        )

        # self.points_cache[user.id] += points_to_add
        # self.last_action_cache[user.id] = (action, timestamp_int)

        # TODO: don't update the database every time PLEASE GOD
        # db_user.points = new_points
        # db_user.last_action_type = last_action_type
        # db_user.last_action_timestamp = last_action_timestamp
        # db.user_cache[user.id] = db_user
        # await db_user.save()
        await db.update_user(
            db_user,
            points=new_points,
            last_action_type=last_action_type,
            last_action_timestamp=timestamp,
        )

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
        await db.create_user(user_id=ctx.author.id)
        prefix = await self.bot.prefix(ctx.message)
        await ctx.send(f"Signup successful! Leave the game with `{prefix}unregister`.")

    @commands.command()
    async def unregister(self, ctx: commands.Context):
        """Delete your data from the bot and opt out of the game."""
        await db.User.filter(user_id=ctx.author.id).delete()
        del db.UserCache.user_cache[ctx.author.id]
        await ctx.send("Successfully deleted your data from the bot.")

    @commands.command()
    async def rank(
        self,
        ctx: commands.Context,
        user: typing.Union[disnake.User, disnake.Member] = None,
    ):
        """View level information."""
        if not user:
            user = ctx.author

        prefix = await self.bot.prefix(ctx.message)
        db_user = await db.get_user(user.id)

        if db_user is None:
            if user == ctx.author:
                await ctx.send(
                    f"You are not registered with the bot, use `{prefix}register` to register."
                )
                return
            else:
                await ctx.send("This user is not registered with the bot.")
                return

        points = db_user.points

        if user == ctx.author:
            await ctx.send(f"You have {points} points")
        else:
            await ctx.send(f"{user} has {points} points (estimated)")


def setup(bot: commands.Bot):
    bot.add_cog(Leveling(bot))
