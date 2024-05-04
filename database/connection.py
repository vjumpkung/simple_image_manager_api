# create sqlite database
import sqlite3
from sqlmodel import Field, SQLModel, create_engine
import config.load_config as CONFIG

# create database.db file if not exists

with open("database.db", "a") as f:
    pass


class Images(SQLModel, table=True):
    image_id: str = Field(primary_key=True)
    type: str
    file_name: str


sqlite_url = "sqlite:///database.db"
engine = create_engine(sqlite_url, echo=not CONFIG.PRODUCTION)

SQLModel.metadata.create_all(engine)
