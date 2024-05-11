import os

import dotenv

from .bot import GoOutside
from .settings import Settings


def main():
    dotenv.load_dotenv(override=True)
    token = os.getenv("BOT_TOKEN")
    db_url = os.getenv("DB_URL")

    bot = GoOutside(token, db_url)
    bot.run()


if __name__ == "__main__":
    main()
