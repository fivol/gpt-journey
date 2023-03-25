
from sqlalchemy import create_engine, MetaData, Integer, ForeignKey, UniqueConstraint, text, Text
from sqlalchemy import Table, Column, BigInteger, String, DateTime
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from sqlalchemy.orm import sessionmaker

from jouney.config import config

engine = create_engine(config.DB_URL, echo=False, isolation_level='AUTOCOMMIT')

metadata = MetaData(bind=engine)

SessionLocal = sessionmaker(autocommit=True, autoflush=False, bind=engine)

ts_field = TIMESTAMP(timezone=True)
ts_default = text("(now() at time zone 'utc')")

users_table = Table(
    "users",
    metadata,
    Column("id", BigInteger, primary_key=True),
    Column("name", String(256), nullable=True),
    Column("username", String(256), nullable=True),
    Column("ts", ts_field, nullable=False, server_default=ts_default),
)

stories_table = Table(
    "stories",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("ts", ts_field, nullable=False, server_default=ts_default),
    Column("user_id", BigInteger(), ForeignKey('users.id')),
    Column("prompt", Text(), nullable=True),
)


story_items_table = Table(
    "story_items",
    metadata,
    Column("id", Integer(), primary_key=True),
    Column("story_id", Integer(), ForeignKey('stories.id')),
    Column("ts", ts_field, nullable=False, server_default=ts_default),
    Column("text", Text(), nullable=False),
    Column("option", Integer(), nullable=True),
    Column("img", Text(), nullable=False),
)


# metadata.drop_all()
metadata.create_all()
