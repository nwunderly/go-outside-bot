import datetime
import itertools
import sys

import disnake
import psutil
import pygit2
from disnake.ext import commands
from loguru import logger

from go_outside.settings import Settings
from go_outside.utils.emojis import GIT, PYTHON
from go_outside.utils.format import approximate_timedelta


class General(commands.Cog):
    """General commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def format_commit(self, commit: pygit2.Commit):
        short, _, _ = commit.message.partition("\n")
        short_sha2 = commit.hex[0:6]
        commit_tz = datetime.timezone(
            datetime.timedelta(minutes=commit.commit_time_offset)
        )
        commit_time = datetime.datetime.fromtimestamp(commit.commit_time).astimezone(
            commit_tz
        )

        # [`hash`](url) message (offset)
        offset = approximate_timedelta(
            datetime.datetime.utcnow()
            - commit_time.astimezone(datetime.timezone.utc).replace(tzinfo=None)
        )
        return f"[`{short_sha2}`]({Settings.repo_url}/commit/{commit.hex}) {short} ({offset} ago)"

    def get_last_commits(self, count: int = 3):
        repo = pygit2.Repository(".git")
        commits = list(
            itertools.islice(
                repo.walk(repo.head.target, pygit2.GIT_SORT_TOPOLOGICAL), count
            )
        )
        return "\n".join(self.format_commit(c) for c in commits)

    @commands.command()
    async def about(self, ctx: commands.Context):
        """More info about the bot."""
        embed = disnake.Embed(
            color=Settings.embed_color, description=Settings.description
        )
        embed.set_author(name="Go Outside", icon_url=Settings.avatar_url)

        py_v = sys.version_info
        ver = (
            f"{PYTHON} Made with disnake {disnake.__version__}, Python {py_v.major}.{py_v.minor}.{py_v.micro}\n"
            f"\u200b"
        )
        embed.add_field(name="\u200b", value=ver, inline=False)

        embed.add_field(name="Source", value=f"[github]({Settings.repo_url})")
        # embed.add_field(name="Support server", value=f"[join]({Settings.support_url})")
        embed.add_field(name="Support server", value=f"soon:tm:")
        embed.add_field(name="Add me!", value=f"[invite]({Settings.invite_url})")

        revision = self.get_last_commits(2)
        embed.add_field(
            name="\u200b", value=f"{GIT} Recent commits:\n{revision}", inline=False
        )

        embed.set_footer(
            text=f"made with ❤ by nwunder",
            icon_url="https://avatars.githubusercontent.com/u/48489521?v=4",
        )
        embed.timestamp = self.bot.user.created_at
        await ctx.send(embed=embed)

    @commands.command()
    async def invite(self, ctx: commands.Context):
        """Get an invite link for the bot."""
        await ctx.send(f"[Invite me to your server!]({Settings.invite_url})")


def setup(bot):
    bot.add_cog(General(bot))
