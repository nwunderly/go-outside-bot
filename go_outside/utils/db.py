import asyncio
import time

import disnake
from loguru import logger
from tortoise import Tortoise, fields
from tortoise.models import Model

from go_outside.settings import Settings

# async def edit_record(record: Model, **kwargs):
#     """Edit a record. Handles database query and caching."""
#     for key, value in kwargs.items():
#         record.__setattr__(key, value)
#     await record.save()
#     if isinstance(record, Config):
#         config_cache[record.guild_id] = record
#     elif isinstance(record, User):
#         user_cache[record.user_id] = record


class Config(Model):
    """Table in database storing guild configuration."""

    guild_id: int = fields.BigIntField(pk=True, generated=False)
    prefix: str = fields.TextField(default=Settings.prefix)


# Guild config cache. Stores None for unconfigured guilds to reduce database queries.
config_cache: dict[int, "Config"] = {}  # {guild_id: Config}


async def get_config(guild_id: int):
    "Get a guild config, if one exists. Return None otherwise."
    if guild_id not in config_cache:
        config = await Config.get_or_none(guild_id=guild_id)
        config_cache[guild_id] = config
        return config
    return config_cache[guild_id]


async def create_config(guild_id):
    """Create a config. Returns existing config if it exists."""
    config = await get_config(guild_id)
    if config:
        return config, False
    config = await Config.create(guild_id=guild_id)
    config_cache[guild_id] = config
    return config, True


async def update_config(config: Config, **kwargs):
    """Update a Config record. Handles database query and cache update."""
    for key, value in kwargs.items():
        setattr(config, key, value)
    await config.save()
    config_cache[config.guild_id] = config


# user_id: (action, timestamp)
# self.last_action_cache: dict[int, tuple[str, float]] = {}
# user_id: duration
# self.personal_best_cache: dict[int, int] = {}
# user_id: points
# self.points_cache: dict[int, int] = {}


class User(Model):
    """Table in database storing individual user data."""

    user_id: int = fields.BigIntField(pk=True, generated=False)
    last_action_type: str = fields.TextField()
    last_action_timestamp: int = fields.BigIntField()
    personal_best: int = fields.BigIntField()
    points: int = fields.BigIntField()


class UserCache:
    """Database caching for the User table."""

    # actual user cache
    user_cache: dict[int, "User"] = {}  # {user_id: User}

    # cache for batch updates
    last_batch_update: int = 0
    # User records that need to be updated
    batch_update_records: list["User"] = []
    # fields that have been updated across all records
    batch_update_fields: set[str] = set()


async def get_user(user_id: int):
    "Get a User, if it exists. Return None otherwise."
    if user_id not in UserCache.user_cache:
        db_user = await User.get_or_none(user_id=user_id)
        UserCache.user_cache[user_id] = db_user
        return db_user
    return UserCache.user_cache[user_id]


async def create_user(user_id: int) -> User:
    """Create a user."""
    db_user = await User.create(
        user_id=user_id,
        last_action_type="message_create",
        last_action_timestamp=time.time(),
        personal_best=0,
        points=0,
    )
    UserCache.user_cache[user_id] = db_user
    return db_user


async def update_user(db_user: User, **kwargs):
    """Update a user. Handles caching and bulk updates."""
    # NOTE: maybe use a set to track IDs if this starts getting big and slow
    if db_user not in UserCache.batch_update_records:
        UserCache.batch_update_records.append(db_user)

    for key, value in kwargs.items():
        setattr(db_user, key, value)
        UserCache.batch_update_fields.add(key)

    if (
        time.time() - UserCache.last_batch_update
        >= Settings.Database.batch_update_interval
    ):
        # if a batch update is ongoing, don't queue a new one
        if not user_update_lock.locked():
            await batch_update_users()


user_update_lock = asyncio.Lock()


async def batch_update_users():
    """Run a bulk update on all the Users in the user_update_queue and reset the queue."""
    async with user_update_lock:
        # pull the cache/queue
        cached_objects = UserCache.batch_update_records
        cached_fields = UserCache.batch_update_fields
        logger.info(
            f"Executing batch update | {len(cached_objects)} users, {cached_fields=}"
        )
        await User.bulk_update(cached_objects, cached_fields)

        # empty the cache/queue, update timer
        UserCache.batch_update_records = []
        UserCache.batch_update_fields = set()
        UserCache.last_batch_update = time.time()


async def init(db_url: str):
    """Connect to the database."""
    logger.info("Connecting to database.")
    await Tortoise.init(db_url=db_url, modules={"models": ["go_outside.utils.db"]})
    # await Tortoise.generate_schemas()
