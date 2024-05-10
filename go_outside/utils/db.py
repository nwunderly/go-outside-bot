import disnake
from loguru import logger
from tortoise import Tortoise, fields
from tortoise.models import Model

from go_outside.settings import Settings


async def edit_record(record: Model, **kwargs):
    """Edit a record. Handles database query and caching."""
    for key, value in kwargs.items():
        record.__setattr__(key, value)
    await record.save()
    if isinstance(record, Config):
        config_cache[record.guild_id] = record
    elif isinstance(record, User):
        user_cache[record.user_id] = record


config_cache: dict[int, "Config"] = {}  # {guild_id: Config}


class Config(Model):
    guild_id: int = fields.BigIntField(pk=True, generated=False)
    prefix: str = fields.TextField(default=Settings.prefix)


async def get_config(guild: disnake.Guild):
    "Get a guild config, if one exists. Return None otherwise."
    if guild.id not in config_cache:
        config = await Config.get_or_none(guild_id=guild.id)
        config_cache[guild.id] = config
        return config
    return config_cache[guild.id]


async def create_config(guild: disnake.Guild):
    """Create a config. Returns existing config if it exists."""
    if config_cache.get(guild.id) or await Config.exists(guild_id=guild.id):
        return config, False
    config = await Config.create(guild_id=guild.id)
    config_cache[guild.id] = config
    return config, True


"""
        # user_id: (action, timestamp)
        self.last_action_cache: dict[int, tuple[str, float]] = {}
        # user_id: duration
        self.personal_best_cache: dict[int, int] = {}
        # user_id: points
        self.points_cache: dict[int, int] = {}
"""


user_cache: dict[int, "User"] = {}  # {user_id: User}


class User(Model):
    user_id: int = fields.BigIntField(pk=True, generated=False)
    last_action_type: str = fields.TextField()
    last_action_timestamp: int = fields.BigIntField()
    personal_best: int = fields.BigIntField()
    points: int = fields.BigIntField()


async def get_user(user: disnake.User | disnake.Member):
    "Get a guild config, if one exists. Return None otherwise."
    if user.id not in config_cache:
        config = await User.get_or_none(user_id=user.id)
        config_cache[user.id] = config
        return config
    return config_cache[user.id]


async def create_user(user: disnake.User | disnake.Member):
    """Create a user. Returns existing user if it exists."""
    if user_cache.get(user.id) or await User.exists(user_id=user.id):
        return user, False
    user = await User.create(user_id=user.id)
    user_cache[user.id] = user
    return user, True


async def init(db_url):
    logger.info("Connecting to database.")
    await Tortoise.init(db_url=db_url, modules={"models": ["go_outside.utils.db"]})
