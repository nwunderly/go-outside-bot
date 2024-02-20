import os

import dotenv

from .bot import GoOutside
from .settings import Settings


def main():
    dotenv.load_dotenv(override=True)
    token = os.getenv("BOT_TOKEN")

    bot = GoOutside(token)
    bot.load_cogs(Settings.cogs)
    bot.run()


if __name__ == "__main__":
    main()
