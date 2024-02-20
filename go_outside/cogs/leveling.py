import datetime
import time

import disnake
from disnake.ext import commands
from loguru import logger

from go_outside.settings import Settings


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

        # user_id: (action, timestamp)
        self.last_action_cache: dict[int, tuple[str, float]] = {}
        # user_id: duration
        self.personal_best_cache: dict[int, int] = {}
        # user_id: points
        self.points_cache: dict[int, int] = {}

    async def process_action(self, user: disnake.Member, action: str, timestamp: float):
        """When we detect an action by a user, update cache and assign points."""
        # ignore bots
        if user.bot:
            return

        # ignore users who haven't opted in
        if user.id not in self.last_action_cache:
            return
            # logger.debug(
            #     f"adding user to cache | {user.id=} {user.name=} | {action=} {timestamp=}"
            # )
            # self.last_action_cache[user.id] = (action, timestamp)
            # self.points_cache[user.id] = 0
            # return

        last_action, last_timestamp = self.last_action_cache[user.id]
        time_since = timestamp - last_timestamp
        points = calculate_points(time_since)

        new_points = self.points_cache[user.id] + points
        logger.debug(
            f"updating user | {user.id=} {user.name=} | {action=} {timestamp=} | {last_action=} {last_timestamp=} "
            f"| {time_since=} {points=} | {new_points=}"
        )

        self.points_cache[user.id] += points
        self.last_action_cache[user.id] = (action, timestamp)

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

    @commands.Cog.listener()
    async def on_message_delete(self, message: disnake.Message):
        await self.process_action(
            message.author, "message_delete", to_unix(message.created_at)
        )

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
        self.last_action_cache[ctx.author.id] = (
            "message_create",
            to_unix(ctx.message.created_at),
        )
        self.personal_best_cache[ctx.author.id] = 0
        self.points_cache[ctx.author.id] = 0
        await ctx.send(
            f"Signup successful! Leave the game with `{Settings.prefix}unregister`."
        )

    @commands.command()
    async def unregister(self, ctx: commands.Context):
        """Delete your data from the bot and opt out of the game."""
        del self.last_action_cache[ctx.author.id]
        del self.personal_best_cache[ctx.author.id]
        del self.points_cache[ctx.author.id]
        await ctx.send("Successfully deleted your data from the bot.")

    @commands.command()
    async def rank(self, ctx: commands.Context):
        """View level information."""
        points = self.points_cache[ctx.author.id]
        await ctx.send(f"You have {points} points")

    # TODO: put this functionality into rank command
    @commands.command()
    async def rankuser(self, ctx: commands.Context, user: disnake.User):
        """View level information for a user."""
        current_points = self.points_cache.get(user.id)
        if current_points is None:
            return (await ctx.send("no"), None)[1]
        time_since = time.time() - self.last_action_cache[user.id][1]
        points = current_points + calculate_points(time_since)
        await ctx.send(f"{user} has {points} points (estimated)")


def setup(bot):
    bot.add_cog(Leveling(bot))
