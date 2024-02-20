import disnake
from disnake.ext import commands


class Settings:
    prefix = "--"
    description = (
        "A Discord bot with an inverse leveling system that rewards you for inactivity."
    )
    author = "nwunder"

    embed_color = disnake.Color(0x3B964E)

    avatar_url = "https://cdn.discordapp.com/avatars/1209320739438723093/9495ce052daa9093ad10cdd63c50d17c.png"
    invite_url = (
        "https://discord.com/oauth2/authorize?client_id=1209320739438723093&scope=bot"
    )
    support_url = "soon:tm:"
    repo_url = "https://github.com/nwunderly/go-outside-bot"

    intents = disnake.Intents.all()
    help_command = commands.MinimalHelpCommand()
    allowed_mentions = disnake.AllowedMentions.none()

    cogs = ["jishaku", "go_outside.cogs.general", "go_outside.cogs.leveling"]

    activity = disnake.Game("outside")

    class Leveling:
        points_scaling = 1  # 1 for seconds, 3600 for hours
