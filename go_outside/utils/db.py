import json
from tortoise import Tortoise, fields
from tortoise.models import Model
from loguru import logger

from go_outside.settings import Settings


config_cache = {}  # {guild_id: Config}
user_cache = {}  # {user_id: User}


async def edit_record(record, **kwargs):
    for key, value in kwargs.items():
        record.__setattr__(key, value)
    await record.save()
    if isinstance(record, Config):
        config_cache[record.guild_id] = record
    elif isinstance(record, User):
        user_cache[record.user_id] = record


class Config(Model):
    guild_id = fields.BigIntField(pk=True, generated=False)
    prefix = fields.TextField(default=Settings.prefix)


"""
        # user_id: (action, timestamp)
        self.last_action_cache: dict[int, tuple[str, float]] = {}
        # user_id: duration
        self.personal_best_cache: dict[int, int] = {}
        # user_id: points
        self.points_cache: dict[int, int] = {}
"""


class User(Model):
    user_id = fields.BigIntField(pk=True, generated=False)
    last_action_type = fields.TextField()
    last_action_timestamp = fields.BigIntField()
    personal_best = fields.BigIntField()
    points = fields.BigIntField()


async def init(db_url):
    logger.info("Connecting to database.")
    await Tortoise.init(db_url=db_url, modules={"models": ["go_outside.utils.db"]})