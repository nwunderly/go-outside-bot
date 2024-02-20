import disnake
from disnake.ext import commands


class Settings:
    prefix = "!!!"
    description = "Inverse leveling bot."

    intents = disnake.Intents.all()
    help_command = commands.MinimalHelpCommand()
    allowed_mentions = disnake.AllowedMentions.none()

    cogs = ["jishaku", "bot.cogs.leveling"]
