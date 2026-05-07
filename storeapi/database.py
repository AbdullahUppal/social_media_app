import databases
import sqlalchemy

from SettingsConfigDict import config

# variable that stores the info of our database
metadata = sqlalchemy.MetaData()


post_table = sqlalchemy.Table(
    "posts",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("body", sqlalchemy.String),
    sqlalchemy.Column("user_id", sqlalchemy.ForeignKey("users.id"), nullable=False),
)

user_table = sqlalchemy.Table(
    "users",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("email", sqlalchemy.String, unique=True, nullable=False),
    sqlalchemy.Column("password", sqlalchemy.String, nullable=False),
    sqlalchemy.Column("confirmed", sqlalchemy.Boolean, default=False),
)

comment_table = sqlalchemy.Table(
    "comments",
    metadata,
    # making columns in table
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("body", sqlalchemy.String),
    sqlalchemy.Column("post_id", sqlalchemy.ForeignKey("posts.id"), nullable=False),
    sqlalchemy.Column("user_id", sqlalchemy.ForeignKey("users.id"), nullable=False),
    sqlalchemy.Column("image_url", sqlalchemy.String, nullable=True),
)

like_table = sqlalchemy.Table(
    "likes",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("post_id", sqlalchemy.ForeignKey("posts.id"), nullable=False),
    sqlalchemy.Column("user_id", sqlalchemy.ForeignKey("users.id"), nullable=False),
)

# engine that allows the sqlalchemy to specific database like sqlite/postgre

if config.DATABASE_URL.startswith("sqlite"):
    print(config.DATABASE_URL)
    engine = sqlalchemy.create_engine(
        config.DATABASE_URL,
        connect_args={"check_same_thread": False},
    )
else:
    engine = sqlalchemy.create_engine(config.DATABASE_URL)

# tells engine to use metadata to create tables and column
db_args = {"min_size": 1, "max_size": 3} if "postgres" in config.DATABASE_URL else {}
metadata.create_all(engine)
database = databases.Database(
    config.DATABASE_URL, force_rollback=config.DB_FORCE_ROLL_BACK, **db_args
)
