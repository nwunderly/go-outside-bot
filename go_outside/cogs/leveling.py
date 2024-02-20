import datetime
import time

import disnake
from disnake.ext import commands
from loguru import logger


def to_unix(dt: datetime.datetime) -> float:
    return time.mktime(dt.timetuple())


def calculate_points(time_since: float) -> int:
    return int((time_since // 1) ** 2)


class Leveling(commands.Cog):
    """Inverse leveling."""

    def __init__(self, bot):
        self.bot = bot

        self.last_action_cache: dict[int, tuple[str, float]] = (
            {}
        )  # user_id: (action, timestamp)
        self.points: dict[int, int] = {}  # user_id: points

    async def process_action(self, user: disnake.Member, action: str, timestamp: float):
        """When we detect an action by a user, update cache and assign points."""
        if user.id not in self.last_action_cache:
            logger.debug(
                f"adding user to cache | {user.id=} {user.name=} | {action=} {timestamp=}"
            )
            self.last_action_cache[user.id] = (action, timestamp)
            self.points[user.id] = 0
            return

        last_action, last_timestamp = self.last_action_cache[user.id]
        time_since = timestamp - last_timestamp

        # TODO: decide how to scale points
        # points = (time_since // 3600) ** 2
        points = calculate_points(time_since)

        new_points = self.points[user.id] + points
        logger.debug(
            f"updating user | {user.id=} {user.name=} | {action=} {timestamp=} | {last_action=} {last_timestamp=} "
            f"| {time_since=} {points=} | {new_points=}"
        )

        self.points[user.id] += points
        self.last_action_cache[user.id] = (action, timestamp)

    async def process_presence(self, before: disnake.Member, after: disnake.Member):
        """Handle things like presence updates"""
        pass

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message):
        await self.process_action(
            message.author, "message", to_unix(message.created_at)
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
    async def rank(self, ctx: commands.Context):
        """View level information."""
        points = self.points[ctx.author.id]
        await ctx.send(f"{points}")

    @commands.command()
    async def rankuser(self, ctx: commands.Context, user: disnake.User):
        """View level information for a user."""
        current_points = self.points.get(user.id)
        if current_points is None:
            return (await ctx.send("no"), None)[1]
        time_since = time.time() - self.last_action_cache[user.id][1]
        points = current_points + calculate_points(time_since)
        await ctx.send(f"{user} has {points} points")


def setup(bot):
    bot.add_cog(Leveling(bot))
