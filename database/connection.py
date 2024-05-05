# create sqlite database
import sqlite3
from sqlmodel import Field, SQLModel, create_engine
import config.load_config as CONFIG

# create database.db file if not exists

with open("database.db", "a") as f:
    pass


class ApiKeys(SQLModel, table=True):
    api_key_id: str = Field(primary_key=True)
    user_id: str = Field(foreign_key="users.user_id")


class Images(SQLModel, table=True):
    image_id: str = Field(primary_key=True)
    type: str
    file_name: str
    user_id: str = Field(foreign_key="users.user_id")


class Users(SQLModel, table=True):
    user_id: str = Field(primary_key=True)
    username: str
    password: str


sqlite_url = "sqlite:///database.db"
engine = create_engine(sqlite_url, echo=not CONFIG.PRODUCTION)

SQLModel.metadata.create_all(engine)
